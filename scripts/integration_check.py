"""
End-to-end integration check: boots the real backend (SQLite by default,
any DATABASE_URL works) plus a throwaway Redis instance, applies real Alembic
migrations, then exercises the API exactly the way the frontend's Axios
services do (same paths, same payload shapes) to validate the contract.

Run with:  python3 scripts/integration_check.py
Requires: redis-server on PATH, and this project's requirements installed.
"""
import json
import os
import signal
import subprocess
import sys
import time

import requests

BACKEND_ROOT = str(__import__("pathlib").Path(__file__).resolve().parents[1])

BASE = "http://localhost:8000"
API = f"{BASE}/api/v1"
FRONTEND_ORIGIN = "http://localhost:3000"

results = []


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    results.append((name, status, detail))
    print(f"[{status}] {name} {('- ' + detail) if detail and status == 'FAIL' else ''}")


def main():
    # Redis must be started in-process: anything backgrounded in a prior shell
    # call doesn't survive into this one in this sandbox.
    redis_proc = subprocess.Popen(
        ["redis-server", "--port", "6379", "--daemonize", "no"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(1)

    env = os.environ.copy()
    db_path = "./integration.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    env.update({
        "SECRET_KEY": "devsecret",
        "REFRESH_SECRET_KEY": "devrefreshsecret",
        "DATABASE_URL": f"sqlite:///{db_path}",
        "REDIS_URL": "redis://localhost:6379/0",
        "BACKEND_CORS_ORIGINS": f"{FRONTEND_ORIGIN},http://localhost:3100",
        "PYTHONDONTWRITEBYTECODE": "1",
    })

    migrate = subprocess.run(
        ["python3", "-B", "-m", "alembic", "upgrade", "head"],
        cwd=".", env=env, capture_output=True, text=True,
    )
    check("Alembic migrations apply cleanly", migrate.returncode == 0, migrate.stdout[-500:] + migrate.stderr[-500:])

    proc = subprocess.Popen(
        ["python3", "-B", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=".", env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )

    try:
        # Wait for readiness
        for _ in range(30):
            try:
                r = requests.get(f"{BASE}/health", timeout=1)
                if r.status_code == 200:
                    break
            except requests.exceptions.ConnectionError:
                pass
            time.sleep(0.5)
        else:
            proc.terminate()
            out, _ = proc.communicate(timeout=5)
            print(out[-3000:])
            check("Server startup", False, "server never became healthy")
            return

        check("Health check", r.status_code == 200, str(r.status_code))

        # --- CORS preflight ---
        preflight = requests.options(
            f"{API}/auth/login",
            headers={
                "Origin": FRONTEND_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization",
            },
        )
        allow_origin = preflight.headers.get("access-control-allow-origin")
        check("CORS preflight allows frontend origin", allow_origin == FRONTEND_ORIGIN, f"got {allow_origin!r}")

        # --- Register (matches authService.register / RegisterFormValues) ---
        register_payload = {
            "full_name": "Integration Customer",
            "email": "integration.customer@example.com",
            "phone": "+919812345601",
            "password": "StrongPass123",
            "role": "customer",
        }
        r = requests.post(f"{API}/auth/register", json=register_payload)
        check("Register customer", r.status_code == 201, f"{r.status_code} {r.text[:200]}")
        reg_data = r.json().get("data", {})
        access_token = reg_data.get("access_token")
        refresh_token = reg_data.get("refresh_token")
        check("Register returns access+refresh tokens", bool(access_token and refresh_token))
        check(
            "Register response.data.user matches frontend User type",
            {"id", "full_name", "email", "phone", "role", "is_active", "is_phone_verified",
             "is_email_verified", "avatar_url"} <= set(reg_data.get("user", {}).keys()),
            str(reg_data.get("user", {}).keys()),
        )

        # --- Login ---
        r = requests.post(f"{API}/auth/login", json={"phone": register_payload["phone"], "password": register_payload["password"]})
        check("Login with password", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
        access_token = r.json()["data"]["access_token"]
        refresh_token = r.json()["data"]["refresh_token"]

        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # --- GET /users/me (matches userService.me usage) ---
        r = requests.get(f"{API}/users/me", headers=auth_headers)
        check("GET /users/me with bearer token", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

        # --- Unauthorized access without token ---
        r = requests.get(f"{API}/users/me")
        check("GET /users/me without token -> 401", r.status_code in (401, 403), str(r.status_code))

        # --- Refresh token flow ---
        r = requests.post(f"{API}/auth/refresh", json={"refresh_token": refresh_token})
        check("Refresh token", r.status_code == 200, f"{r.status_code} {r.text[:200]}")
        new_access = r.json()["data"]["access_token"]
        check("Refresh issues a usable new access token",
              requests.get(f"{API}/users/me", headers={"Authorization": f"Bearer {new_access}"}).status_code == 200)

        # --- OTP login flow (register via OTP-only path) ---
        otp_phone = "+919812345602"
        r = requests.post(f"{API}/auth/otp/request", json={"phone": otp_phone})
        check("OTP request", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

        # Pull the real OTP straight from Redis (this is what "receiving the SMS" stands in for)
        import redis
        rds = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)
        otp_value = rds.get(f"otp:{otp_phone}")
        check("OTP stored in Redis", otp_value is not None)

        r = requests.post(f"{API}/auth/otp/verify", json={"phone": otp_phone, "otp": otp_value})
        check("OTP verify logs user in", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

        # --- Vendor registration + admin approval + category/product flow ---
        vendor_owner_payload = {
            "full_name": "Vendor Owner", "phone": "+919812345603", "password": "VendorPass123", "role": "vendor",
        }
        r = requests.post(f"{API}/auth/register", json=vendor_owner_payload)
        vendor_owner_token = r.json()["data"]["access_token"]
        check("Register vendor-role user", r.status_code == 201, str(r.status_code))

        r = requests.post(
            f"{API}/vendors/register",
            headers={"Authorization": f"Bearer {vendor_owner_token}"},
            json={
                "shop_name": "Integration Print Shop", "address_line": "1 Test Rd",
                "city": "Chennai", "state": "Tamil Nadu", "pincode": "600001",
                "latitude": 13.08, "longitude": 80.27, "phone": "+919812345603",
            },
        )
        check("Vendor store registration", r.status_code == 201, f"{r.status_code} {r.text[:300]}")
        vendor_id = r.json()["data"]["id"]

        # Seed an admin directly (no public admin-signup endpoint, matches backend design)
        sys.path.insert(0, ".")
        os.environ.update(env)
        from app.core.database import SessionLocal
        from app.core.security import hash_password
        import app.modules.users.models as users_models
        import app.modules.vendors.models  # noqa: F401 - needed for User.vendor_profile relationship resolution
        import app.modules.categories.models  # noqa: F401
        import app.modules.products.models  # noqa: F401
        import app.modules.orders.models  # noqa: F401
        import app.modules.payments.models  # noqa: F401

        User, UserRole = users_models.User, users_models.UserRole

        db = SessionLocal()
        admin_user = User(
            full_name="Integration Admin", phone="+919812345699",
            hashed_password=hash_password("AdminPass123"), role=UserRole.ADMIN, is_active=True,
        )
        db.add(admin_user)
        db.commit()
        db.close()

        r = requests.post(f"{API}/auth/login", json={"phone": "+919812345699", "password": "AdminPass123"})
        check("Admin login", r.status_code == 200, str(r.status_code))
        admin_token = r.json()["data"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        r = requests.post(f"{API}/vendors/{vendor_id}/approve", headers=admin_headers)
        check("Admin approves vendor", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

        r = requests.post(f"{API}/categories/", headers=admin_headers, json={"name": "Mugs", "slug": "mugs-int-test"})
        check("Admin creates category", r.status_code == 201, f"{r.status_code} {r.text[:200]}")
        category_id = r.json()["data"]["id"]

        r = requests.post(
            f"{API}/products/",
            headers={"Authorization": f"Bearer {vendor_owner_token}"},
            json={
                "category_id": category_id, "title": "Integration Mug", "slug": "integration-mug",
                "base_price": 29900, "variants": [{"sku": "MUG-INT-1", "price": 29900, "stock_qty": 10}],
            },
        )
        check("Vendor creates product", r.status_code == 201, f"{r.status_code} {r.text[:300]}")
        product = r.json()["data"]
        variant_id = product["variants"][0]["id"]

        # --- Document print pricing (customer) ---
        r = requests.get(f"{API}/vendors/nearby", params={"lat": 13.08, "lng": 80.27, "radius_km": 20})
        check("Nearby vendors search", r.status_code == 200 and len(r.json()["data"]) >= 1, f"{r.status_code} {r.text[:200]}")

        # --- Search endpoint (matches frontend SearchService) ---
        r = requests.get(f"{API}/search/", params={"q": "mug"})
        check("Search endpoint", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

        # --- Cart -> Checkout -> Orders (customer) ---
        r = requests.post(f"{API}/cart", headers=auth_headers, json={"product_variant_id": variant_id, "quantity": 2})
        check("Add to cart", r.status_code == 201, f"{r.status_code} {r.text[:300]}")

        r = requests.post(
            f"{API}/orders/checkout", headers=auth_headers,
            json={"vendor_id": vendor_id, "delivery_mode": "vendor_delivery"},
        )
        check("Checkout creates order", r.status_code == 201, f"{r.status_code} {r.text[:300]}")
        order = r.json()["data"]
        check("Order total matches unit price * qty", order["total_amount"] == 29900 * 2, str(order.get("total_amount")))

        r = requests.get(f"{API}/orders/me", headers=auth_headers)
        check("List my orders", r.status_code == 200 and len(r.json()["data"]) == 1, f"{r.status_code}")

        # --- 404 / validation error shape ---
        r = requests.get(f"{API}/products/00000000-0000-0000-0000-000000000000")
        check("Unknown product -> 404 with {success:false}", r.status_code == 404 and r.json().get("success") is False, str(r.status_code))

        r = requests.post(f"{API}/auth/login", json={"phone": "not-a-phone"})
        check("Malformed payload -> 422", r.status_code == 422, str(r.status_code))

        # --- Google Sign-In endpoint (can't get a real Firebase token here,
        # but confirm it's wired correctly: garbage token -> clean 401/422,
        # not a 500, and it's unaffected by FIREBASE_PROJECT_ID being unset
        # in this test environment) ---
        r = requests.post(f"{API}/auth/google", json={"id_token": "not-a-real-token"})
        check(
            "POST /auth/google rejects an invalid token cleanly (no 500)",
            r.status_code in (401, 422), f"{r.status_code} {r.text[:200]}",
        )

        # --- RBAC boundary: vendor must NEVER reach admin resources (spec rule) ---
        vendor_headers = {"Authorization": f"Bearer {vendor_owner_token}"}
        r = requests.get(f"{API}/admin/customers", headers=vendor_headers)
        check("Vendor blocked from admin resources (403)", r.status_code == 403, str(r.status_code))

        r = requests.get(f"{API}/admin/customers", headers=auth_headers)  # plain customer token
        check("Customer blocked from admin resources (403)", r.status_code == 403, str(r.status_code))

        # --- Admin: cities ---
        r = requests.post(f"{API}/admin/cities", headers=admin_headers,
                           json={"name": "Chennai", "state": "Tamil Nadu", "slug": "chennai-int-test"})
        check("Admin adds a city", r.status_code == 201, f"{r.status_code} {r.text[:200]}")
        city_id = r.json()["data"]["id"]

        r = requests.get(f"{API}/admin/cities", headers=admin_headers)
        check("Admin lists cities", r.status_code == 200 and len(r.json()["data"]) >= 1, str(r.status_code))

        r = requests.delete(f"{API}/admin/cities/{city_id}", headers=admin_headers)
        check("Admin removes a city", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

        # --- Admin: banners ---
        r = requests.post(f"{API}/admin/banners", headers=admin_headers,
                           json={"title": "Diwali Sale", "image_url": "https://example.com/banner.jpg"})
        check("Admin creates a banner", r.status_code == 201, f"{r.status_code} {r.text[:200]}")
        banner_id = r.json()["data"]["id"]

        r = requests.patch(f"{API}/admin/banners/{banner_id}", headers=admin_headers, json={"is_active": False})
        check("Admin updates a banner", r.status_code == 200 and r.json()["data"]["is_active"] is False, str(r.status_code))

        # --- Admin: vendor manual create/edit/delete ---
        r = requests.post(f"{API}/admin/vendors", headers=admin_headers, json={
            "shop_name": "Admin Added Shop", "owner_email": "adminadded@example.com",
            "owner_full_name": "Manual Owner", "address_line": "9 Test Ave", "city": "Chennai",
            "state": "Tamil Nadu", "pincode": "600002", "latitude": 13.05, "longitude": 80.2,
            "phone": "+919812345610",
        })
        check("Admin manually creates a vendor (auto-approved)", r.status_code == 201, f"{r.status_code} {r.text[:300]}")
        manual_vendor = r.json()["data"]
        check("Manually-created vendor is auto-approved", manual_vendor.get("status") == "approved", str(manual_vendor.get("status")))
        manual_vendor_id = manual_vendor["id"]

        r = requests.patch(f"{API}/admin/vendors/{manual_vendor_id}", headers=admin_headers, json={"shop_name": "Renamed Shop"})
        check("Admin edits a vendor", r.status_code == 200 and r.json()["data"]["shop_name"] == "Renamed Shop", str(r.status_code))

        r = requests.delete(f"{API}/admin/vendors/{manual_vendor_id}", headers=admin_headers)
        check("Admin deletes a vendor", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

        # --- Admin: full order visibility + cancel + refund ---
        r = requests.get(f"{API}/admin/orders", headers=admin_headers)
        check("Admin sees every order platform-wide", r.status_code == 200 and len(r.json()["data"]) >= 1, str(r.status_code))

        r = requests.post(f"{API}/admin/orders/{order['id']}/cancel", headers=admin_headers, json={"reason": "integration test"})
        check("Admin cancels any order", r.status_code == 200 and r.json()["data"]["status"] == "cancelled", f"{r.status_code} {r.text[:200]}")

        r = requests.post(f"{API}/admin/orders/{order['id']}/refund", headers=admin_headers, json={"reason": "test refund"})
        check(
            "Admin refund attempt on an order with no successful payment -> clean error, not 500",
            r.status_code in (404, 400, 422), f"{r.status_code} {r.text[:200]}",
        )

        # --- Admin: configurable pricing engine ---
        r = requests.get(f"{API}/admin/pricing", headers=admin_headers)
        check("Admin views current pricing rates", r.status_code == 200 and "rate_bw_page" in r.json()["data"]["rates"], str(r.status_code))
        original_bw_rate = r.json()["data"]["rates"]["rate_bw_page"]

        r = requests.put(f"{API}/admin/pricing/rate_bw_page", headers=admin_headers, json={"value": 999})
        check("Admin updates a pricing rate without a code change", r.status_code == 200, f"{r.status_code} {r.text[:200]}")

        r = requests.get(f"{API}/admin/pricing", headers=admin_headers)
        new_rate = r.json()["data"]["rates"]["rate_bw_page"]
        check("Updated pricing rate takes effect immediately", new_rate == 999.0, f"expected 999.0, got {new_rate}")

        r = requests.put(f"{API}/admin/pricing/not_a_real_field", headers=admin_headers, json={"value": 1})
        check("Rejects unknown pricing field", r.status_code == 422, str(r.status_code))

        # restore the rate so re-runs of this script are order-independent
        requests.put(f"{API}/admin/pricing/rate_bw_page", headers=admin_headers, json={"value": original_bw_rate})

        # --- Admin: maintenance mode ---
        r = requests.put(f"{API}/admin/maintenance-mode", headers=admin_headers,
                          json={"enabled": True, "message": "Down for scheduled maintenance"})
        check("Admin enables maintenance mode", r.status_code == 200 and r.json()["data"]["enabled"] is True, str(r.status_code))

        r = requests.get(f"{API}/products/{product['id']}")
        check("Non-admin traffic blocked during maintenance (503)", r.status_code == 503, str(r.status_code))

        r = requests.get(f"{API}/admin/customers", headers=admin_headers)
        check("Admin still has access during maintenance", r.status_code == 200, str(r.status_code))

        r = requests.put(f"{API}/admin/maintenance-mode", headers=admin_headers, json={"enabled": False})
        check("Admin disables maintenance mode", r.status_code == 200, str(r.status_code))

        r = requests.get(f"{API}/products/{product['id']}")
        check("Traffic restored after disabling maintenance mode", r.status_code == 200, str(r.status_code))

        # --- Admin: login events + audit log actually recorded real entries ---
        r = requests.get(f"{API}/admin/login-events", headers=admin_headers)
        check(
            "Admin sees recorded login events (password/otp/google)",
            r.status_code == 200 and len(r.json()["data"]) >= 3, f"{r.status_code}, count={len(r.json().get('data', []))}",
        )

        r = requests.get(f"{API}/admin/audit-logs", headers=admin_headers)
        check(
            "Admin actions taken in this run appear in the audit log",
            r.status_code == 200 and len(r.json()["data"]) >= 5, f"{r.status_code}, count={len(r.json().get('data', []))}",
        )

    finally:
        proc.terminate()
        try:
            out, _ = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
        if any(s == "FAIL" for _, s, _ in results):
            print("\n=== SERVER LOG (tail) ===")
            print(out[-6000:])
        redis_proc.terminate()
        try:
            redis_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            redis_proc.kill()

    print("\n=== SUMMARY ===")
    passed = sum(1 for _, s, _ in results if s == "PASS")
    print(f"{passed}/{len(results)} checks passed")
    if passed != len(results):
        print("\nFAILURES:")
        for name, status, detail in results:
            if status == "FAIL":
                print(f" - {name}: {detail}")
        sys.exit(1)


if __name__ == "__main__":
    main()

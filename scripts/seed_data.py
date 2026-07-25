"""
Seeds the database with a demo admin, a customer, an approved vendor with
products, and a couple of categories, so the API is immediately explorable.

Run with:  python -m scripts.seed_data   (after `alembic upgrade head`)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.modules.categories.models import Category
from app.modules.products.models import Product, ProductVariant
from app.modules.users.models import User, UserRole
from app.modules.vendors.models import Vendor, VendorStatus


def run():
    db = SessionLocal()
    try:
        admin = User(
            full_name="Zyro Admin", email="admin@zyroprints.com", phone="+919999999999",
            hashed_password=hash_password("Admin@123"), role=UserRole.ADMIN,
            is_active=True, is_phone_verified=True, is_email_verified=True,
        )
        customer = User(
            full_name="Demo Customer", email="customer@zyroprints.com", phone="+919999999998",
            hashed_password=hash_password("Customer@123"), role=UserRole.CUSTOMER,
            is_active=True, is_phone_verified=True,
        )
        vendor_owner = User(
            full_name="Demo Print Shop Owner", email="vendor@zyroprints.com", phone="+919999999997",
            hashed_password=hash_password("Vendor@123"), role=UserRole.VENDOR,
            is_active=True, is_phone_verified=True,
        )
        db.add_all([admin, customer, vendor_owner])
        db.flush()

        vendor = Vendor(
            owner_id=vendor_owner.id, shop_name="Quick Print Studio", slug="quick-print-studio-demo",
            description="Fast, reliable printing for documents and custom gifts.",
            address_line="12 MG Road", city="Chennai", state="Tamil Nadu", pincode="600001",
            latitude=13.0827, longitude=80.2707, phone="+919999999997",
            status=VendorStatus.APPROVED, is_verified=True,
        )
        db.add(vendor)
        db.flush()

        cat_mugs = Category(name="Printed Mugs", slug="printed-mugs")
        cat_tshirts = Category(name="Custom T-Shirts", slug="custom-t-shirts")
        cat_wedding = Category(name="Wedding Invitations", slug="wedding-invitations")
        db.add_all([cat_mugs, cat_tshirts, cat_wedding])
        db.flush()

        cat_royal = Category(name="Royal Wedding", slug="royal-wedding", parent_id=cat_wedding.id)
        db.add(cat_royal)
        db.flush()

        mug = Product(
            vendor_id=vendor.id, category_id=cat_mugs.id, title="Personalized Photo Mug",
            slug="personalized-photo-mug-demo", description="Upload any photo and print it on a ceramic mug.",
            images=[], base_price=29900, delivery_time_days=2,
        )
        db.add(mug)
        db.flush()
        db.add(ProductVariant(product_id=mug.id, sku="MUG-WHITE-STD", attributes={"color": "white"}, price=29900, stock_qty=100))

        db.commit()
        print("Seed data created successfully.")
        print("Admin login:    +919999999999 / Admin@123")
        print("Customer login: +919999999998 / Customer@123")
        print("Vendor login:   +919999999997 / Vendor@123")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run()

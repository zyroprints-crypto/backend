import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.modules.cart.repository import CartRepository
from app.modules.documents.repository import PrintDocumentRepository
from app.modules.orders.models import Coupon, Order, OrderItem, OrderStatus, OrderStatusEvent
from app.modules.orders.repository import OrderItemRepository, OrderRepository, OrderStatusEventRepository
from app.modules.orders.schemas import CheckoutRequest, OrderStatusUpdate
from app.modules.products.repository import ProductVariantRepository
from app.modules.vendors.repository import VendorRepository

# Status transitions a VENDOR is allowed to make.
VENDOR_ALLOWED_TRANSITIONS = {
    OrderStatus.PLACED: {OrderStatus.ACCEPTED, OrderStatus.REJECTED},
    OrderStatus.ACCEPTED: {OrderStatus.PRINTING, OrderStatus.PAUSED, OrderStatus.CANCELLED},
    OrderStatus.PAUSED: {OrderStatus.PRINTING, OrderStatus.CANCELLED},
    OrderStatus.PRINTING: {OrderStatus.READY},
    OrderStatus.READY: {OrderStatus.OUT_FOR_DELIVERY, OrderStatus.DELIVERED},
    OrderStatus.OUT_FOR_DELIVERY: {OrderStatus.DELIVERED},
}


def _order_number() -> str:
    return f"ZP{datetime.now(timezone.utc):%Y%m%d}{uuid.uuid4().hex[:6].upper()}"


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.orders = OrderRepository(db)
        self.items = OrderItemRepository(db)
        self.events = OrderStatusEventRepository(db)
        self.cart = CartRepository(db)
        self.variants = ProductVariantRepository(db)
        self.documents = PrintDocumentRepository(db)
        self.vendors = VendorRepository(db)

    def checkout(self, customer_id: UUID, payload: CheckoutRequest) -> Order:
        cart_items = self.cart.list(limit=200, customer_id=customer_id)
        if payload.cart_item_ids:
            cart_items = [c for c in cart_items if c.id in payload.cart_item_ids]
        if not cart_items:
            raise ValidationAppError("Cart is empty")

        vendor = self.vendors.get(payload.vendor_id)
        if not vendor:
            raise NotFoundError("Vendor not found")

        order = Order(
            order_number=_order_number(),
            customer_id=customer_id,
            vendor_id=vendor.id,
            delivery_address_id=payload.delivery_address_id,
            delivery_mode=payload.delivery_mode,
            status=OrderStatus.PLACED,
        )
        order = self.orders.create(order)

        subtotal = 0
        for cart_item in cart_items:
            if cart_item.product_variant_id:
                variant = self.variants.get(cart_item.product_variant_id)
                if not variant or variant.stock_qty < cart_item.quantity:
                    raise ValidationAppError("One or more items are out of stock")
                unit_price = variant.price
                self.variants.update(variant, stock_qty=variant.stock_qty - cart_item.quantity)
            else:
                doc = self.documents.get(cart_item.print_document_id)
                if not doc:
                    raise NotFoundError("Print document not found")
                unit_price = doc.calculated_price

            line_total = unit_price * cart_item.quantity
            subtotal += line_total
            self.items.create(OrderItem(
                order_id=order.id,
                product_variant_id=cart_item.product_variant_id,
                print_document_id=cart_item.print_document_id,
                quantity=cart_item.quantity,
                unit_price=unit_price,
                line_total=line_total,
            ))
            self.cart.soft_delete(cart_item)

        discount = self._apply_coupon(payload.coupon_code, vendor.id, subtotal) if payload.coupon_code else 0
        commission = round((subtotal - discount) * vendor.commission_percent / 100)
        total = subtotal - discount

        order = self.orders.update(
            order,
            subtotal=subtotal,
            discount_amount=discount,
            platform_commission=commission,
            total_amount=total,
            coupon_code=payload.coupon_code,
        )
        self._record_event(order.id, OrderStatus.PLACED, "Order placed")
        return self.orders.get_with_items(order.id)

    def _apply_coupon(self, code: str, vendor_id: UUID, subtotal: int) -> int:
        from sqlalchemy import select
        stmt = select(Coupon).where(Coupon.code == code, Coupon.is_active.is_(True), Coupon.is_deleted.is_(False))
        coupon = self.db.execute(stmt).scalar_one_or_none()
        if not coupon:
            raise ValidationAppError("Invalid coupon code")
        if coupon.vendor_id and coupon.vendor_id != vendor_id:
            raise ValidationAppError("Coupon not valid for this store")
        if coupon.expires_at and coupon.expires_at < datetime.now(timezone.utc):
            raise ValidationAppError("Coupon has expired")
        if coupon.max_uses and coupon.used_count >= coupon.max_uses:
            raise ValidationAppError("Coupon usage limit reached")
        if subtotal < coupon.min_order_amount:
            raise ValidationAppError(f"Minimum order amount not met for this coupon")

        discount = round(subtotal * coupon.discount_percent / 100)
        if coupon.max_discount_amount:
            discount = min(discount, coupon.max_discount_amount)
        coupon.used_count += 1
        self.db.flush()
        return discount

    def get_order(self, order_id: UUID) -> Order:
        order = self.orders.get_with_items(order_id)
        if not order:
            raise NotFoundError("Order not found")
        return order

    def list_for_customer(self, customer_id: UUID) -> list[Order]:
        return self.orders.list_for_customer(customer_id, limit=100)

    def list_for_vendor(self, vendor_owner_id: UUID) -> list[Order]:
        vendor = self.vendors.get_by_owner(vendor_owner_id)
        if not vendor:
            raise NotFoundError("Vendor store not found")
        return self.orders.list_for_vendor(vendor.id, limit=100)

    def update_status(self, vendor_owner_id: UUID, order_id: UUID, payload: OrderStatusUpdate) -> Order:
        vendor = self.vendors.get_by_owner(vendor_owner_id)
        order = self.get_order(order_id)
        if not vendor or order.vendor_id != vendor.id:
            raise ForbiddenError("You do not manage this order")

        allowed = VENDOR_ALLOWED_TRANSITIONS.get(order.status, set())
        if payload.status not in allowed:
            raise ValidationAppError(f"Cannot move order from {order.status.value} to {payload.status.value}")

        updated = self.orders.update(order, status=payload.status)
        self._record_event(order.id, payload.status, payload.note)
        return self.orders.get_with_items(updated.id)

    def cancel_order(self, customer_id: UUID, order_id: UUID) -> Order:
        order = self.get_order(order_id)
        if order.customer_id != customer_id:
            raise ForbiddenError("Not your order")
        if order.status not in (OrderStatus.PLACED, OrderStatus.ACCEPTED):
            raise ValidationAppError("Order can no longer be cancelled")
        updated = self.orders.update(order, status=OrderStatus.CANCELLED)
        self._record_event(order.id, OrderStatus.CANCELLED, "Cancelled by customer")
        return updated

    def _record_event(self, order_id: UUID, status: OrderStatus, note: str | None) -> None:
        self.events.create(OrderStatusEvent(order_id=order_id, status=status, note=note))

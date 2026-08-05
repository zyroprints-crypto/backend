from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.cart.models import CartItem, FavoriteShop, WishlistItem
from app.modules.cart.repository import CartRepository, FavoriteShopRepository, WishlistRepository
from app.modules.cart.schemas import CartItemCreate, CartItemOut, FavoriteShopCreate, WishlistCreate
from app.modules.documents.repository import PrintDocumentRepository
from app.modules.products.repository import ProductRepository, ProductVariantRepository


class CartService:
    def __init__(self, db: Session):
        self.db = db
        self.cart = CartRepository(db)
        self.wishlist = WishlistRepository(db)
        self.favorites = FavoriteShopRepository(db)
        self.variants = ProductVariantRepository(db)
        self.products = ProductRepository(db)
        self.documents = PrintDocumentRepository(db)

    def _enrich(self, item: CartItem) -> CartItemOut:
        """Attach display fields (title/image/price) by resolving the linked
        product variant or print document. Missing/deleted references degrade
        to nulls rather than erroring, so a stale cart item is still listable."""
        title = image_url = None
        unit_price = None

        if item.product_variant_id:
            variant = self.variants.get(item.product_variant_id)
            if variant:
                unit_price = variant.price
                image_url = variant.image_url
                product = self.products.get(variant.product_id)
                if product:
                    title = f"{product.title} — {variant.sku}" if variant.attributes else product.title
                    image_url = image_url or (product.images[0] if product.images else None)
        elif item.print_document_id:
            doc = self.documents.get(item.print_document_id)
            if doc:
                unit_price = doc.calculated_price
                title = f"Print job — {doc.file_name}"

        return CartItemOut(
            id=item.id, product_variant_id=item.product_variant_id, print_document_id=item.print_document_id,
            quantity=item.quantity, title=title, image_url=image_url, unit_price=unit_price,
        )

    def add_to_cart(self, customer_id: UUID, payload: CartItemCreate) -> CartItemOut:
        item = CartItem(customer_id=customer_id, **payload.model_dump())
        item = self.cart.create(item)
        return self._enrich(item)

    def list_cart(self, customer_id: UUID) -> list[CartItemOut]:
        items = self.cart.list(limit=200, customer_id=customer_id)
        return [self._enrich(item) for item in items]

    def remove_from_cart(self, customer_id: UUID, item_id: UUID) -> None:
        item = self.cart.get(item_id)
        if not item or item.customer_id != customer_id:
            raise NotFoundError("Cart item not found")
        self.cart.soft_delete(item)

    def clear_cart(self, customer_id: UUID) -> None:
        for item in self.list_cart(customer_id):
            self.cart.soft_delete(item)

    def add_wishlist(self, customer_id: UUID, payload: WishlistCreate) -> WishlistItem:
        return self.wishlist.create(WishlistItem(customer_id=customer_id, **payload.model_dump()))

    def list_wishlist(self, customer_id: UUID) -> list[WishlistItem]:
        return self.wishlist.list(limit=200, customer_id=customer_id)

    def remove_wishlist(self, customer_id: UUID, item_id: UUID) -> None:
        item = self.wishlist.get(item_id)
        if not item or item.customer_id != customer_id:
            raise NotFoundError("Wishlist item not found")
        self.wishlist.soft_delete(item)

    def add_favorite_shop(self, customer_id: UUID, payload: FavoriteShopCreate) -> FavoriteShop:
        return self.favorites.create(FavoriteShop(customer_id=customer_id, **payload.model_dump()))

    def list_favorite_shops(self, customer_id: UUID) -> list[FavoriteShop]:
        return self.favorites.list(limit=200, customer_id=customer_id)

from sqlalchemy.orm import Session

from app.common.base_repository import BaseRepository
from app.modules.cart.models import CartItem, FavoriteShop, WishlistItem


class CartRepository(BaseRepository[CartItem]):
    def __init__(self, db: Session):
        super().__init__(db, CartItem)


class WishlistRepository(BaseRepository[WishlistItem]):
    def __init__(self, db: Session):
        super().__init__(db, WishlistItem)


class FavoriteShopRepository(BaseRepository[FavoriteShop]):
    def __init__(self, db: Session):
        super().__init__(db, FavoriteShop)

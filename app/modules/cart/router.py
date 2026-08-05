from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.common.dependencies import get_current_user
from app.common.responses import SuccessResponse
from app.core.database import get_db
from app.modules.cart.schemas import (
    CartItemCreate, CartItemOut, FavoriteShopCreate, FavoriteShopOut, WishlistCreate, WishlistOut,
)
from app.modules.cart.service import CartService
from app.modules.users.models import User

router = APIRouter(tags=["Cart & Wishlist"])


@router.post("/cart", response_model=SuccessResponse[CartItemOut], status_code=status.HTTP_201_CREATED)
def add_to_cart(payload: CartItemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = CartService(db).add_to_cart(current_user.id, payload)
    return SuccessResponse(message="Added to cart", data=item)


@router.get("/cart", response_model=SuccessResponse[list[CartItemOut]])
def list_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = CartService(db).list_cart(current_user.id)
    return SuccessResponse(data=items)


@router.delete("/cart/{item_id}", response_model=SuccessResponse)
def remove_from_cart(item_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    CartService(db).remove_from_cart(current_user.id, item_id)
    return SuccessResponse(message="Removed from cart")


@router.delete("/cart", response_model=SuccessResponse)
def clear_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    CartService(db).clear_cart(current_user.id)
    return SuccessResponse(message="Cart cleared")


@router.post("/wishlist", response_model=SuccessResponse[WishlistOut], status_code=status.HTTP_201_CREATED)
def add_wishlist(payload: WishlistCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = CartService(db).add_wishlist(current_user.id, payload)
    return SuccessResponse(message="Added to wishlist", data=WishlistOut.model_validate(item))


@router.get("/wishlist", response_model=SuccessResponse[list[WishlistOut]])
def list_wishlist(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = CartService(db).list_wishlist(current_user.id)
    return SuccessResponse(data=[WishlistOut.model_validate(i) for i in items])


@router.delete("/wishlist/{item_id}", response_model=SuccessResponse)
def remove_wishlist(item_id: UUID, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    CartService(db).remove_wishlist(current_user.id, item_id)
    return SuccessResponse(message="Removed from wishlist")


@router.post("/favorite-shops", response_model=SuccessResponse[FavoriteShopOut], status_code=status.HTTP_201_CREATED)
def add_favorite_shop(
    payload: FavoriteShopCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    item = CartService(db).add_favorite_shop(current_user.id, payload)
    return SuccessResponse(message="Shop favorited", data=FavoriteShopOut.model_validate(item))


@router.get("/favorite-shops", response_model=SuccessResponse[list[FavoriteShopOut]])
def list_favorite_shops(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = CartService(db).list_favorite_shops(current_user.id)
    return SuccessResponse(data=[FavoriteShopOut.model_validate(i) for i in items])

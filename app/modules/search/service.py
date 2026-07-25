"""
Unified search across shops and products. Uses simple ILIKE matching against
PostgreSQL, filterable by category/location/price/rating. For production scale,
swap the query layer for Elasticsearch/OpenSearch/Meilisearch behind the same
`SearchService.search` interface.
"""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.modules.products.models import Product
from app.modules.search.schemas import SearchResponse, SearchResultItem
from app.modules.vendors.models import Vendor, VendorStatus


class SearchService:
    def __init__(self, db: Session):
        self.db = db

    def search(
        self, query: str, category_id=None, min_price=None, max_price=None, min_rating=None, city=None
    ) -> SearchResponse:
        results: list[SearchResultItem] = []

        vendor_stmt = select(Vendor).where(
            Vendor.is_deleted.is_(False), Vendor.status == VendorStatus.APPROVED,
            Vendor.shop_name.ilike(f"%{query}%"),
        )
        if city:
            vendor_stmt = vendor_stmt.where(Vendor.city.ilike(f"%{city}%"))
        if min_rating:
            vendor_stmt = vendor_stmt.where(Vendor.rating_avg >= min_rating)
        for v in self.db.execute(vendor_stmt.limit(20)).scalars():
            results.append(SearchResultItem(
                type="vendor", id=v.id, title=v.shop_name, subtitle=v.city, rating=v.rating_avg, image_url=v.logo_url
            ))

        product_stmt = select(Product).where(
            Product.is_deleted.is_(False), Product.is_active.is_(True),
            or_(Product.title.ilike(f"%{query}%"), Product.description.ilike(f"%{query}%")),
        )
        if category_id:
            product_stmt = product_stmt.where(Product.category_id == category_id)
        if min_price is not None:
            product_stmt = product_stmt.where(Product.base_price >= min_price)
        if max_price is not None:
            product_stmt = product_stmt.where(Product.base_price <= max_price)
        if min_rating:
            product_stmt = product_stmt.where(Product.rating_avg >= min_rating)
        for p in self.db.execute(product_stmt.limit(20)).scalars():
            results.append(SearchResultItem(
                type="product", id=p.id, title=p.title, price=p.base_price, rating=p.rating_avg,
                image_url=(p.images[0] if p.images else None),
            ))

        return SearchResponse(query=query, results=results)

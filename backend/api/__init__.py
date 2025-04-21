from .products import router as products_router
from .categories import router as categories_router
from .orders import router as orders_router
from .reviews import router as reviews_router
from .users import router as users_router
from .wishlists import router as wishlists_router

__all__ = [
    "products_router",
    "categories_router",
    "orders_router",
    "reviews_router",
    "users_router",
    "wishlists_router"
]

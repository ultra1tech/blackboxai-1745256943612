from pydantic import BaseModel, EmailStr, constr, validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum

# Enums
class UserType(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"

class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

# Base Schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    user_type: Optional[UserType] = UserType.BUYER
    country: Optional[str] = None
    language: Optional[str] = "en"
    profile_image: Optional[str] = None

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[int] = None

class ProductBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: float
    currency: Optional[str] = "USD"
    stock_quantity: int
    category_id: int
    image_urls: Optional[str] = None  # JSON string of URLs
    shipping_info: Optional[str] = None  # JSON string
    is_active: Optional[bool] = True

class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    price: float
    currency: Optional[str] = "USD"

class OrderBase(BaseModel):
    total_amount: float
    currency: Optional[str] = "USD"
    status: Optional[OrderStatus] = OrderStatus.PENDING
    shipping_address: str
    payment_method: Optional[str] = None

class ReviewBase(BaseModel):
    product_id: int
    rating: constr(min_length=1, max_length=5)
    comment: Optional[str] = None

class WishlistBase(BaseModel):
    product_id: int

# Create Schemas
class UserCreate(UserBase):
    password: str

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserProfileUpdate(UserBase):
    password: Optional[str] = None

    @validator('password')
    def password_strength(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class CategoryCreate(CategoryBase):
    pass

class ProductCreate(ProductBase):
    pass

class OrderItemCreate(OrderItemBase):
    pass

class OrderCreate(OrderBase):
    items: List[OrderItemCreate]

class ReviewCreate(ReviewBase):
    pass

class WishlistCreate(WishlistBase):
    pass

# Response Schemas
class Category(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Review(ReviewBase):
    id: int
    reviewer_id: int
    seller_id: int
    created_at: datetime

    class Config:
        orm_mode = True

class Product(ProductBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    reviews: Optional[List[Review]] = []
    category: Optional[Category] = None

    class Config:
        orm_mode = True

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    product: Product

    class Config:
        orm_mode = True

class Order(OrderBase):
    id: int
    buyer_id: int
    seller_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    tracking_number: Optional[str]
    payment_status: str
    items: List[OrderItem]

    class Config:
        orm_mode = True

class Wishlist(WishlistBase):
    id: int
    user_id: int
    created_at: datetime
    product: Product

    class Config:
        orm_mode = True

class User(UserBase):
    id: int
    is_verified: bool
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]
    products: Optional[List[Product]] = []
    orders_as_buyer: Optional[List[Order]] = []
    orders_as_seller: Optional[List[Order]] = []
    reviews_given: Optional[List[Review]] = []
    reviews_received: Optional[List[Review]] = []

    class Config:
        orm_mode = True

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: User

class TokenData(BaseModel):
    email: Optional[str] = None
    user_type: Optional[UserType] = None

# Additional Schemas
class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    tracking_number: Optional[str] = None

class SellerStats(BaseModel):
    total_orders: int
    pending_orders: int
    completed_orders: int
    total_revenue: float

class UserStats(BaseModel):
    total_orders: int
    total_spent: Optional[float] = None
    total_revenue: Optional[float] = None
    total_products: Optional[int] = None
    average_rating: Optional[float] = None
    total_reviews: Optional[int] = None

class SellerProfile(BaseModel):
    seller: User
    total_products: int
    total_sales: int
    average_rating: float

class WishlistCheck(BaseModel):
    in_wishlist: bool

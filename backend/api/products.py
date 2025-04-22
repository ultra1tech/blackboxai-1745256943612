from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db
from api.deps import get_current_user
from sqlalchemy import or_

router = APIRouter()

@router.post("/", response_model=schemas.Product)
async def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    if current_user.user_type != models.UserType.SELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can create products"
        )
    
    db_product = models.Product(
        **product.dict(),
        owner_id=current_user.id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/", response_model=List[schemas.Product])
async def read_products(
    skip: int = 0,
    limit: int = 20,
    category_id: Optional[int] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    sort_by: Optional[str] = Query(None, enum=["price_asc", "price_desc", "newest", "rating"]),
    db: Session = Depends(get_db)
):
    query = db.query(models.Product).filter(models.Product.is_active == True)
    
    # Apply filters
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    
    if search:
        search_filter = or_(
            models.Product.title.ilike(f"%{search}%"),
            models.Product.description.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    if min_price is not None:
        query = query.filter(models.Product.price >= min_price)
    
    if max_price is not None:
        query = query.filter(models.Product.price <= max_price)
    
    # Apply sorting
    if sort_by:
        if sort_by == "price_asc":
            query = query.order_by(models.Product.price.asc())
        elif sort_by == "price_desc":
            query = query.order_by(models.Product.price.desc())
        elif sort_by == "newest":
            query = query.order_by(models.Product.created_at.desc())
        elif sort_by == "rating":
            # Assuming we have a rating calculation
            query = query.order_by(models.Product.rating.desc())
    
    return query.offset(skip).limit(limit).all()

@router.get("/{product_id}", response_model=schemas.Product)
async def read_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.is_active == True
    ).first()
    
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product

@router.put("/{product_id}", response_model=schemas.Product)
async def update_product(
    product_id: int,
    product_update: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.is_active == True
    ).first()
    
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if db_product.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this product"
        )
    
    for key, value in product_update.dict().items():
        setattr(db_product, key, value)
    
    db_product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    db_product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.is_active == True
    ).first()
    
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    if db_product.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this product"
        )
    
    # Soft delete
    db_product.is_active = False
    db_product.updated_at = datetime.utcnow()
    db.commit()

@router.get("/{product_id}/reviews", response_model=List[schemas.Review])
async def read_product_reviews(
    product_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.is_active == True
    ).first()
    
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    reviews = db.query(models.Review).filter(
        models.Review.product_id == product_id
    ).offset(skip).limit(limit).all()
    
    return reviews

@router.get("/seller/{seller_id}", response_model=List[schemas.Product])
async def read_seller_products(
    seller_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    products = db.query(models.Product).filter(
        models.Product.owner_id == seller_id,
        models.Product.is_active == True
    ).offset(skip).limit(limit).all()
    
    return products

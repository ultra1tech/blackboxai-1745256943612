from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db
from api.deps import get_current_active_user, verify_marketplace_access
from datetime import datetime
from sqlalchemy import func

router = APIRouter()

@router.post("/product/{product_id}", response_model=schemas.Review)
async def create_product_review(
    product_id: int,
    review: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_marketplace_access)
):
    """Create a new product review"""
    # Check if product exists and is active
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if user has purchased the product
    order = db.query(models.Order).join(models.OrderItem).filter(
        models.Order.buyer_id == current_user.id,
        models.Order.status == models.OrderStatus.DELIVERED,
        models.OrderItem.product_id == product_id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only review purchased and delivered products"
        )
    
    # Check if user has already reviewed this product
    existing_review = db.query(models.Review).filter(
        models.Review.product_id == product_id,
        models.Review.reviewer_id == current_user.id
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already reviewed this product"
        )
    
    # Create review
    db_review = models.Review(
        product_id=product_id,
        reviewer_id=current_user.id,
        seller_id=product.owner_id,
        rating=review.rating,
        comment=review.comment
    )
    
    db.add(db_review)
    db.commit()
    db.refresh(db_review)
    
    # Update product rating
    avg_rating = db.query(func.avg(models.Review.rating)).filter(
        models.Review.product_id == product_id
    ).scalar()
    
    product.rating = float(avg_rating)
    db.commit()
    
    return db_review

@router.get("/product/{product_id}", response_model=List[schemas.Review])
async def read_product_reviews(
    product_id: int,
    skip: int = 0,
    limit: int = 20,
    rating: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all reviews for a specific product"""
    # Verify product exists
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Query reviews
    query = db.query(models.Review).filter(models.Review.product_id == product_id)
    
    if rating:
        query = query.filter(models.Review.rating == rating)
    
    reviews = query.order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()
    return reviews

@router.get("/seller/{seller_id}", response_model=List[schemas.Review])
async def read_seller_reviews(
    seller_id: int,
    skip: int = 0,
    limit: int = 20,
    rating: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all reviews for a specific seller"""
    # Verify seller exists
    seller = db.query(models.User).filter(
        models.User.id == seller_id,
        models.User.user_type == models.UserType.SELLER,
        models.User.is_active == True
    ).first()
    
    if not seller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found"
        )
    
    # Query reviews
    query = db.query(models.Review).filter(models.Review.seller_id == seller_id)
    
    if rating:
        query = query.filter(models.Review.rating == rating)
    
    reviews = query.order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()
    return reviews

@router.put("/{review_id}", response_model=schemas.Review)
async def update_review(
    review_id: int,
    review_update: schemas.ReviewCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update a review"""
    db_review = db.query(models.Review).filter(
        models.Review.id == review_id,
        models.Review.reviewer_id == current_user.id
    ).first()
    
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or not authorized to update"
        )
    
    # Update review
    db_review.rating = review_update.rating
    db_review.comment = review_update.comment
    db.commit()
    db.refresh(db_review)
    
    # Update product rating
    avg_rating = db.query(func.avg(models.Review.rating)).filter(
        models.Review.product_id == db_review.product_id
    ).scalar()
    
    product = db.query(models.Product).filter(models.Product.id == db_review.product_id).first()
    product.rating = float(avg_rating)
    db.commit()
    
    return db_review

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Delete a review"""
    db_review = db.query(models.Review).filter(
        models.Review.id == review_id,
        models.Review.reviewer_id == current_user.id
    ).first()
    
    if not db_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or not authorized to delete"
        )
    
    db.delete(db_review)
    db.commit()
    
    # Update product rating
    avg_rating = db.query(func.avg(models.Review.rating)).filter(
        models.Review.product_id == db_review.product_id
    ).scalar()
    
    product = db.query(models.Product).filter(models.Product.id == db_review.product_id).first()
    product.rating = float(avg_rating) if avg_rating else 0
    db.commit()

@router.get("/user/reviews", response_model=List[schemas.Review])
async def read_user_reviews(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get all reviews written by the current user"""
    reviews = db.query(models.Review).filter(
        models.Review.reviewer_id == current_user.id
    ).order_by(models.Review.created_at.desc()).offset(skip).limit(limit).all()
    
    return reviews

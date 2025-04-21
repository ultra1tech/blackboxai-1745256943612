from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from .deps import get_current_active_user, get_current_admin
from datetime import datetime
from sqlalchemy import func
import os
from passlib.context import CryptContext

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/profile", response_model=schemas.User)
async def read_user_profile(
    current_user: models.User = Depends(get_current_active_user)
):
    """Get current user's profile"""
    return current_user

@router.put("/profile", response_model=schemas.User)
async def update_user_profile(
    profile_update: schemas.UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update current user's profile"""
    # Update allowed fields
    for field, value in profile_update.dict(exclude_unset=True).items():
        if field != "password":  # Handle password separately
            setattr(current_user, field, value)
    
    # Update password if provided
    if profile_update.password:
        current_user.hashed_password = pwd_context.hash(profile_update.password)
    
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/profile/image", response_model=schemas.User)
async def update_profile_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update user's profile image"""
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Create uploads directory if it doesn't exist
    os.makedirs("uploads/profile_images", exist_ok=True)
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    filename = f"user_{current_user.id}_{datetime.utcnow().timestamp()}.{file_extension}"
    file_path = f"uploads/profile_images/{filename}"
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Update user profile
    current_user.profile_image = file_path
    db.commit()
    db.refresh(current_user)
    
    return current_user

@router.get("/sellers", response_model=List[schemas.User])
async def list_sellers(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
    country: Optional[str] = None,
    min_rating: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """List all sellers with optional filters"""
    query = db.query(models.User).filter(
        models.User.user_type == models.UserType.SELLER,
        models.User.is_active == True
    )
    
    if search:
        query = query.filter(models.User.full_name.ilike(f"%{search}%"))
    
    if country:
        query = query.filter(models.User.country == country)
    
    if min_rating:
        # Subquery to get average seller rating
        seller_ratings = db.query(
            models.Review.seller_id,
            func.avg(models.Review.rating).label('avg_rating')
        ).group_by(models.Review.seller_id).subquery()
        
        query = query.join(
            seller_ratings,
            models.User.id == seller_ratings.c.seller_id,
            isouter=True
        ).filter(seller_ratings.c.avg_rating >= min_rating)
    
    sellers = query.order_by(models.User.created_at.desc()).offset(skip).limit(limit).all()
    return sellers

@router.get("/seller/{seller_id}", response_model=schemas.SellerProfile)
async def get_seller_profile(
    seller_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed seller profile"""
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
    
    # Get seller statistics
    total_products = db.query(models.Product).filter(
        models.Product.owner_id == seller_id,
        models.Product.is_active == True
    ).count()
    
    total_sales = db.query(models.Order).filter(
        models.Order.seller_id == seller_id,
        models.Order.status == models.OrderStatus.DELIVERED
    ).count()
    
    avg_rating = db.query(func.avg(models.Review.rating)).filter(
        models.Review.seller_id == seller_id
    ).scalar() or 0
    
    return {
        "seller": seller,
        "total_products": total_products,
        "total_sales": total_sales,
        "average_rating": float(avg_rating)
    }

@router.post("/verify-seller/{user_id}", response_model=schemas.User)
async def verify_seller(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Verify a seller (admin only)"""
    user = db.query(models.User).filter(
        models.User.id == user_id,
        models.User.user_type == models.UserType.SELLER
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Seller not found"
        )
    
    user.is_verified = True
    db.commit()
    db.refresh(user)
    return user

@router.post("/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_account(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Deactivate current user's account"""
    current_user.is_active = False
    db.commit()

@router.get("/dashboard/stats", response_model=schemas.UserStats)
async def get_user_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get user's dashboard statistics"""
    if current_user.user_type == models.UserType.SELLER:
        # Seller stats
        total_products = db.query(models.Product).filter(
            models.Product.owner_id == current_user.id,
            models.Product.is_active == True
        ).count()
        
        total_orders = db.query(models.Order).filter(
            models.Order.seller_id == current_user.id
        ).count()
        
        total_revenue = db.query(func.sum(models.Order.total_amount)).filter(
            models.Order.seller_id == current_user.id,
            models.Order.status == models.OrderStatus.DELIVERED
        ).scalar() or 0
        
        avg_rating = db.query(func.avg(models.Review.rating)).filter(
            models.Review.seller_id == current_user.id
        ).scalar() or 0
        
        return {
            "total_products": total_products,
            "total_orders": total_orders,
            "total_revenue": float(total_revenue),
            "average_rating": float(avg_rating)
        }
    else:
        # Buyer stats
        total_orders = db.query(models.Order).filter(
            models.Order.buyer_id == current_user.id
        ).count()
        
        total_spent = db.query(func.sum(models.Order.total_amount)).filter(
            models.Order.buyer_id == current_user.id,
            models.Order.status == models.OrderStatus.DELIVERED
        ).scalar() or 0
        
        total_reviews = db.query(models.Review).filter(
            models.Review.reviewer_id == current_user.id
        ).count()
        
        return {
            "total_orders": total_orders,
            "total_spent": float(total_spent),
            "total_reviews": total_reviews
        }

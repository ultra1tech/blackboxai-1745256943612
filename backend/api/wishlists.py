from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from .deps import get_current_active_user
from datetime import datetime

router = APIRouter()

@router.post("/{product_id}", response_model=schemas.Wishlist)
async def add_to_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Add a product to user's wishlist"""
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
    
    # Check if product is already in wishlist
    existing_wishlist = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user.id,
        models.Wishlist.product_id == product_id
    ).first()
    
    if existing_wishlist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already in wishlist"
        )
    
    # Add to wishlist
    wishlist_item = models.Wishlist(
        user_id=current_user.id,
        product_id=product_id
    )
    
    db.add(wishlist_item)
    db.commit()
    db.refresh(wishlist_item)
    
    return wishlist_item

@router.get("/", response_model=List[schemas.Wishlist])
async def read_wishlist(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get user's wishlist items"""
    wishlist_items = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user.id
    ).order_by(
        models.Wishlist.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return wishlist_items

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_wishlist(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Remove a product from user's wishlist"""
    wishlist_item = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user.id,
        models.Wishlist.product_id == product_id
    ).first()
    
    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in wishlist"
        )
    
    db.delete(wishlist_item)
    db.commit()

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_wishlist(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Clear user's entire wishlist"""
    db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user.id
    ).delete()
    
    db.commit()

@router.get("/check/{product_id}", response_model=schemas.WishlistCheck)
async def check_wishlist_status(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Check if a product is in user's wishlist"""
    exists = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user.id,
        models.Wishlist.product_id == product_id
    ).first() is not None
    
    return {"in_wishlist": exists}

@router.post("/move-to-cart/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def move_to_cart(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Move a product from wishlist to cart and remove from wishlist"""
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
    
    # Check if product is in wishlist
    wishlist_item = db.query(models.Wishlist).filter(
        models.Wishlist.user_id == current_user.id,
        models.Wishlist.product_id == product_id
    ).first()
    
    if not wishlist_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in wishlist"
        )
    
    # Create cart item (assuming we have a Cart model)
    # This is a placeholder - implement according to your cart functionality
    # cart_item = models.CartItem(
    #     user_id=current_user.id,
    #     product_id=product_id,
    #     quantity=1
    # )
    # db.add(cart_item)
    
    # Remove from wishlist
    db.delete(wishlist_item)
    db.commit()

@router.get("/products/available", response_model=List[schemas.Wishlist])
async def get_available_wishlist_items(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get wishlist items that are currently available for purchase"""
    available_items = db.query(models.Wishlist).join(
        models.Product,
        models.Wishlist.product_id == models.Product.id
    ).filter(
        models.Wishlist.user_id == current_user.id,
        models.Product.is_active == True,
        models.Product.stock_quantity > 0
    ).order_by(
        models.Wishlist.created_at.desc()
    ).all()
    
    return available_items

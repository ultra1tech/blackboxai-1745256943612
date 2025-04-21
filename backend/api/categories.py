from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from .deps import get_current_admin, get_current_user
from datetime import datetime

router = APIRouter()

@router.post("/", response_model=schemas.Category)
async def create_category(
    category: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Create a new category (admin only)"""
    db_category = models.Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/", response_model=List[schemas.Category])
async def read_categories(
    skip: int = 0,
    limit: int = 100,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all categories or subcategories of a specific parent"""
    query = db.query(models.Category)
    if parent_id is not None:
        query = query.filter(models.Category.parent_id == parent_id)
    else:
        query = query.filter(models.Category.parent_id == None)
    
    categories = query.offset(skip).limit(limit).all()
    return categories

@router.get("/{category_id}", response_model=schemas.Category)
async def read_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific category by ID"""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    return category

@router.put("/{category_id}", response_model=schemas.Category)
async def update_category(
    category_id: int,
    category_update: schemas.CategoryCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Update a category (admin only)"""
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if trying to set as subcategory of itself
    if category_update.parent_id == category_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category cannot be its own parent"
        )
    
    for key, value in category_update.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    """Delete a category (admin only)"""
    # Check if category has subcategories
    subcategories = db.query(models.Category).filter(
        models.Category.parent_id == category_id
    ).first()
    
    if subcategories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with subcategories"
        )
    
    # Check if category has products
    products = db.query(models.Product).filter(
        models.Product.category_id == category_id
    ).first()
    
    if products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with products"
        )
    
    db_category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if db_category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    db.delete(db_category)
    db.commit()

@router.get("/{category_id}/products", response_model=List[schemas.Product])
async def read_category_products(
    category_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all products in a specific category"""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    products = db.query(models.Product).filter(
        models.Product.category_id == category_id,
        models.Product.is_active == True
    ).offset(skip).limit(limit).all()
    
    return products

@router.get("/{category_id}/subcategories", response_model=List[schemas.Category])
async def read_subcategories(
    category_id: int,
    db: Session = Depends(get_db)
):
    """Get all subcategories of a specific category"""
    category = db.query(models.Category).filter(models.Category.id == category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    subcategories = db.query(models.Category).filter(
        models.Category.parent_id == category_id
    ).all()
    
    return subcategories

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models, schemas
from ..database import get_db
from .deps import get_current_user, get_current_active_user, verify_marketplace_access
from datetime import datetime
from sqlalchemy import or_

router = APIRouter()

async def update_product_stock(db: Session, order_items: List[models.OrderItem]):
    """Background task to update product stock quantities"""
    for item in order_items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            product.stock_quantity -= item.quantity
            db.add(product)
    db.commit()

@router.post("/", response_model=schemas.Order)
async def create_order(
    order: schemas.OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(verify_marketplace_access)
):
    """Create a new order"""
    # Validate products and calculate total
    total_amount = 0
    order_items = []
    
    for item in order.items:
        product = db.query(models.Product).filter(
            models.Product.id == item.product_id,
            models.Product.is_active == True
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item.product_id} not found"
            )
            
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product {product.title}"
            )
            
        item_total = product.price * item.quantity
        total_amount += item_total
        
        order_items.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "price": product.price,
            "currency": product.currency
        })

    # Create order
    db_order = models.Order(
        buyer_id=current_user.id,
        seller_id=product.owner_id,  # Assuming one seller per order for now
        total_amount=total_amount,
        currency=order.currency,
        status=models.OrderStatus.PENDING,
        shipping_address=order.shipping_address,
        payment_method=order.payment_method
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Create order items
    for item_data in order_items:
        db_item = models.OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_item)
    
    db.commit()
    db.refresh(db_order)
    
    # Update product stock in background
    background_tasks.add_task(update_product_stock, db, db_order.items)
    
    return db_order

@router.get("/", response_model=List[schemas.Order])
async def read_orders(
    skip: int = 0,
    limit: int = 20,
    status: Optional[models.OrderStatus] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get all orders for the current user (as buyer or seller)"""
    query = db.query(models.Order).filter(
        or_(
            models.Order.buyer_id == current_user.id,
            models.Order.seller_id == current_user.id
        )
    )
    
    if status:
        query = query.filter(models.Order.status == status)
    
    orders = query.order_by(models.Order.created_at.desc()).offset(skip).limit(limit).all()
    return orders

@router.get("/{order_id}", response_model=schemas.Order)
async def read_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get specific order details"""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        or_(
            models.Order.buyer_id == current_user.id,
            models.Order.seller_id == current_user.id
        )
    ).first()
    
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order

@router.put("/{order_id}/status", response_model=schemas.Order)
async def update_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Update order status (seller only)"""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.seller_id == current_user.id
    ).first()
    
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Validate status transition
    valid_transitions = {
        models.OrderStatus.PENDING: [models.OrderStatus.PAID, models.OrderStatus.CANCELLED],
        models.OrderStatus.PAID: [models.OrderStatus.SHIPPED],
        models.OrderStatus.SHIPPED: [models.OrderStatus.DELIVERED],
        models.OrderStatus.DELIVERED: [],
        models.OrderStatus.CANCELLED: []
    }
    
    if status_update.status not in valid_transitions[order.status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {order.status} to {status_update.status}"
        )
    
    order.status = status_update.status
    order.updated_at = datetime.utcnow()
    
    if status_update.tracking_number:
        order.tracking_number = status_update.tracking_number
    
    db.commit()
    db.refresh(order)
    return order

@router.post("/{order_id}/cancel", response_model=schemas.Order)
async def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Cancel an order (buyer only, if still pending)"""
    order = db.query(models.Order).filter(
        models.Order.id == order_id,
        models.Order.buyer_id == current_user.id,
        models.Order.status == models.OrderStatus.PENDING
    ).first()
    
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or cannot be cancelled"
        )
    
    order.status = models.OrderStatus.CANCELLED
    order.updated_at = datetime.utcnow()
    
    # Return items to stock
    for item in order.items:
        product = db.query(models.Product).filter(models.Product.id == item.product_id).first()
        if product:
            product.stock_quantity += item.quantity
    
    db.commit()
    db.refresh(order)
    return order

@router.get("/seller/stats", response_model=schemas.SellerStats)
async def get_seller_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """Get seller's order statistics"""
    if current_user.user_type != models.UserType.SELLER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a seller"
        )
    
    total_orders = db.query(models.Order).filter(
        models.Order.seller_id == current_user.id
    ).count()
    
    pending_orders = db.query(models.Order).filter(
        models.Order.seller_id == current_user.id,
        models.Order.status == models.OrderStatus.PENDING
    ).count()
    
    completed_orders = db.query(models.Order).filter(
        models.Order.seller_id == current_user.id,
        models.Order.status == models.OrderStatus.DELIVERED
    ).count()
    
    total_revenue = db.query(func.sum(models.Order.total_amount)).filter(
        models.Order.seller_id == current_user.id,
        models.Order.status != models.OrderStatus.CANCELLED
    ).scalar() or 0
    
    return {
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "total_revenue": total_revenue
    }

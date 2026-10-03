from datetime import datetime
import random
from models import db, Product, InventoryTransaction, StockAdjustment
from services.audit_service import create_notification, log_audit

def generate_adjustment_number():
    timestamp = datetime.utcnow().strftime('%Y%m%d')
    rand = random.randint(1000, 9999)
    return f"ADJ-{timestamp}-{rand}"

def record_transaction(product_id, quantity_change, transaction_type, reference_type=None, reference_id=None, reason='', user_id=None):
    """
    Core inventory ledger function.
    Updates product current_stock, writes to InventoryTransaction, and triggers notifications.
    """
    product = Product.query.get(product_id)
    if not product:
        raise ValueError(f"Product with ID {product_id} not found.")

    prev_qty = product.current_stock
    new_qty = prev_qty + quantity_change

    if new_qty < 0 and transaction_type not in ['stock_removed', 'damaged_stock']:
        raise ValueError(f"Insufficient stock for {product.name}. Current stock: {prev_qty}, Requested: {abs(quantity_change)}")

    product.current_stock = new_qty

    txn = InventoryTransaction(
        product_id=product.id,
        transaction_type=transaction_type,
        quantity_change=quantity_change,
        previous_quantity=prev_qty,
        new_quantity=new_qty,
        reference_type=reference_type,
        reference_id=reference_id,
        reason=reason,
        user_id=user_id,
        created_at=datetime.utcnow()
    )
    db.session.add(txn)

    # Check for Low / Out of Stock alerts
    if new_qty <= 0:
        create_notification(
            title=f"Out of Stock: {product.name}",
            message=f"Product '{product.name}' (SKU: {product.sku}) is now completely out of stock!",
            type='out_of_stock',
            link=f"/inventory/reorder"
        )
    elif new_qty <= product.min_stock_level:
        create_notification(
            title=f"Low Stock Alert: {product.name}",
            message=f"Product '{product.name}' (SKU: {product.sku}) stock dropped to {new_qty} (Minimum threshold: {product.min_stock_level}).",
            type='low_stock',
            link=f"/inventory/reorder"
        )

    return txn

def process_stock_adjustment(product_id, adjustment_type, quantity, reason, user_id):
    """
    Process manual stock adjustment (add, subtract, recount, damaged).
    """
    product = Product.query.get(product_id)
    if not product:
        raise ValueError("Product not found.")

    prev_qty = product.current_stock
    adj_number = generate_adjustment_number()

    if adjustment_type == 'add':
        qty_change = quantity
        new_qty = prev_qty + quantity
        txn_type = 'adjustment_add'
    elif adjustment_type in ['subtract', 'damaged']:
        qty_change = -quantity
        new_qty = prev_qty - quantity
        txn_type = 'damaged_stock' if adjustment_type == 'damaged' else 'adjustment_sub'
    elif adjustment_type == 'recount':
        new_qty = quantity
        qty_change = new_qty - prev_qty
        txn_type = 'adjustment_add' if qty_change >= 0 else 'adjustment_sub'
    else:
        raise ValueError(f"Invalid adjustment type: {adjustment_type}")

    if new_qty < 0:
        raise ValueError(f"Adjustment would result in negative stock ({new_qty}).")

    # Update product
    product.current_stock = new_qty

    # Create StockAdjustment record
    adjustment = StockAdjustment(
        adjustment_number=adj_number,
        product_id=product.id,
        adjustment_type=adjustment_type,
        quantity=quantity,
        previous_quantity=prev_qty,
        new_quantity=new_qty,
        reason=reason,
        user_id=user_id,
        created_at=datetime.utcnow()
    )
    db.session.add(adjustment)

    # Record in transaction ledger
    txn = InventoryTransaction(
        product_id=product.id,
        transaction_type=txn_type,
        quantity_change=qty_change,
        previous_quantity=prev_qty,
        new_quantity=new_qty,
        reference_type='adjustment',
        reference_id=adj_number,
        reason=reason or f"Stock adjustment: {adjustment_type}",
        user_id=user_id,
        created_at=datetime.utcnow()
    )
    db.session.add(txn)

    # Trigger stock alerts if threshold breached
    if new_qty <= 0:
        create_notification(
            title=f"Out of Stock: {product.name}",
            message=f"Product '{product.name}' (SKU: {product.sku}) is now completely out of stock!",
            type='out_of_stock',
            link=f"/inventory/reorder"
        )
    elif new_qty <= product.min_stock_level:
        create_notification(
            title=f"Low Stock Alert: {product.name}",
            message=f"Product '{product.name}' (SKU: {product.sku}) stock dropped to {new_qty} (Minimum threshold: {product.min_stock_level}).",
            type='low_stock',
            link=f"/inventory/reorder"
        )

    # General adjustment notification
    create_notification(
        title=f"Stock Adjusted: {product.name}",
        message=f"{product.name} adjusted ({adjustment_type}) by {qty_change:+d}. New quantity: {new_qty}.",
        type='adjustment',
        link=f"/inventory/ledger"
    )

    log_audit(
        action='STOCK_ADJUSTMENT',
        target_type='StockAdjustment',
        target_id=adj_number,
        details=f"Adjusted {product.name} ({product.sku}): {adjustment_type} {quantity}. Stock changed from {prev_qty} to {new_qty}. Reason: {reason}"
    )

    db.session.commit()
    return adjustment

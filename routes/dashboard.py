from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify
from flask_login import login_required
from sqlalchemy import func
from models import (
    db, Product, Category, Supplier, PurchaseOrder, Sale,
    InventoryTransaction
)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    # Key Summary Metrics
    total_products = Product.query.count()
    total_categories = Category.query.filter_by(is_active=True).count()
    total_suppliers = Supplier.query.filter_by(is_active=True).count()

    # Inventory Valuation
    all_products = Product.query.all()
    inventory_value = sum(p.inventory_value for p in all_products)
    retail_value = sum(p.retail_value for p in all_products)

    # Stock alerts count
    low_stock_count = sum(1 for p in all_products if p.is_low_stock)
    out_of_stock_count = sum(1 for p in all_products if p.is_out_of_stock)

    # Sales Metrics
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    month_start = datetime(today.year, today.month, 1)

    today_sales_val = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0.0))\
        .filter(Sale.status == 'Completed', Sale.sale_date >= today_start).scalar()

    month_sales_val = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0.0))\
        .filter(Sale.status == 'Completed', Sale.sale_date >= month_start).scalar()

    # Recent Records
    recent_transactions = InventoryTransaction.query.order_by(InventoryTransaction.created_at.desc()).limit(6).all()
    recent_purchases = PurchaseOrder.query.order_by(PurchaseOrder.order_date.desc()).limit(5).all()
    recent_sales = Sale.query.order_by(Sale.sale_date.desc()).limit(5).all()
    
    # Priority Low Stock List (top 5)
    urgent_low_stock = [p for p in all_products if p.current_stock <= p.min_stock_level][:5]

    return render_template(
        'dashboard/index.html',
        total_products=total_products,
        total_categories=total_categories,
        total_suppliers=total_suppliers,
        inventory_value=inventory_value,
        retail_value=retail_value,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        today_sales_val=today_sales_val,
        month_sales_val=month_sales_val,
        recent_transactions=recent_transactions,
        recent_purchases=recent_purchases,
        recent_sales=recent_sales,
        urgent_low_stock=urgent_low_stock
    )

@dashboard_bp.route('/dashboard/chart-data')
@login_required
def chart_data():
    """
    Returns JSON dataset for dynamic Chart.js rendering on Dashboard.
    """
    # 1. Last 7 Days Sales Trend
    today = datetime.utcnow().date()
    date_labels = []
    sales_trend_data = []

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)
        
        day_revenue = db.session.query(func.coalesce(func.sum(Sale.total_amount), 0.0))\
            .filter(Sale.status == 'Completed', Sale.sale_date >= day_start, Sale.sale_date < day_end).scalar()
            
        date_labels.append(day.strftime('%b %d'))
        sales_trend_data.append(round(float(day_revenue), 2))

    # 2. Category Distribution
    category_data = db.session.query(
        Category.name,
        func.count(Product.id)
    ).join(Product, Category.id == Product.category_id, isouter=True)\
     .group_by(Category.name)\
     .order_by(func.count(Product.id).desc())\
     .limit(6).all()

    category_labels = [c[0] for c in category_data]
    category_counts = [c[1] for c in category_data]

    # 3. Stock Movement by Type
    movement_breakdown = db.session.query(
        InventoryTransaction.transaction_type,
        func.count(InventoryTransaction.id)
    ).group_by(InventoryTransaction.transaction_type).all()

    type_map = {
        'stock_added': 'Purchases / Added',
        'stock_removed': 'Sales / Dispatched',
        'stock_returned': 'Customer Returns',
        'damaged_stock': 'Damaged / Spoiled',
        'adjustment_add': 'Adjustments (+)',
        'adjustment_sub': 'Adjustments (-)'
    }

    movement_labels = [type_map.get(m[0], m[0]) for m in movement_breakdown]
    movement_counts = [m[1] for m in movement_breakdown]

    return jsonify({
        'sales_trend': {
            'labels': date_labels,
            'data': sales_trend_data
        },
        'category_distribution': {
            'labels': category_labels,
            'data': category_counts
        },
        'movement_breakdown': {
            'labels': movement_labels,
            'data': movement_counts
        }
    })

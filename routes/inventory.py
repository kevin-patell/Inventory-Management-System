from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, Response
from flask_login import login_required, current_user
from models import db, Product, InventoryTransaction, StockAdjustment, Supplier
from forms import StockAdjustmentForm
from utils.decorators import manager_required
from services.inventory_service import process_stock_adjustment
from services.export_service import export_to_csv, export_to_excel
from config import Config

inventory_bp = Blueprint('inventory', __name__)

@inventory_bp.route('/inventory/ledger')
@login_required
def ledger():
    page = request.args.get('page', 1, type=int)
    txn_type = request.args.get('type', 'all')
    product_id = request.args.get('product_id', type=int)

    query = InventoryTransaction.query

    if txn_type != 'all':
        query = query.filter(InventoryTransaction.transaction_type == txn_type)

    if product_id:
        query = query.filter(InventoryTransaction.product_id == product_id)

    pagination = query.order_by(InventoryTransaction.created_at.desc()).paginate(
        page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False
    )
    transactions = pagination.items

    products = Product.query.order_by(Product.name).all()

    return render_template(
        'inventory/ledger.html',
        transactions=transactions,
        pagination=pagination,
        products=products,
        selected_type=txn_type,
        selected_product=product_id
    )

@inventory_bp.route('/inventory/adjust', methods=['GET', 'POST'])
@login_required
@manager_required
def adjust():
    form = StockAdjustmentForm()
    form.product_id.choices = [(p.id, f"{p.name} ({p.sku}) - Stock: {p.current_stock}") for p in Product.query.order_by(Product.name).all()]

    # If product preselected in query param
    req_prod = request.args.get('product_id', type=int)
    if request.method == 'GET' and req_prod:
        form.product_id.data = req_prod

    if form.validate_on_submit():
        try:
            adjustment = process_stock_adjustment(
                product_id=form.product_id.data,
                adjustment_type=form.adjustment_type.data,
                quantity=form.quantity.data,
                reason=form.reason.data.strip(),
                user_id=current_user.id
            )
            flash(f"Stock adjustment '{adjustment.adjustment_number}' processed successfully!", 'success')
            return redirect(url_for('inventory.ledger'))
        except ValueError as ve:
            flash(str(ve), 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f"Error during stock adjustment: {str(e)}", 'danger')

    recent_adjustments = StockAdjustment.query.order_by(StockAdjustment.created_at.desc()).limit(6).all()
    return render_template('inventory/adjustment.html', form=form, recent_adjustments=recent_adjustments)

@inventory_bp.route('/inventory/reorder')
@login_required
def reorder():
    # Fetch all items that are low in stock or out of stock
    reorder_products = Product.query.filter(
        Product.current_stock <= Product.min_stock_level,
        Product.status == 'Active'
    ).order_by(Product.current_stock.asc()).all()

    # Calculate suggested reorder quantity: (min_stock_level * 2) - current_stock
    reorder_data = []
    for p in reorder_products:
        suggested_qty = max(10, (p.min_stock_level * 2) - p.current_stock)
        est_cost = suggested_qty * p.purchase_price
        reorder_data.append({
            'product': p,
            'suggested_qty': suggested_qty,
            'est_cost': est_cost
        })

    return render_template('inventory/reorder.html', reorder_data=reorder_data)

@inventory_bp.route('/inventory/export/ledger-csv')
@login_required
def export_ledger_csv():
    transactions = InventoryTransaction.query.order_by(InventoryTransaction.created_at.desc()).all()
    headers = ['ID', 'Date/Time', 'Product SKU', 'Product Name', 'Type', 'Change', 'Prev Qty', 'New Qty', 'Reference', 'Reason', 'User']
    rows = []
    for t in transactions:
        rows.append([
            t.id,
            t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            t.product.sku if t.product else 'N/A',
            t.product.name if t.product else 'N/A',
            t.transaction_type,
            f"{t.quantity_change:+d}",
            t.previous_quantity,
            t.new_quantity,
            f"{t.reference_type or ''} {t.reference_id or ''}".strip(),
            t.reason or '',
            t.user.full_name if t.user else 'System'
        ])
    data = export_to_csv(headers, rows)
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=stock_ledger_export.csv"}
    )

@inventory_bp.route('/inventory/export/ledger-excel')
@login_required
def export_ledger_excel():
    transactions = InventoryTransaction.query.order_by(InventoryTransaction.created_at.desc()).all()
    headers = ['ID', 'Date/Time', 'Product SKU', 'Product Name', 'Type', 'Change', 'Prev Qty', 'New Qty', 'Reference', 'Reason', 'User']
    rows = []
    for t in transactions:
        rows.append([
            t.id,
            t.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            t.product.sku if t.product else 'N/A',
            t.product.name if t.product else 'N/A',
            t.transaction_type,
            t.quantity_change,
            t.previous_quantity,
            t.new_quantity,
            f"{t.reference_type or ''} {t.reference_id or ''}".strip(),
            t.reason or '',
            t.user.full_name if t.user else 'System'
        ])
    data = export_to_excel("Stock Movement Ledger", headers, rows)
    return Response(
        data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition": "attachment; filename=stock_ledger_export.xlsx"}
    )

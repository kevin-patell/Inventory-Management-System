import json
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response, send_file
from flask_login import login_required, current_user
import io
from models import db, PurchaseOrder, PurchaseItem, Supplier, Product, InventoryTransaction
from utils.decorators import manager_required, role_required
from utils.helpers import generate_po_number
from services.inventory_service import record_transaction
from services.audit_service import log_audit, create_notification
from services.pdf_service import generate_purchase_order_pdf
from services.export_service import export_to_csv, export_to_excel
from config import Config

purchases_bp = Blueprint('purchases', __name__)

@purchases_bp.route('/purchases')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all')
    supplier_id = request.args.get('supplier_id', type=int)

    query = PurchaseOrder.query

    if search:
        query = query.filter(
            (PurchaseOrder.po_number.ilike(f"%{search}%")) |
            (PurchaseOrder.supplier.has(Supplier.name.ilike(f"%{search}%")))
        )

    if status_filter != 'all':
        query = query.filter(PurchaseOrder.status == status_filter)

    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)

    pagination = query.order_by(PurchaseOrder.order_date.desc()).paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
    purchases = pagination.items

    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()

    return render_template(
        'purchases/index.html',
        purchases=purchases,
        pagination=pagination,
        suppliers=suppliers,
        selected_status=status_filter,
        selected_supplier=supplier_id,
        search_query=search
    )

@purchases_bp.route('/purchases/create', methods=['GET', 'POST'])
@login_required
@manager_required
def create():
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()
    products = Product.query.filter_by(status='Active').order_by(Product.name).all()

    if not suppliers:
        flash('Please add at least one supplier before creating purchase orders.', 'warning')
        return redirect(url_for('suppliers.create'))

    if not products:
        flash('Please add at least one product before creating purchase orders.', 'warning')
        return redirect(url_for('products.create'))

    # Check if pre-filling items from reorder page (e.g. reorder_product_id)
    reorder_product_id = request.args.get('reorder_product_id', type=int)

    if request.method == 'POST':
        try:
            supplier_id = int(request.form.get('supplier_id'))
            order_status = request.form.get('status', 'Received')
            payment_status = request.form.get('payment_status', 'Paid')
            notes = request.form.get('notes', '').strip()
            discount_amount = float(request.form.get('discount_amount', 0.0) or 0.0)
            tax_amount = float(request.form.get('tax_amount', 0.0) or 0.0)
            shipping_fee = float(request.form.get('shipping_fee', 0.0) or 0.0)

            # Parse line items submitted from form
            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            unit_prices = request.form.getlist('unit_price[]')

            if not product_ids or len(product_ids) == 0:
                flash('Please add at least one product to the purchase order.', 'danger')
                return render_template('purchases/create.html', suppliers=suppliers, products=products, reorder_product_id=reorder_product_id)

            po_number = generate_po_number()
            subtotal = 0.0

            # Calculate subtotal first
            for p_id, qty_str, price_str in zip(product_ids, quantities, unit_prices):
                qty = int(qty_str)
                price = float(price_str)
                if qty > 0 and price >= 0:
                    subtotal += (qty * price)

            total_amount = max(0.0, subtotal - discount_amount + tax_amount + shipping_fee)

            purchase = PurchaseOrder(
                po_number=po_number,
                supplier_id=supplier_id,
                user_id=current_user.id,
                order_date=datetime.utcnow(),
                status=order_status,
                payment_status=payment_status,
                subtotal=subtotal,
                discount_amount=discount_amount,
                tax_amount=tax_amount,
                shipping_fee=shipping_fee,
                total_amount=total_amount,
                notes=notes
            )
            db.session.add(purchase)
            db.session.flush()

            # Create items & update stock if 'Received'
            for p_id_str, qty_str, price_str in zip(product_ids, quantities, unit_prices):
                p_id = int(p_id_str)
                qty = int(qty_str)
                price = float(price_str)

                if qty <= 0:
                    continue

                item_total = qty * price
                item = PurchaseItem(
                    purchase_id=purchase.id,
                    product_id=p_id,
                    quantity=qty,
                    unit_price=price,
                    total_price=item_total
                )
                db.session.add(item)

                # Update purchase price on product for valuation
                prod = Product.query.get(p_id)
                if prod:
                    prod.purchase_price = price

                # If status is Received, add stock automatically!
                if order_status == 'Received':
                    record_transaction(
                        product_id=p_id,
                        quantity_change=qty,
                        transaction_type='stock_added',
                        reference_type='purchase',
                        reference_id=po_number,
                        reason=f"Purchase Order {po_number} received",
                        user_id=current_user.id
                    )

            db.session.commit()

            create_notification(
                title=f"New Purchase Order: {po_number}",
                message=f"Purchase order {po_number} created for supplier {purchase.supplier.name} totaling ₹{total_amount:,.2f}.",
                type='purchase',
                link=f"/purchases/{purchase.id}"
            )

            log_audit(
                action='PURCHASE_CREATE',
                target_type='PurchaseOrder',
                target_id=purchase.id,
                details=f"Created PO {po_number} ({order_status}) for supplier {purchase.supplier.name}, total ₹{total_amount:.2f}"
            )

            flash(f"Purchase order '{po_number}' created successfully!", 'success')
            return redirect(url_for('purchases.view', id=purchase.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Failed to create purchase order: {str(e)}", 'danger')

    return render_template('purchases/create.html', suppliers=suppliers, products=products, reorder_product_id=reorder_product_id)

@purchases_bp.route('/purchases/<int:id>')
@login_required
def view(id):
    purchase = PurchaseOrder.query.get_or_404(id)
    return render_template('purchases/view.html', purchase=purchase)

@purchases_bp.route('/purchases/<int:id>/invoice')
@login_required
def invoice(id):
    purchase = PurchaseOrder.query.get_or_404(id)
    return render_template('purchases/invoice.html', purchase=purchase, config=Config)

@purchases_bp.route('/purchases/<int:id>/pdf')
@login_required
def download_pdf(id):
    purchase = PurchaseOrder.query.get_or_404(id)
    pdf_bytes = generate_purchase_order_pdf(purchase)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{purchase.po_number}.pdf"
    )

@purchases_bp.route('/purchases/<int:id>/receive', methods=['POST'])
@login_required
@manager_required
def receive(id):
    purchase = PurchaseOrder.query.get_or_404(id)
    if purchase.status == 'Received':
        flash('This purchase order is already marked as received.', 'info')
        return redirect(url_for('purchases.view', id=purchase.id))

    if purchase.status == 'Cancelled':
        flash('Cancelled purchase orders cannot be received.', 'danger')
        return redirect(url_for('purchases.view', id=purchase.id))

    # Add stock for each line item
    for item in purchase.items:
        record_transaction(
            product_id=item.product_id,
            quantity_change=item.quantity,
            transaction_type='stock_added',
            reference_type='purchase',
            reference_id=purchase.po_number,
            reason=f"Purchase order {purchase.po_number} received in warehouse",
            user_id=current_user.id
        )

    purchase.status = 'Received'
    db.session.commit()

    log_audit('PURCHASE_RECEIVE', 'PurchaseOrder', purchase.id, f"Received items for PO {purchase.po_number}")
    flash(f"Purchase order {purchase.po_number} marked as Received. Stock quantities updated successfully!", 'success')
    return redirect(url_for('purchases.view', id=purchase.id))

@purchases_bp.route('/purchases/<int:id>/cancel', methods=['POST'])
@login_required
@manager_required
def cancel(id):
    purchase = PurchaseOrder.query.get_or_404(id)
    if purchase.status == 'Received':
        flash('Cannot cancel an already received purchase order directly. Please make a manual stock adjustment instead.', 'danger')
        return redirect(url_for('purchases.view', id=purchase.id))

    purchase.status = 'Cancelled'
    db.session.commit()
    log_audit('PURCHASE_CANCEL', 'PurchaseOrder', purchase.id, f"Cancelled pending PO {purchase.po_number}")
    flash(f"Purchase order {purchase.po_number} has been cancelled.", 'warning')
    return redirect(url_for('purchases.view', id=purchase.id))

@purchases_bp.route('/purchases/export/csv')
@login_required
def export_csv():
    purchases = PurchaseOrder.query.order_by(PurchaseOrder.order_date.desc()).all()
    headers = ['PO Number', 'Supplier', 'Order Date', 'Status', 'Payment Status', 'Items Count', 'Subtotal (₹)', 'Tax (₹)', 'Shipping (₹)', 'Discount (₹)', 'Total (₹)']
    rows = []
    for p in purchases:
        rows.append([
            p.po_number,
            p.supplier.name if p.supplier else 'N/A',
            p.order_date.strftime('%Y-%m-%d %H:%M'),
            p.status,
            p.payment_status,
            len(p.items),
            f"{p.subtotal:.2f}",
            f"{p.tax_amount:.2f}",
            f"{p.shipping_fee:.2f}",
            f"{p.discount_amount:.2f}",
            f"{p.total_amount:.2f}"
        ])
    data = export_to_csv(headers, rows)
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=purchases_export.csv"}
    )

@purchases_bp.route('/purchases/export/excel')
@login_required
def export_excel():
    purchases = PurchaseOrder.query.order_by(PurchaseOrder.order_date.desc()).all()
    headers = ['PO Number', 'Supplier', 'Order Date', 'Status', 'Payment Status', 'Items Count', 'Subtotal (₹)', 'Tax (₹)', 'Shipping (₹)', 'Discount (₹)', 'Total (₹)']
    rows = []
    for p in purchases:
        rows.append([
            p.po_number,
            p.supplier.name if p.supplier else 'N/A',
            p.order_date.strftime('%Y-%m-%d %H:%M'),
            p.status,
            p.payment_status,
            len(p.items),
            p.subtotal,
            p.tax_amount,
            p.shipping_fee,
            p.discount_amount,
            p.total_amount
        ])
    data = export_to_excel("Purchases Order List", headers, rows)
    return Response(
        data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition": "attachment; filename=purchases_export.xlsx"}
    )

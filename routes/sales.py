import io
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response, send_file
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, Sale, SaleItem, Customer, Product, InventoryTransaction
from utils.decorators import manager_required, role_required
from utils.helpers import generate_invoice_number
from services.inventory_service import record_transaction
from services.audit_service import log_audit, create_notification
from services.pdf_service import generate_sales_invoice_pdf
from services.export_service import export_to_csv, export_to_excel
from config import Config

sales_bp = Blueprint('sales', __name__)

@sales_bp.route('/sales')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    status_filter = request.args.get('status', 'all')
    payment_method = request.args.get('payment_method', 'all')

    query = Sale.query

    if search:
        query = query.filter(
            or_(
                Sale.invoice_number.ilike(f"%{search}%"),
                Sale.customer_name.ilike(f"%{search}%"),
                Sale.customer_phone.ilike(f"%{search}%")
            )
        )

    if status_filter != 'all':
        query = query.filter(Sale.status == status_filter)

    if payment_method != 'all':
        query = query.filter(Sale.payment_method == payment_method)

    pagination = query.order_by(Sale.sale_date.desc()).paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
    sales = pagination.items

    return render_template(
        'sales/index.html',
        sales=sales,
        pagination=pagination,
        selected_status=status_filter,
        selected_payment=payment_method,
        search_query=search
    )

@sales_bp.route('/sales/create', methods=['GET', 'POST'])
@login_required
def create():
    customers = Customer.query.order_by(Customer.name).all()
    products = Product.query.filter_by(status='Active').order_by(Product.name).all()

    if request.method == 'POST':
        try:
            customer_id_val = request.form.get('customer_id')
            customer_name_val = request.form.get('customer_name', 'Walk-in Customer').strip()
            customer_phone_val = request.form.get('customer_phone', '').strip()
            payment_method = request.form.get('payment_method', 'Cash')
            notes = request.form.get('notes', '').strip()
            discount_amount = float(request.form.get('discount_amount', 0.0) or 0.0)
            tax_amount = float(request.form.get('tax_amount', 0.0) or 0.0)

            # Customer link if existing chosen
            customer_id = int(customer_id_val) if customer_id_val and customer_id_val != '0' else None
            if customer_id:
                cust = Customer.query.get(customer_id)
                if cust:
                    customer_name_val = cust.name
                    if not customer_phone_val:
                        customer_phone_val = cust.phone

            product_ids = request.form.getlist('product_id[]')
            quantities = request.form.getlist('quantity[]')
            unit_prices = request.form.getlist('unit_price[]')

            if not product_ids or len(product_ids) == 0:
                flash('Please select at least one product item to sell.', 'danger')
                return render_template('sales/create.html', customers=customers, products=products)

            # Validate stock availability
            for p_id_str, qty_str in zip(product_ids, quantities):
                p_id = int(p_id_str)
                qty = int(qty_str)
                prod = Product.query.get(p_id)
                if not prod:
                    flash(f"Invalid product specified.", 'danger')
                    return render_template('sales/create.html', customers=customers, products=products)
                if prod.current_stock < qty:
                    flash(f"Insufficient stock for '{prod.name}'. Current stock is {prod.current_stock}, requested {qty}.", 'danger')
                    return render_template('sales/create.html', customers=customers, products=products)

            invoice_number = generate_invoice_number()
            subtotal = 0.0

            for qty_str, price_str in zip(quantities, unit_prices):
                qty = int(qty_str)
                price = float(price_str)
                subtotal += (qty * price)

            total_amount = max(0.0, subtotal - discount_amount + tax_amount)

            sale = Sale(
                invoice_number=invoice_number,
                customer_id=customer_id,
                customer_name=customer_name_val or 'Walk-in Customer',
                customer_phone=customer_phone_val,
                user_id=current_user.id,
                sale_date=datetime.utcnow(),
                status='Completed',
                payment_method=payment_method,
                subtotal=subtotal,
                discount_amount=discount_amount,
                tax_amount=tax_amount,
                total_amount=total_amount,
                notes=notes
            )
            db.session.add(sale)
            db.session.flush()

            # Create line items and deduct stock
            for p_id_str, qty_str, price_str in zip(product_ids, quantities, unit_prices):
                p_id = int(p_id_str)
                qty = int(qty_str)
                price = float(price_str)
                prod = Product.query.get(p_id)

                item = SaleItem(
                    sale_id=sale.id,
                    product_id=p_id,
                    quantity=qty,
                    unit_price=price,
                    cost_price=prod.purchase_price, # locked cost for profit margin tracking
                    total_price=qty * price
                )
                db.session.add(item)

                # Deduct inventory stock
                record_transaction(
                    product_id=p_id,
                    quantity_change=-qty,
                    transaction_type='stock_removed',
                    reference_type='sale',
                    reference_id=invoice_number,
                    reason=f"Sale order {invoice_number}",
                    user_id=current_user.id
                )

            db.session.commit()

            create_notification(
                title=f"Sale Completed: {invoice_number}",
                message=f"Sale {invoice_number} processed for {sale.customer_name} totaling ${total_amount:,.2f}.",
                type='sale',
                link=f"/sales/{sale.id}"
            )

            log_audit(
                action='SALE_CREATE',
                target_type='Sale',
                target_id=sale.id,
                details=f"Processed sale {invoice_number} for ${total_amount:.2f} ({payment_method})"
            )

            flash(f"Sale invoice '{invoice_number}' created successfully!", 'success')
            return redirect(url_for('sales.view', id=sale.id))

        except Exception as e:
            db.session.rollback()
            flash(f"Failed to process sale: {str(e)}", 'danger')

    return render_template('sales/create.html', customers=customers, products=products)

@sales_bp.route('/sales/<int:id>')
@login_required
def view(id):
    sale = Sale.query.get_or_404(id)
    return render_template('sales/view.html', sale=sale)

@sales_bp.route('/sales/<int:id>/invoice')
@login_required
def invoice(id):
    sale = Sale.query.get_or_404(id)
    return render_template('sales/invoice.html', sale=sale, config=Config)

@sales_bp.route('/sales/<int:id>/pdf')
@login_required
def download_pdf(id):
    sale = Sale.query.get_or_404(id)
    pdf_bytes = generate_sales_invoice_pdf(sale)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{sale.invoice_number}.pdf"
    )

@sales_bp.route('/sales/<int:id>/return', methods=['POST'])
@login_required
@manager_required
def return_sale(id):
    sale = Sale.query.get_or_404(id)
    if sale.status == 'Returned':
        flash('This sale order has already been marked as returned.', 'info')
        return redirect(url_for('sales.view', id=sale.id))

    reason = request.form.get('return_reason', 'Customer return requested').strip()

    # Restore stock for each item
    for item in sale.items:
        record_transaction(
            product_id=item.product_id,
            quantity_change=item.quantity,
            transaction_type='stock_returned',
            reference_type='sale',
            reference_id=sale.invoice_number,
            reason=f"Sale {sale.invoice_number} returned: {reason}",
            user_id=current_user.id
        )

    sale.status = 'Returned'
    sale.notes = (sale.notes or '') + f"\n[Returned: {reason}]"
    db.session.commit()

    create_notification(
        title=f"Sale Returned: {sale.invoice_number}",
        message=f"Sale {sale.invoice_number} was marked as Returned. Stock items restored.",
        type='sale',
        link=f"/sales/{sale.id}"
    )

    log_audit('SALE_RETURN', 'Sale', sale.id, f"Returned sale {sale.invoice_number}. Reason: {reason}")
    flash(f"Sale {sale.invoice_number} has been marked as Returned and stock restored to inventory.", 'warning')
    return redirect(url_for('sales.view', id=sale.id))

@sales_bp.route('/sales/export/csv')
@login_required
def export_csv():
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    headers = ['Invoice Number', 'Customer', 'Phone', 'Date', 'Status', 'Payment Method', 'Items Count', 'Subtotal ($)', 'Discount ($)', 'Tax ($)', 'Total ($)', 'Profit ($)']
    rows = []
    for s in sales:
        rows.append([
            s.invoice_number,
            s.customer_name,
            s.customer_phone or '',
            s.sale_date.strftime('%Y-%m-%d %H:%M'),
            s.status,
            s.payment_method,
            len(s.items),
            f"{s.subtotal:.2f}",
            f"{s.discount_amount:.2f}",
            f"{s.tax_amount:.2f}",
            f"{s.total_amount:.2f}",
            f"{s.gross_profit:.2f}"
        ])
    data = export_to_csv(headers, rows)
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=sales_export.csv"}
    )

@sales_bp.route('/sales/export/excel')
@login_required
def export_excel():
    sales = Sale.query.order_by(Sale.sale_date.desc()).all()
    headers = ['Invoice Number', 'Customer', 'Phone', 'Date', 'Status', 'Payment Method', 'Items Count', 'Subtotal ($)', 'Discount ($)', 'Tax ($)', 'Total ($)', 'Profit ($)']
    rows = []
    for s in sales:
        rows.append([
            s.invoice_number,
            s.customer_name,
            s.customer_phone or '',
            s.sale_date.strftime('%Y-%m-%d %H:%M'),
            s.status,
            s.payment_method,
            len(s.items),
            s.subtotal,
            s.discount_amount,
            s.tax_amount,
            s.total_amount,
            s.gross_profit
        ])
    data = export_to_excel("Sales Orders List", headers, rows)
    return Response(
        data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition": "attachment; filename=sales_export.xlsx"}
    )

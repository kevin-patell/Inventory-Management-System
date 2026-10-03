from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, Response
from flask_login import login_required, current_user
from sqlalchemy import or_
from models import db, Product, Category, Supplier, InventoryTransaction
from forms import ProductForm
from utils.decorators import role_required, manager_required
from utils.helpers import save_product_image, generate_sku
from services.inventory_service import record_transaction
from services.audit_service import log_audit, create_notification
from services.export_service import export_to_csv, export_to_excel
from config import Config

products_bp = Blueprint('products', __name__)

@products_bp.route('/products')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '').strip()
    category_id = request.args.get('category_id', type=int)
    supplier_id = request.args.get('supplier_id', type=int)
    stock_status = request.args.get('stock_status', 'all')
    sort_by = request.args.get('sort_by', 'newest')

    query = Product.query

    # Search filter
    if search_query:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search_query}%"),
                Product.sku.ilike(f"%{search_query}%"),
                Product.description.ilike(f"%{search_query}%")
            )
        )

    # Category filter
    if category_id:
        query = query.filter(Product.category_id == category_id)

    # Supplier filter
    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)

    # Stock Status filter
    if stock_status == 'low_stock':
        query = query.filter(Product.current_stock > 0, Product.current_stock <= Product.min_stock_level)
    elif stock_status == 'out_of_stock':
        query = query.filter(Product.current_stock <= 0)
    elif stock_status == 'in_stock':
        query = query.filter(Product.current_stock > Product.min_stock_level)

    # Sorting
    if sort_by == 'name_asc':
        query = query.order_by(Product.name.asc())
    elif sort_by == 'name_desc':
        query = query.order_by(Product.name.desc())
    elif sort_by == 'price_asc':
        query = query.order_by(Product.selling_price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.selling_price.desc())
    elif sort_by == 'stock_asc':
        query = query.order_by(Product.current_stock.asc())
    elif sort_by == 'stock_desc':
        query = query.order_by(Product.current_stock.desc())
    else:  # newest
        query = query.order_by(Product.created_at.desc())

    pagination = query.paginate(page=page, per_page=Config.ITEMS_PER_PAGE, error_out=False)
    products = pagination.items

    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    suppliers = Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()

    return render_template(
        'products/index.html',
        products=products,
        pagination=pagination,
        categories=categories,
        suppliers=suppliers,
        search_query=search_query,
        selected_category=category_id,
        selected_supplier=supplier_id,
        selected_status=stock_status,
        selected_sort=sort_by
    )

@products_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@manager_required
def create():
    form = ProductForm()
    # Populate dropdown choices
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).order_by(Category.name).all()]
    form.supplier_id.choices = [(0, '-- None / Unassigned --')] + [(s.id, s.name) for s in Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()]

    if not form.category_id.choices:
        flash('Please create at least one category before adding products.', 'warning')
        return redirect(url_for('categories.index'))

    if request.method == 'GET' and not form.sku.data:
        form.sku.data = generate_sku()

    if form.validate_on_submit():
        # Check SKU uniqueness
        existing_sku = Product.query.filter_by(sku=form.sku.data.strip()).first()
        if existing_sku:
            flash(f"A product with SKU '{form.sku.data}' already exists.", 'danger')
            return render_template('products/form.html', form=form, title='Add New Product', is_edit=False)

        image_filename = save_product_image(form.image.data)

        supplier_id_val = form.supplier_id.data if form.supplier_id.data != 0 else None

        product = Product(
            sku=form.sku.data.strip().upper(),
            name=form.name.data.strip(),
            description=form.description.data.strip() if form.description.data else '',
            category_id=form.category_id.data,
            supplier_id=supplier_id_val,
            purchase_price=float(form.purchase_price.data),
            selling_price=float(form.selling_price.data),
            current_stock=0,  # updated via ledger below if initial > 0
            min_stock_level=int(form.min_stock_level.data),
            image_url=image_filename,
            status=form.status.data
        )
        db.session.add(product)
        db.session.flush()

        initial_qty = int(form.current_stock.data or 0)
        if initial_qty > 0:
            record_transaction(
                product_id=product.id,
                quantity_change=initial_qty,
                transaction_type='stock_added',
                reference_type='manual',
                reason='Initial stock setup upon product creation',
                user_id=current_user.id
            )
        else:
            product.current_stock = 0

        db.session.commit()

        log_audit(
            action='PRODUCT_CREATE',
            target_type='Product',
            target_id=product.id,
            details=f"Created product {product.name} (SKU: {product.sku}) with initial stock {initial_qty}"
        )

        flash(f"Product '{product.name}' created successfully!", 'success')
        return redirect(url_for('products.view', id=product.id))

    return render_template('products/form.html', form=form, title='Add New Product', is_edit=False)

@products_bp.route('/products/<int:id>')
@login_required
def view(id):
    product = Product.query.get_or_404(id)
    recent_transactions = InventoryTransaction.query.filter_by(product_id=product.id)\
        .order_by(InventoryTransaction.created_at.desc()).limit(10).all()
    return render_template('products/view.html', product=product, recent_transactions=recent_transactions)

@products_bp.route('/products/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@manager_required
def edit(id):
    product = Product.query.get_or_404(id)
    form = ProductForm(obj=product)

    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(is_active=True).order_by(Category.name).all()]
    form.supplier_id.choices = [(0, '-- None / Unassigned --')] + [(s.id, s.name) for s in Supplier.query.filter_by(is_active=True).order_by(Supplier.name).all()]

    if request.method == 'GET':
        form.supplier_id.data = product.supplier_id or 0

    if form.validate_on_submit():
        # Check SKU uniqueness if changed
        new_sku = form.sku.data.strip().upper()
        if new_sku != product.sku:
            existing = Product.query.filter_by(sku=new_sku).first()
            if existing:
                flash(f"SKU '{new_sku}' is already assigned to another product.", 'danger')
                return render_template('products/form.html', form=form, title='Edit Product', is_edit=True, product=product)

        product.sku = new_sku
        product.name = form.name.data.strip()
        product.description = form.description.data.strip() if form.description.data else ''
        product.category_id = form.category_id.data
        product.supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None
        product.purchase_price = float(form.purchase_price.data)
        product.selling_price = float(form.selling_price.data)
        product.min_stock_level = int(form.min_stock_level.data)
        product.status = form.status.data

        # Handle image replacement
        if form.image.data and form.image.data.filename:
            product.image_url = save_product_image(form.image.data)

        db.session.commit()

        log_audit(
            action='PRODUCT_UPDATE',
            target_type='Product',
            target_id=product.id,
            details=f"Updated product {product.name} (SKU: {product.sku})"
        )

        flash(f"Product '{product.name}' updated successfully!", 'success')
        return redirect(url_for('products.view', id=product.id))

    return render_template('products/form.html', form=form, title='Edit Product', is_edit=True, product=product)

@products_bp.route('/products/<int:id>/toggle-status', methods=['POST'])
@login_required
@manager_required
def toggle_status(id):
    product = Product.query.get_or_404(id)
    product.status = 'Inactive' if product.status == 'Active' else 'Active'
    db.session.commit()
    log_audit('PRODUCT_STATUS_TOGGLE', 'Product', product.id, f"Toggled status to {product.status}")
    flash(f"Product '{product.name}' status set to {product.status}.", 'info')
    return redirect(request.referrer or url_for('products.index'))

@products_bp.route('/products/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete(id):
    product = Product.query.get_or_404(id)
    # Check if product is in purchases or sales
    if product.purchase_items or product.sale_items:
        # Cannot hard-delete; deactivate safely
        product.status = 'Discontinued'
        db.session.commit()
        flash(f"Product '{product.name}' has transaction history. To protect records, it has been marked as Discontinued.", 'warning')
        return redirect(url_for('products.index'))

    prod_name = product.name
    prod_sku = product.sku
    db.session.delete(product)
    db.session.commit()

    log_audit('PRODUCT_DELETE', 'Product', id, f"Deleted product {prod_name} ({prod_sku})")
    flash(f"Product '{prod_name}' has been deleted.", 'info')
    return redirect(url_for('products.index'))

@products_bp.route('/products/generate-sku')
@login_required
def api_generate_sku():
    return jsonify({'sku': generate_sku()})

@products_bp.route('/products/export/csv')
@login_required
def export_csv():
    products = Product.query.order_by(Product.name).all()
    headers = ['ID', 'SKU', 'Name', 'Category', 'Supplier', 'Cost Price ($)', 'Retail Price ($)', 'Current Stock', 'Min Level', 'Stock Status', 'Inventory Value ($)', 'Status']
    rows = []
    for p in products:
        rows.append([
            p.id,
            p.sku,
            p.name,
            p.category.name if p.category else 'N/A',
            p.supplier.name if p.supplier else 'N/A',
            f"{p.purchase_price:.2f}",
            f"{p.selling_price:.2f}",
            p.current_stock,
            p.min_stock_level,
            p.stock_status,
            f"{p.inventory_value:.2f}",
            p.status
        ])
    data = export_to_csv(headers, rows)
    return Response(
        data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=products_export.csv"}
    )

@products_bp.route('/products/export/excel')
@login_required
def export_excel():
    products = Product.query.order_by(Product.name).all()
    headers = ['ID', 'SKU', 'Name', 'Category', 'Supplier', 'Cost Price ($)', 'Retail Price ($)', 'Current Stock', 'Min Level', 'Stock Status', 'Inventory Value ($)', 'Status']
    rows = []
    for p in products:
        rows.append([
            p.id,
            p.sku,
            p.name,
            p.category.name if p.category else 'N/A',
            p.supplier.name if p.supplier else 'N/A',
            p.purchase_price,
            p.selling_price,
            p.current_stock,
            p.min_stock_level,
            p.stock_status,
            p.inventory_value,
            p.status
        ])
    data = export_to_excel("Products Master List", headers, rows)
    return Response(
        data,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-disposition": "attachment; filename=products_export.xlsx"}
    )

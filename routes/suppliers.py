from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Supplier, Product, PurchaseOrder
from forms import SupplierForm
from utils.decorators import manager_required, role_required
from services.audit_service import log_audit

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/suppliers')
@login_required
def index():
    search = request.args.get('q', '').strip()
    query = Supplier.query
    if search:
        query = query.filter(
            (Supplier.name.ilike(f"%{search}%")) |
            (Supplier.contact_person.ilike(f"%{search}%")) |
            (Supplier.email.ilike(f"%{search}%")) |
            (Supplier.phone.ilike(f"%{search}%"))
        )
    suppliers = query.order_by(Supplier.name).all()
    return render_template('suppliers/index.html', suppliers=suppliers, search_query=search)

@suppliers_bp.route('/suppliers/create', methods=['GET', 'POST'])
@login_required
@manager_required
def create():
    form = SupplierForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        existing = Supplier.query.filter(Supplier.name.ilike(name)).first()
        if existing:
            flash(f"A supplier with name '{name}' already exists.", 'danger')
            return render_template('suppliers/form.html', form=form, title='Add New Supplier', is_edit=False)

        supplier = Supplier(
            name=name,
            contact_person=form.contact_person.data.strip() if form.contact_person.data else '',
            email=form.email.data.strip() if form.email.data else '',
            phone=form.phone.data.strip() if form.phone.data else '',
            address=form.address.data.strip() if form.address.data else '',
            tax_number=form.tax_number.data.strip() if form.tax_number.data else '',
            notes=form.notes.data.strip() if form.notes.data else '',
            is_active=form.is_active.data
        )
        db.session.add(supplier)
        db.session.commit()

        log_audit('SUPPLIER_CREATE', 'Supplier', supplier.id, f"Created supplier '{supplier.name}'")
        flash(f"Supplier '{supplier.name}' created successfully!", 'success')
        return redirect(url_for('suppliers.view', id=supplier.id))

    return render_template('suppliers/form.html', form=form, title='Add New Supplier', is_edit=False)

@suppliers_bp.route('/suppliers/<int:id>')
@login_required
def view(id):
    supplier = Supplier.query.get_or_404(id)
    products = Product.query.filter_by(supplier_id=supplier.id).all()
    purchases = PurchaseOrder.query.filter_by(supplier_id=supplier.id).order_by(PurchaseOrder.order_date.desc()).all()
    
    total_spent = sum(po.total_amount for po in purchases if po.status == 'Received')
    total_inventory_value = sum(p.inventory_value for p in products)

    return render_template(
        'suppliers/view.html',
        supplier=supplier,
        products=products,
        purchases=purchases,
        total_spent=total_spent,
        total_inventory_value=total_inventory_value
    )

@suppliers_bp.route('/suppliers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@manager_required
def edit(id):
    supplier = Supplier.query.get_or_404(id)
    form = SupplierForm(obj=supplier)

    if form.validate_on_submit():
        supplier.name = form.name.data.strip()
        supplier.contact_person = form.contact_person.data.strip() if form.contact_person.data else ''
        supplier.email = form.email.data.strip() if form.email.data else ''
        supplier.phone = form.phone.data.strip() if form.phone.data else ''
        supplier.address = form.address.data.strip() if form.address.data else ''
        supplier.tax_number = form.tax_number.data.strip() if form.tax_number.data else ''
        supplier.notes = form.notes.data.strip() if form.notes.data else ''
        supplier.is_active = form.is_active.data

        db.session.commit()
        log_audit('SUPPLIER_UPDATE', 'Supplier', supplier.id, f"Updated supplier '{supplier.name}'")
        flash(f"Supplier '{supplier.name}' updated successfully!", 'success')
        return redirect(url_for('suppliers.view', id=supplier.id))

    return render_template('suppliers/form.html', form=form, title='Edit Supplier', is_edit=True, supplier=supplier)

@suppliers_bp.route('/suppliers/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete(id):
    supplier = Supplier.query.get_or_404(id)
    if supplier.purchases.count() > 0 or supplier.products.count() > 0:
        supplier.is_active = False
        db.session.commit()
        flash(f"Supplier '{supplier.name}' has associated purchases or products. It has been deactivated instead of deleted.", 'warning')
        return redirect(url_for('suppliers.index'))

    supp_name = supplier.name
    db.session.delete(supplier)
    db.session.commit()
    log_audit('SUPPLIER_DELETE', 'Supplier', id, f"Deleted supplier '{supp_name}'")
    flash(f"Supplier '{supp_name}' deleted.", 'info')
    return redirect(url_for('suppliers.index'))

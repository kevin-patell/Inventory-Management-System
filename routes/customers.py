from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Customer, Sale
from forms import CustomerForm
from utils.decorators import role_required, manager_required
from services.audit_service import log_audit

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers')
@login_required
def index():
    search = request.args.get('q', '').strip()
    query = Customer.query
    if search:
        query = query.filter(
            (Customer.name.ilike(f"%{search}%")) |
            (Customer.email.ilike(f"%{search}%")) |
            (Customer.phone.ilike(f"%{search}%"))
        )
    customers = query.order_by(Customer.name).all()
    return render_template('customers/index.html', customers=customers, search_query=search)

@customers_bp.route('/customers/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CustomerForm()
    if form.validate_on_submit():
        customer = Customer(
            name=form.name.data.strip(),
            email=form.email.data.strip() if form.email.data else '',
            phone=form.phone.data.strip() if form.phone.data else '',
            address=form.address.data.strip() if form.address.data else ''
        )
        db.session.add(customer)
        db.session.commit()

        log_audit('CUSTOMER_CREATE', 'Customer', customer.id, f"Created customer '{customer.name}'")
        flash(f"Customer '{customer.name}' created successfully!", 'success')
        return redirect(url_for('customers.view', id=customer.id))

    return render_template('customers/form.html', form=form, title='Add Customer', is_edit=False)

@customers_bp.route('/customers/<int:id>')
@login_required
def view(id):
    customer = Customer.query.get_or_404(id)
    sales = Sale.query.filter_by(customer_id=customer.id).order_by(Sale.sale_date.desc()).all()
    total_spent = sum(s.total_amount for s in sales if s.status == 'Completed')
    return render_template('customers/view.html', customer=customer, sales=sales, total_spent=total_spent)

@customers_bp.route('/customers/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    customer = Customer.query.get_or_404(id)
    form = CustomerForm(obj=customer)

    if form.validate_on_submit():
        customer.name = form.name.data.strip()
        customer.email = form.email.data.strip() if form.email.data else ''
        customer.phone = form.phone.data.strip() if form.phone.data else ''
        customer.address = form.address.data.strip() if form.address.data else ''

        db.session.commit()
        log_audit('CUSTOMER_UPDATE', 'Customer', customer.id, f"Updated customer '{customer.name}'")
        flash(f"Customer '{customer.name}' updated successfully!", 'success')
        return redirect(url_for('customers.view', id=customer.id))

    return render_template('customers/form.html', form=form, title='Edit Customer', is_edit=True, customer=customer)

@customers_bp.route('/customers/<int:id>/delete', methods=['POST'])
@login_required
@manager_required
def delete(id):
    customer = Customer.query.get_or_404(id)
    if customer.sales.count() > 0:
        flash(f"Cannot delete customer '{customer.name}' because they have existing order history.", 'danger')
        return redirect(url_for('customers.view', id=customer.id))

    name = customer.name
    db.session.delete(customer)
    db.session.commit()
    log_audit('CUSTOMER_DELETE', 'Customer', id, f"Deleted customer '{name}'")
    flash(f"Customer '{name}' deleted.", 'info')
    return redirect(url_for('customers.index'))

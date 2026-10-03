from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from models import db, Category, Product
from forms import CategoryForm
from utils.decorators import manager_required, role_required
from services.audit_service import log_audit

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories', methods=['GET', 'POST'])
@login_required
def index():
    form = CategoryForm()
    # Populate parent categories
    parent_choices = [(0, '-- None (Top-Level Category) --')] + [
        (c.id, c.name) for c in Category.query.filter_by(parent_id=None, is_active=True).order_by(Category.name).all()
    ]
    form.parent_id.choices = parent_choices

    if form.validate_on_submit() and current_user_can_manage():
        name = form.name.data.strip()
        existing = Category.query.filter(Category.name.ilike(name)).first()
        if existing:
            flash(f"Category '{name}' already exists.", 'danger')
        else:
            parent_id = form.parent_id.data if form.parent_id.data != 0 else None
            category = Category(
                name=name,
                parent_id=parent_id,
                description=form.description.data.strip() if form.description.data else '',
                is_active=form.is_active.data
            )
            db.session.add(category)
            db.session.commit()
            log_audit('CATEGORY_CREATE', 'Category', category.id, f"Created category '{category.name}'")
            flash(f"Category '{category.name}' created successfully!", 'success')
            return redirect(url_for('categories.index'))

    categories = Category.query.order_by(Category.name).all()
    return render_template('categories/index.html', categories=categories, form=form)

def current_user_can_manage():
    from flask_login import current_user
    return current_user.has_role('Admin', 'Manager')

@categories_bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@manager_required
def edit(id):
    category = Category.query.get_or_404(id)
    form = CategoryForm(obj=category)

    parent_choices = [(0, '-- None (Top-Level Category) --')] + [
        (c.id, c.name) for c in Category.query.filter(Category.id != id, Category.parent_id == None, Category.is_active == True).order_by(Category.name).all()
    ]
    form.parent_id.choices = parent_choices

    if request.method == 'GET':
        form.parent_id.data = category.parent_id or 0

    if form.validate_on_submit():
        new_name = form.name.data.strip()
        existing = Category.query.filter(Category.name.ilike(new_name), Category.id != id).first()
        if existing:
            flash(f"Another category with name '{new_name}' already exists.", 'danger')
            return render_template('categories/edit.html', form=form, category=category)

        category.name = new_name
        category.parent_id = form.parent_id.data if form.parent_id.data != 0 else None
        category.description = form.description.data.strip() if form.description.data else ''
        category.is_active = form.is_active.data

        db.session.commit()
        log_audit('CATEGORY_UPDATE', 'Category', category.id, f"Updated category '{category.name}'")
        flash(f"Category '{category.name}' updated successfully!", 'success')
        return redirect(url_for('categories.index'))

    return render_template('categories/edit.html', form=form, category=category)

@categories_bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete(id):
    category = Category.query.get_or_404(id)
    if category.products.count() > 0:
        flash(f"Cannot delete category '{category.name}' because it contains {category.products.count()} products. Reassign or delete products first.", 'danger')
        return redirect(url_for('categories.index'))

    cat_name = category.name
    db.session.delete(category)
    db.session.commit()
    log_audit('CATEGORY_DELETE', 'Category', id, f"Deleted category '{cat_name}'")
    flash(f"Category '{cat_name}' deleted.", 'info')
    return redirect(url_for('categories.index'))

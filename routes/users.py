from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import db, User, Role
from forms import UserAdminForm
from utils.decorators import admin_required
from services.audit_service import log_audit

users_bp = Blueprint('users', __name__)

@users_bp.route('/users')
@login_required
@admin_required
def index():
    users = User.query.order_by(User.id.asc()).all()
    return render_template('users/index.html', users=users)

@users_bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    form = UserAdminForm()
    form.role_id.choices = [(r.id, r.name) for r in Role.query.order_by(Role.id).all()]

    if form.validate_on_submit():
        if not form.password.data:
            flash('Password is required when creating a new user.', 'danger')
            return render_template('users/form.html', form=form, title='Create New User', is_edit=False)

        username = form.username.data.strip()
        email = form.email.data.strip()

        if User.query.filter_by(username=username).first():
            flash('Username is already taken.', 'danger')
            return render_template('users/form.html', form=form, title='Create New User', is_edit=False)

        if User.query.filter_by(email=email).first():
            flash('Email address is already registered.', 'danger')
            return render_template('users/form.html', form=form, title='Create New User', is_edit=False)

        user = User(
            username=username,
            email=email,
            full_name=form.full_name.data.strip(),
            phone=form.phone.data.strip() if form.phone.data else None,
            role_id=form.role_id.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        log_audit(
            action='USER_CREATE',
            target_type='User',
            target_id=user.id,
            details=f"Admin created new user {user.username} with role {user.role.name}"
        )

        flash(f"User account '{user.username}' created successfully!", 'success')
        return redirect(url_for('users.index'))

    return render_template('users/form.html', form=form, title='Create New User', is_edit=False)

@users_bp.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(id):
    user = User.query.get_or_404(id)
    form = UserAdminForm(obj=user)
    form.role_id.choices = [(r.id, r.name) for r in Role.query.order_by(Role.id).all()]

    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip()

        # Check uniqueness
        existing_u = User.query.filter(User.username == username, User.id != id).first()
        if existing_u:
            flash('Username is already taken.', 'danger')
            return render_template('users/form.html', form=form, title='Edit User', is_edit=True, user=user)

        existing_e = User.query.filter(User.email == email, User.id != id).first()
        if existing_e:
            flash('Email is already registered.', 'danger')
            return render_template('users/form.html', form=form, title='Edit User', is_edit=True, user=user)

        user.username = username
        user.email = email
        user.full_name = form.full_name.data.strip()
        user.phone = form.phone.data.strip() if form.phone.data else None
        
        # Don't let an admin accidentally lock themselves out of admin status
        if current_user.id == user.id and form.role_id.data != user.role_id:
            flash('You cannot change your own role from Admin.', 'warning')
        else:
            user.role_id = form.role_id.data

        if current_user.id == user.id and not form.is_active.data:
            flash('You cannot deactivate your own active account.', 'warning')
        else:
            user.is_active = form.is_active.data

        if form.password.data:
            user.set_password(form.password.data)
            flash('User password reset successfully.', 'info')

        db.session.commit()
        log_audit(
            action='USER_UPDATE',
            target_type='User',
            target_id=user.id,
            details=f"Admin updated user {user.username} (Role: {user.role.name}, Active: {user.is_active})"
        )

        flash(f"User account '{user.username}' updated successfully!", 'success')
        return redirect(url_for('users.index'))

    return render_template('users/form.html', form=form, title='Edit User', is_edit=True, user=user)

@users_bp.route('/users/<int:id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_status(id):
    if current_user.id == id:
        flash('You cannot deactivate yourself!', 'danger')
        return redirect(url_for('users.index'))

    user = User.query.get_or_404(id)
    user.is_active = not user.is_active
    db.session.commit()
    log_audit('USER_STATUS_TOGGLE', 'User', user.id, f"Toggled status to {user.is_active}")
    flash(f"User {user.username} is now {'Active' if user.is_active else 'Deactivated'}.", 'info')
    return redirect(url_for('users.index'))

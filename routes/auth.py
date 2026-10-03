from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User
from forms import LoginForm, ProfileForm
from services.audit_service import log_audit

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        login_input = form.username.data.strip()
        user = User.query.filter(
            (User.username == login_input) | (User.email == login_input)
        ).first()

        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an Administrator.', 'danger')
                return render_template('auth/login.html', form=form)

            user.last_login = datetime.utcnow()
            db.session.commit()
            login_user(user, remember=form.remember.data)

            log_audit(
                action='LOGIN',
                target_type='User',
                target_id=user.id,
                details=f"User {user.username} logged in successfully.",
                user=user
            )

            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid username/email or password.', 'danger')
            log_audit(
                action='FAILED_LOGIN',
                target_type='Auth',
                details=f"Failed login attempt for: {login_input}"
            )

    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    u_id = current_user.id
    logout_user()
    log_audit(
        action='LOGOUT',
        target_type='User',
        target_id=u_id,
        details=f"User {username} logged out."
    )
    flash('You have been securely signed out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)

    if form.validate_on_submit():
        # Check email uniqueness if changed
        if form.email.data != current_user.email:
            existing = User.query.filter_by(email=form.email.data).first()
            if existing:
                flash('That email address is already in use.', 'danger')
                return render_template('auth/profile.html', form=form)

        current_user.full_name = form.full_name.data.strip()
        current_user.email = form.email.data.strip()
        current_user.phone = form.phone.data.strip() if form.phone.data else None

        # Password change
        if form.new_password.data:
            if not form.current_password.data:
                flash('Please provide your current password to set a new password.', 'danger')
                return render_template('auth/profile.html', form=form)
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect.', 'danger')
                return render_template('auth/profile.html', form=form)

            current_user.set_password(form.new_password.data)
            flash('Password updated successfully.', 'success')

        db.session.commit()
        log_audit(
            action='PROFILE_UPDATE',
            target_type='User',
            target_id=current_user.id,
            details=f"User {current_user.username} updated their profile."
        )
        flash('Profile settings updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html', form=form)

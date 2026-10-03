from functools import wraps
from flask import abort, flash, redirect, url_for, request, jsonify
from flask_login import current_user

def role_required(*role_names):
    """
    Decorator to restrict view access to specific roles.
    Example: @role_required('Admin', 'Manager')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Unauthorized', 'message': 'Authentication required.'}), 401
                return redirect(url_for('auth.login', next=request.url))

            if not current_user.has_role(*role_names):
                if request.path.startswith('/api/'):
                    return jsonify({'error': 'Forbidden', 'message': 'You do not have permission to access this resource.'}), 403
                flash('Access denied. You do not have permission to view that page.', 'danger')
                return redirect(url_for('dashboard.index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('Admin')(f)

def manager_required(f):
    return role_required('Admin', 'Manager')(f)

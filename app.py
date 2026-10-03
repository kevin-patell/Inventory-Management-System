import os
from flask import Flask, render_template, jsonify, request
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

from config import Config
from models import db, User, Notification
from utils.helpers import format_currency, format_datetime, format_date

# Import Blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.products import products_bp
from routes.categories import categories_bp
from routes.suppliers import suppliers_bp
from routes.customers import customers_bp
from routes.purchases import purchases_bp
from routes.sales import sales_bp
from routes.inventory import inventory_bp
from routes.reports import reports_bp
from routes.audit import audit_bp
from routes.notifications import notifications_bp
from routes.users import users_bp
from routes.api import api_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Extensions
    db.init_app(app)

    csrf = CSRFProtect(app)
    # Exempt REST API from CSRF
    csrf.exempt(api_bp)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please sign in to access this page.'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Jinja Filters
    app.jinja_env.filters['currency'] = format_currency
    app.jinja_env.filters['datetimeformat'] = format_datetime
    app.jinja_env.filters['dateformat'] = format_date

    # Context Processors (Global variables for templates)
    @app.context_processor
    def inject_global_data():
        try:
            unread_count = Notification.query.filter_by(is_read=False).count()
        except Exception:
            unread_count = 0
        return {
            'app_config': Config,
            'unread_notifications_count': unread_count
        }

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(suppliers_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(api_bp)

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Forbidden'}), 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Endpoint not found'}), 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500

    # Ensure DB tables exist
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)

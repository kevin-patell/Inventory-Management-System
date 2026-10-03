from flask import Blueprint, render_template, request
from flask_login import login_required
from models import AuditLog
from utils.decorators import admin_required
from config import Config

audit_bp = Blueprint('audit', __name__)

@audit_bp.route('/audit')
@login_required
@admin_required
def index():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', 'all')
    user_search = request.args.get('username', '').strip()

    query = AuditLog.query

    if action_filter != 'all':
        query = query.filter(AuditLog.action == action_filter)

    if user_search:
        query = query.filter(AuditLog.username.ilike(f"%{user_search}%"))

    pagination = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    logs = pagination.items

    # Fetch unique actions for filter dropdown
    unique_actions = [a[0] for a in AuditLog.query.with_entities(AuditLog.action).distinct().all()]

    return render_template(
        'audit/index.html',
        logs=logs,
        pagination=pagination,
        actions=unique_actions,
        selected_action=action_filter,
        user_search=user_search
    )

from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required
from models import db, Notification

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/notifications')
@login_required
def index():
    notifications = Notification.query.order_by(Notification.created_at.desc()).limit(50).all()
    return render_template('notifications/index.html', notifications=notifications)

@notifications_bp.route('/notifications/unread-count')
@login_required
def unread_count():
    count = Notification.query.filter_by(is_read=False).count()
    return jsonify({'unread_count': count})

@notifications_bp.route('/notifications/latest')
@login_required
def latest():
    notifs = Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
    unread_cnt = Notification.query.filter_by(is_read=False).count()
    return jsonify({
        'unread_count': unread_cnt,
        'notifications': [n.to_dict() for n in notifs]
    })

@notifications_bp.route('/notifications/<int:id>/read', methods=['POST'])
@login_required
def mark_read(id):
    notif = Notification.query.get_or_404(id)
    notif.is_read = True
    db.session.commit()
    if request.is_json:
        return jsonify({'success': True})
    return redirect(request.referrer or url_for('notifications.index'))

@notifications_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    Notification.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    if request.is_json:
        return jsonify({'success': True})
    flash('All notifications marked as read.', 'success')
    return redirect(request.referrer or url_for('notifications.index'))

@notifications_bp.route('/notifications/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    notif = Notification.query.get_or_404(id)
    db.session.delete(notif)
    db.session.commit()
    flash('Notification dismissed.', 'info')
    return redirect(url_for('notifications.index'))

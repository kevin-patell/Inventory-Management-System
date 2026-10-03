from flask import request
from flask_login import current_user
from models import db, AuditLog, Notification

def log_audit(action, target_type, target_id=None, details='', user=None, ip_address=None):
    """
    Centralized service to record an audit log event.
    """
    try:
        u_id = None
        u_name = 'System'
        
        if user:
            u_id = user.id
            u_name = user.username
        elif current_user and current_user.is_authenticated:
            u_id = current_user.id
            u_name = current_user.username

        if not ip_address:
            try:
                ip_address = request.remote_addr
            except RuntimeError:
                ip_address = '127.0.0.1'

        log_entry = AuditLog(
            user_id=u_id,
            username=u_name,
            action=action,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            details=details,
            ip_address=ip_address
        )
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    except Exception as e:
        db.session.rollback()
        print(f"Error logging audit: {e}")
        return None

def create_notification(title, message, type='system', link=None):
    """
    Centralized service to create in-app notifications.
    """
    try:
        notif = Notification(
            title=title,
            message=message,
            type=type,
            link=link
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception as e:
        db.session.rollback()
        print(f"Error creating notification: {e}")
        return None

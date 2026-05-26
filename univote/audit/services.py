"""
Audit Services — Log admin actions and verification attempts.
"""
from audit.models import AuditLog, VerificationLog
from django.contrib.auth.models import User


def log_action(actor: User, action: str, entity_type: str = '', entity_id: str = '',
               metadata: dict = None, ip_address: str = None, user_agent: str = ''):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )


def log_action_from_request(request, action: str, entity_type: str = '',
                            entity_id: str = '', metadata: dict = None):
    """Convenience: log from a Django request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')
    ua = request.META.get('HTTP_USER_AGENT', '')[:500]
    log_action(
        actor=request.user if request.user.is_authenticated else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id),
        metadata=metadata or {},
        ip_address=ip,
        user_agent=ua,
    )


def log_verification(election, student, attempted_id: str, attempted_email: str,
                     status: str, reason: str, ip_address: str, user_agent: str):
    VerificationLog.objects.create(
        election=election,
        student=student,
        attempted_student_id_number=attempted_id,
        attempted_email=attempted_email,
        status=status,
        reason=reason,
        ip_address=ip_address,
        user_agent=user_agent,
    )

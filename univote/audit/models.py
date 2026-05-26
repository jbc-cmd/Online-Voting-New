from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs'
    )
    action = models.CharField(max_length=200)
    entity_type = models.CharField(max_length=100, blank=True)
    entity_id = models.CharField(max_length=100, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        actor = self.actor.username if self.actor else 'Anonymous'
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {actor}: {self.action}"


class VerificationLog(models.Model):
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed_not_found', 'Failed - Student Not Found'),
        ('failed_ineligible', 'Failed - Not Eligible'),
        ('failed_already_voted', 'Failed - Already Voted'),
        ('failed_otp_invalid', 'Failed - OTP Invalid'),
        ('failed_otp_expired', 'Failed - OTP Expired'),
        ('failed_otp_exhausted', 'Failed - OTP Attempts Exhausted'),
        ('duplicate_attempt', 'Duplicate Vote Attempt'),
        ('election_closed', 'Failed - Election Closed'),
    ]

    election = models.ForeignKey(
        'elections.Election', on_delete=models.CASCADE, related_name='verification_logs',
        null=True, blank=True
    )
    student = models.ForeignKey(
        'students.Student', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='verification_logs'
    )
    attempted_student_id_number = models.CharField(max_length=50)
    attempted_email = models.EmailField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    reason = models.CharField(max_length=300, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.attempted_student_id_number} — {self.get_status_display()}"


class SystemEvaluationReport(models.Model):
    UPTIME_CHOICES = [
        ('operational', 'Operational'),
        ('degraded', 'Degraded'),
        ('down', 'Down'),
    ]

    election = models.ForeignKey(
        'elections.Election', on_delete=models.CASCADE, null=True, blank=True,
        related_name='evaluation_reports'
    )
    vote_count_accuracy = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    successful_vote_submission_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    failed_vote_attempt_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    duplicate_vote_prevention_count = models.PositiveIntegerField(default=0)
    otp_success_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    otp_failure_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    average_response_time = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True)
    uptime_status = models.CharField(max_length=20, choices=UPTIME_CHOICES, default='operational')
    usability_notes = models.TextField(blank=True)
    reliability_notes = models.TextField(blank=True)
    security_notes = models.TextField(blank=True)
    performance_notes = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-generated_at']

    def __str__(self):
        election_title = self.election.title if self.election else "System-Wide"
        return f"Evaluation Report: {election_title} ({self.generated_at:%Y-%m-%d})"

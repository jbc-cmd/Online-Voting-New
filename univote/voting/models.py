import hashlib
import secrets
from django.db import models
from django.utils import timezone


class OTPVerification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('expired', 'Expired'),
        ('exhausted', 'Exhausted'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='otp_verifications')
    election = models.ForeignKey('elections.Election', on_delete=models.CASCADE, related_name='otp_verifications')
    email = models.EmailField()
    otp_hash = models.CharField(max_length=64)  # SHA-256 hex
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.student} in {self.election} [{self.status}]"

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return self.status == 'pending' and not self.is_expired()

    @staticmethod
    def hash_otp(otp: str) -> str:
        return hashlib.sha256(otp.encode()).hexdigest()


class VoterParticipation(models.Model):
    election = models.ForeignKey(
        'elections.Election', on_delete=models.CASCADE, related_name='participations'
    )
    student = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, related_name='participations'
    )
    has_voted = models.BooleanField(default=False)
    voted_at = models.DateTimeField(null=True, blank=True)
    verification_method = models.CharField(max_length=50, default='otp_email')
    ballot_number = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        unique_together = [('election', 'student')]
        ordering = ['-voted_at']

    def __str__(self):
        status = "Voted" if self.has_voted else "Not Voted"
        return f"{self.student} in {self.election} [{status}]"


class Ballot(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('invalid', 'Invalid'),
    ]

    election = models.ForeignKey(
        'elections.Election', on_delete=models.CASCADE, related_name='ballots'
    )
    ballot_number = models.CharField(max_length=50, unique=True)
    anonymized_voter_hash = models.CharField(max_length=64)  # SHA-256 of student_id+election_id+salt
    submitted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"Ballot #{self.ballot_number} ({self.election.title})"


class Vote(models.Model):
    ballot = models.ForeignKey(Ballot, on_delete=models.CASCADE, related_name='votes')
    election = models.ForeignKey('elections.Election', on_delete=models.CASCADE, related_name='votes')
    position = models.ForeignKey('elections.Position', on_delete=models.CASCADE, related_name='votes')
    candidate = models.ForeignKey(
        'elections.Candidate', on_delete=models.CASCADE, null=True, blank=True, related_name='votes'
    )
    is_abstain = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['position__display_order']

    def __str__(self):
        if self.is_abstain:
            return f"Abstain on {self.position.title}"
        return f"Vote for {self.candidate.name} ({self.position.title})"

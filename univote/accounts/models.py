from django.db import models
from django.contrib.auth.models import User


class AdminProfile(models.Model):
    ROLE_CHOICES = [
        ('super_admin', 'Super Admin'),
        ('election_admin', 'Election Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='election_admin')
    department = models.ForeignKey(
        'students.Department', on_delete=models.SET_NULL, null=True, blank=True
    )
    is_super_admin = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        if self.role == 'super_admin':
            self.is_super_admin = True
        super().save(*args, **kwargs)

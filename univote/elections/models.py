from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Election(models.Model):
    ELECTION_TYPES = [
        ('usc', 'USC / University Student Council'),
        ('organization', 'Organization'),
        ('department', 'Department'),
        ('program', 'Program'),
        ('class', 'Class'),
    ]
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    RESULTS_VISIBILITY = [
        ('admin_only', 'Admin Only'),
        ('public_after_close', 'Public After Close'),
    ]

    title = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    election_type = models.CharField(max_length=30, choices=ELECTION_TYPES)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=False)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    results_visibility = models.CharField(
        max_length=30, choices=RESULTS_VISIBILITY, default='admin_only'
    )
    allow_abstain = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            n = 1
            while Election.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def voting_url(self):
        from django.conf import settings
        return f"{settings.SITE_URL}/vote/{self.slug}/"

    @property
    def total_eligible_voters(self):
        return self.participations.count()

    @property
    def total_votes_cast(self):
        return self.participations.filter(has_voted=True).count()

    @property
    def voter_turnout_percentage(self):
        total = self.total_eligible_voters
        if total == 0:
            return 0
        return round((self.total_votes_cast / total) * 100, 1)

    def is_voting_open(self):
        """Check if voting is currently open."""
        return self.is_active and self.status == 'active'


class ElectionEligibilityRule(models.Model):
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE, related_name='eligibility_rules'
    )
    department = models.ForeignKey(
        'students.Department', on_delete=models.CASCADE, null=True, blank=True
    )
    program = models.ForeignKey(
        'students.Program', on_delete=models.CASCADE, null=True, blank=True
    )
    class_group = models.ForeignKey(
        'students.ClassGroup', on_delete=models.CASCADE, null=True, blank=True
    )
    organization = models.ForeignKey(
        'students.Organization', on_delete=models.CASCADE, null=True, blank=True
    )
    year_level = models.CharField(max_length=10, blank=True)
    section = models.CharField(max_length=10, blank=True)

    def __str__(self):
        parts = []
        if self.department:
            parts.append(str(self.department))
        if self.program:
            parts.append(str(self.program))
        if self.year_level:
            parts.append(f"Year {self.year_level}")
        if self.section:
            parts.append(f"Section {self.section}")
        return f"Rule for {self.election.title}: " + (', '.join(parts) or 'All students')


class Position(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    max_choices = models.PositiveIntegerField(default=1)
    is_required = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'id']

    def __str__(self):
        return f"{self.title} ({self.election.title})"


class Candidate(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='candidates')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
    name = models.CharField(max_length=200)
    partylist = models.CharField(max_length=200, blank=True)
    photo = models.ImageField(upload_to='candidates/', null=True, blank=True)
    description = models.TextField(blank=True)
    platform = models.TextField(blank=True)
    department = models.ForeignKey(
        'students.Department', on_delete=models.SET_NULL, null=True, blank=True
    )
    program = models.ForeignKey(
        'students.Program', on_delete=models.SET_NULL, null=True, blank=True
    )
    class_group = models.ForeignKey(
        'students.ClassGroup', on_delete=models.SET_NULL, null=True, blank=True
    )
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['display_order', 'name']

    def __str__(self):
        return f"{self.name} — {self.position.title}"

    @property
    def vote_count(self):
        from voting.models import Vote
        return Vote.objects.filter(candidate=self, is_abstain=False).count()

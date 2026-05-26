from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Program(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ClassGroup(models.Model):
    YEAR_LEVEL_CHOICES = [
        ('1', '1st Year'),
        ('2', '2nd Year'),
        ('3', '3rd Year'),
        ('4', '4th Year'),
        ('5', '5th Year'),
    ]

    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='classes')
    year_level = models.CharField(max_length=10, choices=YEAR_LEVEL_CHOICES)
    section = models.CharField(max_length=10)
    name = models.CharField(max_length=100)  # e.g., "BSIT 2A"

    class Meta:
        ordering = ['name']
        unique_together = [('program', 'year_level', 'section')]

    def __str__(self):
        return self.name


class Organization(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Student(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated'),
    ]

    student_id_number = models.CharField(max_length=50, unique=True)
    official_school_email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='students'
    )
    program = models.ForeignKey(
        Program, on_delete=models.SET_NULL, null=True, blank=True, related_name='students'
    )
    year_level = models.CharField(max_length=10, blank=True)
    section = models.CharField(max_length=10, blank=True)
    class_group = models.ForeignKey(
        ClassGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name='students'
    )
    organizations = models.ManyToManyField(Organization, blank=True, related_name='students')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f"{self.last_name}, {self.first_name} ({self.student_id_number})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

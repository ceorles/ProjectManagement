from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models

student_id_validator = RegexValidator(
    regex=r'^[A-Za-z0-9-]{4,20}$',
    message='Student ID must be 4-20 letters, digits or dashes.',
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('An email address is required.')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """`python manage.py createsuperuser` creates a portal Admin."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields['role'] = User.Role.ADMIN
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    One account table for all three roles. The role decides what a person can
    do; student-only and librarian-only details are optional columns.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        LIBRARIAN = 'librarian', 'Librarian'
        STUDENT = 'student', 'Student'

    username = None
    email = models.EmailField('email address', unique=True)
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)

    # Student details
    student_id = models.CharField(
        max_length=20, unique=True, null=True, blank=True, validators=[student_id_validator]
    )
    program = models.CharField(max_length=120, blank=True)
    year_level = models.PositiveSmallIntegerField(null=True, blank=True)

    phone = models.CharField(max_length=30, blank=True)

    # Librarian permission granted by an Admin.
    can_manage_resources = models.BooleanField(
        default=False,
        help_text='Allows a librarian to add, edit and disable seats and study rooms.',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        ordering = ['last_name', 'first_name']
        indexes = [models.Index(fields=['role', 'is_active'])]

    def __str__(self):
        return f'{self.full_name} ({self.email})'

    def save(self, *args, **kwargs):
        self.email = (self.email or '').strip().lower()
        if not self.student_id:
            self.student_id = None  # keep the unique column NULL, never ''
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or self.email

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_librarian(self):
        return self.role == self.Role.LIBRARIAN

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_library_staff(self):
        return self.role in (self.Role.ADMIN, self.Role.LIBRARIAN)

    @property
    def can_manage_library_resources(self):
        return self.is_admin or (self.is_librarian and self.can_manage_resources)

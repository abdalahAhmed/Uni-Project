from django.contrib.auth.models import AbstractUser
from django.db import models

ROLE_CHOICES = (
    ('Doctor', 'Doctor'),
    ('Admin', 'Admin'),
)

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    # ✅ الحقول الجديدة
    full_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    # ✅ لقب العرض (دكتور / مهندس / محاضر)
    display_title = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.username

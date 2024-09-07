from __future__ import annotations
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from typing import Any

from apps.custom_storage import FirebaseStorage


class FirebaseUserManager(BaseUserManager):
    def create_user(self, uid: str, **extra_fields: Any) -> FirebaseUser:
        if not uid:
            raise ValueError("User must have a UID")
        
        user = self.model(uid=uid, **extra_fields)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, uid, **extra_fields) -> FirebaseUser:
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(uid, **extra_fields)
    
class FirebaseUser(AbstractBaseUser, PermissionsMixin):
    uid = models.CharField(max_length=150, unique=True, primary_key=True)

    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    provider = models.CharField(max_length=255, null=True, blank=True)    

    first_name = models.CharField(max_length=50, null=True, blank=True)
    last_name = models.CharField(max_length=60, null=True, blank=True)
    display_name = models.CharField(max_length=100, null=False, blank=False)
    img = models.ImageField(storage=FirebaseStorage(), null=True)

    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = FirebaseUserManager()

    USERNAME_FIELD = 'uid'
    REQUIRED_FIELDS = []

    def __str__(self) -> str:
        return self.display_name + ": " + self.uid

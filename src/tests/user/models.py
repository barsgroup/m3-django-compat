# coding: utf-8
from django.contrib.auth.models import AbstractBaseUser
from django.contrib.auth.models import UserManager
from django.db import models


class CustomUser(AbstractBaseUser):

    USERNAME_FIELD = 'username'

    username = models.CharField(
        u'Логин',
        max_length=100,
        unique=True,
    )
    email = models.EmailField(
        blank=True,
    )
    date_joined = models.DateTimeField(
        u'Дата создания',
        auto_now_add=True,
    )
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

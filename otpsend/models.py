from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class CustomUser(AbstractUser):
    # username_validator = UnicodeUsernameValidator()
     
    username = models.CharField(max_length=80,unique=True)
    email = models.EmailField(unique=True)
    otp = models.IntegerField(null=True,blank=True)
    activation_key = models.CharField(max_length=150,blank=True,null=True)
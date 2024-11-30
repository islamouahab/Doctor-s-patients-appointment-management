from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class custom_user(AbstractUser):
    choices = (('doctor','Doctor'),('labo','Laboratory'))
    type = models.CharField(max_length=25,choices=choices)
    speciality = models.CharField(max_length=25)
    phone_num = models.CharField(max_length=15)
    location = models.CharField(max_length=100)
    firebase_id = models.CharField(max_length=150)
    profile_pic = models.ImageField(upload_to='profile_pics/')
class tests(models.Model):
    name = models.CharField(max_length=50)
    lab_Ref = models.ForeignKey(custom_user,on_delete=models.CASCADE)
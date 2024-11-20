from django.db import models
from django.utils.timezone import now
from datetime import date

class Course(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ownerid = models.CharField(max_length=255)
    alias = models.CharField(max_length=100, default='p')
    datecreated = models.DateTimeField(default=now)
    # startdate = models.DateField(default=date.today)
    googleclassroomid = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

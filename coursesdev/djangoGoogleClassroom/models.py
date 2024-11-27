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
    startdate = models.DateField(default=date.today)
    googleclassroomid = models.CharField(max_length=255, unique=True)
    
    
    
    
    def get_google_classroom_url(self):
        if self.googleclassroomid:
            return f"https://classroom.google.com/c/{self.googleclassroomid}"
        return "#"

    def __str__(self):
        return self.name


class CourseImage(models.Model):
    course = models.OneToOneField(Course, on_delete=models.CASCADE, primary_key=True)
    imagepath = models.ImageField(default='fallback.jpg', blank=True)  

    def __str__(self):
        return f"Image for {self.course.name}"
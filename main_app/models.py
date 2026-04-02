from django.db import models

class University(models.Model):
    name = models.CharField(max_length=255)
    country = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Professor(models.Model):
    name = models.CharField(max_length=255)
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)
    research_area = models.TextField()
    email = models.EmailField()
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name
is_featured = models.BooleanField(default=False)
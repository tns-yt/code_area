from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class problems(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=500)

    def __str__(self):
        return str(self.name)

class testcase(models.Model):
    input = models.TextField()
    output = models.TextField()
    prob = models.ForeignKey(problems,on_delete=models.CASCADE)

    def __str__(self):
        return str( "TC:" + str(self.id) + " for " +  str(self.prob))


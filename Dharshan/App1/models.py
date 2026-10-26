from django.db import models
from django.core.validators import RegexValidator

# Create your models here.
class Registration(models.Model):
    Username=models.CharField(max_length=50)
    password=models.CharField(max_length=100,validators=[
        RegexValidator(
            regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$',
            message="Password must contain at least 8 characters, "
                        "one uppercase, one lowercase, one number "
                        "and one special character."
        )
    ])
    email=models.EmailField()
    mobileNumber=models.CharField(max_length=10,validators=[
        RegexValidator(
            regex=r'^[6-9]\d{9}$',
            message="Enter a valid 10 digit Mobile Number."
        )
    ])

    def __str__(self):
        return self.Username

class EmailOTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
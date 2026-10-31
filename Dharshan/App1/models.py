from django.db import models
from django.core.validators import RegexValidator

# =====================================

# REGISTRATION MODEL

# =====================================

class Registration(models.Model):
    Username = models.CharField(max_length=50)
    password = models.CharField(
        max_length=100,
        validators=[
            RegexValidator(
                regex=r'^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$',
                message="Password must contain at least 8 characters, "
                    "one uppercase, one lowercase, one number "
                    "and one special character.")])
    

    email = models.EmailField()

    mobileNumber = models.CharField(
        max_length=10,
        validators=[
            RegexValidator(
                regex=r'^[6-9]\d{9}$',
                message="Enter a valid 10 digit Mobile Number.")])
    

    def __str__(self):
        return self.Username


# =====================================

# FESTIVAL MODEL

# =====================================

class Festival(models.Model):
    CATEGORY_CHOICES = [
    ("Hindu", "Hindu"),
    ("Muslim", "Muslim"),
    ("Christian", "Christian"),
    ("Sikh", "Sikh"),
    ("Buddhist", "Buddhist"),
    ("Jain", "Jain"),
    ("Other", "Other"),
    ]


    name = models.CharField(max_length=150)

    festival_date = models.DateField()

    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="Hindu")
    

    location = models.CharField(
        max_length=100,
        default="Telangana"
    )

    source = models.URLField(
        max_length=500,
        blank=True,
        null=True
    )

    is_verified = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)


class Meta:

    ordering = ["festival_date"]

    constraints = [
        models.UniqueConstraint(
            fields=["name", "festival_date", "location"],
            name="unique_festival_date_location"
        )
    ]

def __str__(self):
    return f"{self.name} - {self.festival_date}"

class FestivalSync(models.Model):

    year = models.PositiveIntegerField(unique=True)

    completed = models.BooleanField(default=False)

    imported_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"Festival Sync - {self.year}"

from django.contrib import admin
from .models import Registration, Festival


# Registration Admin
@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):

    list_display = ("Username", "email", "mobileNumber")
    search_fields = ("Username", "email")


# Festival Admin
@admin.register(Festival)
class FestivalAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "festival_date",
        "category",
        "location",
        "is_verified"
    )

    list_filter = (
        "category",
        "location",
        "is_verified"
    )

    search_fields = ("name",)

    ordering = ("festival_date",)
from django.urls import path
from . import views


urlpatterns = [
    path("", views.login_view, name="login"),
    path("register/", views.Register, name="Register"),
    path("home/", views.home_view, name="home"),
    path("about/", views.about_view, name="about"),
    path("Temples/", views.Temples_view, name="Temples"),
    path("logout/",views.log_out,name="logout"),
    path("temple-search/",views.temple_search,name="temple_search"),
    path("temple-details/",views.temple_details,name="temple_details"),
    path("calendars/",views.calendar_languages,name="calendar_languages"),
    path("calendar/<str:calendar_type>/",views.calendar_detail,name="calendar_detail"),
    path("temple-events/<str:temple_type>/",views.temple_events_view,name="temple_events"),
]
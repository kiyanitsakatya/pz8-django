from django.urls import path
from . import views

urlpatterns = [
    path("users/",    views.dashboard_users,    name="dashboard_users"),
    path("courses/",  views.dashboard_courses,  name="dashboard_courses"),
    path("activity/", views.dashboard_activity, name="dashboard_activity"),
]
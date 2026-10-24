from django.urls import path
from .views import analyze_crop, health_check

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("analyze/", analyze_crop, name="analyze-crop"),
]

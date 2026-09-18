from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path('', include('solver.urls')),  # Ensure solver.urls is linked to the root path
]

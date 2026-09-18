from django.urls import path
from . import views

urlpatterns = [
    # If your function in views.py is named 'home':
    path('', views.home, name='home'),
]
from django.urls import path
from .views import short_redirect

urlpatterns = [
    path('<slug:code>', short_redirect, name='short-redirect'),
]

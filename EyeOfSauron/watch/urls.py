from django.urls import include, path
from django.contrib import admin
# from rest_framework import routers
from watch import views

urlpatterns = [
    path('', views.Update)
]
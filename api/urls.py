from django.urls import path

from .views import *


urlpatterns = [
    path("category/", CategoryListView.as_view()),
    path("banner/", BannerListView.as_view()),
]
from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register("products", ProductViewSet, basename="products")


urlpatterns = [
    path("category/", CategoryListView.as_view()),
    path("banner/", BannerListView.as_view()),
    path("", include(router.urls)),
]
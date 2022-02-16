from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter

from .views import *

router = DefaultRouter()
router.register("products", ProductViewSet, basename="products")
router.register("categories", CategoryViewSet, basename="categories")
router.register("colors", ColorsViewSet, basename="colors")
router.register("size", SizeViewSet, basename="size")


urlpatterns = [
    path("banners/", BannerListView.as_view()),
    path("", include(router.urls)),
]
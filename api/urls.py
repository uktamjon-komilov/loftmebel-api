from django.urls import path
from django.urls.conf import include
from rest_framework.routers import DefaultRouter

from .views import (
    ProductViewSet,
    CategoryViewSet,
    ColorsViewSet,
    SizeViewSet,
    EmailCheckViewSet,
    EmailOTPCheckViewSet,
    UserCreateViewSet,
    UserLoginViewSet,
    FeedbackViewSet,
    UserViewSet,
    BannerListView,
    StripeAPIView
)

router = DefaultRouter()
router.register("products", ProductViewSet, basename="products")
router.register("categories", CategoryViewSet, basename="categories")
router.register("colors", ColorsViewSet, basename="colors")
router.register("size", SizeViewSet, basename="size")
router.register("check-email", EmailCheckViewSet, basename="check-email")
router.register("check-otp", EmailOTPCheckViewSet, basename="check-email")
router.register("sign-up", UserCreateViewSet, basename="sign-up")
router.register("login", UserLoginViewSet, basename="login")
router.register("feedback", FeedbackViewSet, basename="feedback")
router.register("user", UserViewSet, basename="user")


urlpatterns = [
    path("banners/", BannerListView.as_view()),
    path("payments/stripe/", StripeAPIView.as_view()),
    path("", include(router.urls)),
]
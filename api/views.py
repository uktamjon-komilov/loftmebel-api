from django.conf import settings
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework import status
from rest_framework.viewsets import mixins, GenericViewSet
from django.db.models import Avg, Q
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from datetime import datetime, timedelta

from api.models import *
from api.pagination import StandardResultsSetPagination
from api.serializers import *
from api.filters import *
from api.services import check_black_list, create_wrong_try
from api.utils import get_client_ip


class CategoryViewSet(ViewSet):
    queryset = Category.objects.filter(parent__isnull=True)
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return self.queryset.all()

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=True, methods=["get"], url_path="products")
    def products(self, request, pk=None):
        try:
            id = int(pk)
            category = Category.objects.filter(id=id)
        except:
            category = Category.objects.filter(slug=pk)
        if category.exists():
            category = category.first()
            products = Product.objects.filter(category=category)
            products = ProductFilters.apply_filters(products, self.request)
            serializer = ProductDetailSerializer(products, many=True)
            return Response(serializer.data, status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)
    

    @action(detail=True, methods=["get"], url_path="prices")
    def prices(self, request, pk=None):
        try:
            id = int(pk)
            category = Category.objects.filter(id=id)
        except:
            category = Category.objects.filter(slug=pk)
        if category.exists():
            category = category.first()
            products = Product.objects.filter(category=category)
            products = ProductFilters.apply_filters(products, self.request)
            result = {
                "min": 0.0,
                "max": 0.0
            }
            if products.exists():
                result["max"] = products.order_by("-price").first().price
                result["min"] = products.order_by("price").first().price
                if result["max"] == result["min"]:
                    result["min"] = 0.0
            return Response(result, status.HTTP_200_OK)
        return Response(status=status.HTTP_404_NOT_FOUND)


class BannerListView(ListAPIView):
    pagination_class = None
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer


class ProductViewSet(ModelViewSet):
    serializer_class = ProductSerializer
    detail_serializer_class = ProductDetailSerializer
    pagination_class = StandardResultsSetPagination
    queryset = Product.objects.all()

    def get_queryset(self):
        queryset = self.queryset.annotate(
            average_rating=Avg("reviews__rating")
        ).order_by("-average_rating")
        return ProductFilters.apply_filters(queryset, self.request)

    def retrieve(self, request, pk=None):
        try:
            pk = int(pk)
            product = Product.objects.filter(id=pk)
        except:
            product = Product.objects.filter(slug=pk)

        if product.exists():
            product = product.first()
            serializer = self.detail_serializer_class(product)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)


    @action(detail=False, methods=["get"], url_path="top")
    def top_products(self, request):
        products = self.get_queryset()[:20]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=False, methods=["get"], url_path="discounted")
    def discounted(self, request):
        now = datetime.now()
        today = "{}-{}-{}".format(now.year, now.month, now.day)
        discounts = Discount.objects.filter(is_active=True, expires_in__gt=today)

        product_ids = []
        for discount in discounts:
            product_ids.append(discount.product.id)
        
        products = self.get_queryset().filter(id__in=product_ids)

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=True, methods=["get"], url_path="recommended")
    def recommended(self, request, pk=None):
        try:
            product = Product.objects.get(id=pk)
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
        products = Product.objects.filter(category=product.category).exclude(id=pk)[:4]
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=["get"], url_path="latest")
    def latest(self, request):
        products = Product.objects.all().order_by("-created_at")[:4]
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ColorsViewSet(
        mixins.ListModelMixin,
        GenericViewSet
    ):
    queryset = Color.objects.all()
    serializer_class = ColorSerializer

    def get_queryset(self):
        return ColorsFilter.apply_filters(self.queryset, self.request)


class SizeViewSet(
        mixins.ListModelMixin,
        GenericViewSet
    ):
    queryset = Size.objects.all()
    serializer_class = SizeSerializer

    def get_queryset(self):
        return SizeFilter.apply_filters(self.queryset, self.request)


class EmailCheckViewSet(
        mixins.CreateModelMixin,
        GenericViewSet
    ):
    serializer_class = EmailCheckSerializer
    authentication_classes = []
    permission_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response({
                "status": False,
                "detail": "NOT_VALID_EMAIL"
            })
        
        email = serializer.validated_data["email"].strip()

        users = User.objects.filter(email=email)
        if users.exists():
            return Response({
                "status": False,
                "detail": "USER_EXISTS"
            })
        
        otp = OTP(email=email)
        otp.save()
        self.send_otp_code(otp)
        
        return Response({
            "status": True,
            "data": {
                "token": otp.token
            }
        })
    

    def send_otp_code(self, otp):
        send_mail(
            "OTP code",
            otp.code,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[otp.email]
        )


class EmailOTPCheckViewSet(
        mixins.CreateModelMixin,
        GenericViewSet
    ):
    serializer_class = EmailOTPCheckSerializer
    authentication_classes = []
    permission_classes = []

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "detail": "BAD_REQUEST"
            })
        
        data = serializer.validated_data

        otps = OTP.objects.filter(**data)
        if not otps.exists():
            return Response({
                "status": False,
                "detail": "WRONG_CODE"
            })

        otps = otps.filter(
            is_activated=False,
            created_at__gte=(datetime.now() - timedelta(minutes=5))
        )

        if not otps.exists():
            return Response({
                "status": False,
                "detail": "EXPIRED"
            })
    
        otp = otps.first()
        otp.is_activated = True
        otp.save()

        return Response({
            "status": True,
            "detail": "SUCCESS"
        })


class UserCreateViewSet(
        mixins.CreateModelMixin,
        GenericViewSet
    ):
    serializer_class = UserCreateSerializer
    user_serializer_class = UserSerializer
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(request_body=UserCreateSerializer, responses={201: UserSerializer})
    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "detail": f"BAD_REQUEST ({serializer.errors})"
            })
        
        data = serializer.validated_data

        token = data.pop("token", "")
        otps = OTP.objects.filter(
            token=token,
            is_activated=True,
            created_at__gte=(datetime.now() - timedelta(minutes=5))
        )
        if not otps.exists():
            return Response({
                "status": False,
                "detail": "TIMEOUT"
            })
        
        otp = otps.first()
        user = User(email=otp.email, **data)
        try:
            password = data.pop("password", "")
            user.save()
            user.set_password(password)
            user.save()
        except Exception as e:
            return Response({
                "status": False,
                "detail": "DATABASE_ERROR"
            })
        
        user_serializer = self.user_serializer_class(user)
        return Response({
            "status": True,
            "data": {**user_serializer.data}
        })


class UserLoginViewSet(
        mixins.CreateModelMixin,
        GenericViewSet
    ):
    serializer_class = UserLoginResponseSerializer
    response_serializer_class = UserLoginSerializer
    authentication_classes = []
    permission_classes = []

    @swagger_auto_schema(request_body=UserLoginSerializer)
    def create(self, request, *args, **kwargs):
        if check_black_list(request):
            return Response({
                "status": False,
                "detail": "TRY_IN_FIVE_MINUTES"
            })
        
        serializer = self.response_serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "detail": "BAD_REQUEST"
            })
        
        data = serializer.validated_data

        username = data["username"].strip()
        password = data["password"].strip()

        users = User.objects.filter(
            Q(email=username) |
            Q(phone=username)
        )

        if not users.exists():
            return Response({
                "status": False,
                "detail": "USER_NOT_EXISTS"
            })
        
        user = users.first()

        if not user.check_password(password):
            create_wrong_try(request, data)
            return Response({
                "status": False,
                "detail": "WRONG_PASSWORD"
            })
        
        refresh = RefreshToken.for_user(user)

        return Response({
            "status": True,
            "data": {
                "access": str(refresh.access_token),
                "refresh": str(refresh)
            }
        })
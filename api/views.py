from django.conf import settings
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet, GenericViewSet, mixins
from rest_framework import status
from django.db.models import Avg, Q
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from datetime import datetime, timedelta
import stripe


from .models import (
    Feedback,
    Category,
    Banner,
    Size,
    Color,
    Product,
    User,
    Discount,
    OTP
)

from .pagination import StandardResultsSetPagination
from .serializers import (
    CategorySerializer,
    BannerSerializer,
    SizeSerializer,
    ColorSerializer,
    ProductSerializer,
    ProductDetailSerializer,
    EmailCheckSerializer,
    EmailOTPCheckSerializer,
    UserCreateSerializer,
    UserLoginSerializer,
    UserLoginResponseSerializer,
    StripeGetLinkPostSerializer,
    FeedbackSerializer,
    UserSerializer
)
from .filters import (
    ProductFilters,
    SizeFilter,
    ColorsFilter
)
from .services import check_black_list, create_wrong_try


stripe.api_key = """
sk_test_51L7h4wJOQHe4ItwoFY51RwjQ0fDBBZNIxOr1KCbbMDpsp0Cf4QQVUMHtZ3yaJuX1p4ak5cwaWGDrdhLzkyLKdRTj00bfmEiIYJ
""".strip()


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
            id = int(str(pk))
            category = Category.objects.filter(id=id)
        except Exception:
            category = Category.objects.filter(slug=pk)
        if category.exists():
            category = category.first()
            products = Product.objects.filter(category=category)
            products = ProductFilters.apply_filters(products, self.request)

            paginator = StandardResultsSetPagination()
            page = paginator.paginate_queryset(products, request)
            if page is not None:
                serializer = ProductDetailSerializer(page, many=True)
                return paginator.get_paginated_response(serializer.data)

            serializer = ProductDetailSerializer(products, many=True)
            return Response(serializer.data, status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["get"], url_path="prices")
    def prices(self, request, pk=None):
        try:
            id = int(str(pk))
            category = Category.objects.filter(id=id)
        except Exception:
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
            pk = int(str(pk))
            product = Product.objects.filter(id=pk)
        except Exception:
            product = Product.objects.filter(slug=pk)

        if product.exists():
            product = product.first()
            serializer = self.detail_serializer_class(product)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"], url_path="top")
    def top_products(self, request):
        products = self.get_queryset()[:20]

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=False, methods=["get"], url_path="discounted")
    def discounted(self, request):
        now = datetime.now()
        today = "{}-{}-{}".format(now.year, now.month, now.day)
        discounts = Discount.objects.filter(is_active=True, expires_in__gt=today)

        product_ids = []
        for discount in discounts:
            product_ids.append(discount.product.id) # type: ignore
        
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
        except Exception:
            return Response(status=status.HTTP_404_NOT_FOUND)
        products = Product.objects.filter(category=product.category).exclude(id=pk)[:4]

        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

    @action(detail=False, methods=["get"], url_path="latest")
    def latest(self, request):
        products = Product.objects.all().order_by("-created_at")[:4]
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(products, many=True)
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
        serializer = self.get_serializer(data=request.data)
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
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "detail": "BAD_REQUEST"
            })

        otps = OTP.objects.filter(**serializer.validated_data)
        if not otps.exists():
            return Response({
                "status": False,
                "detail": "WRONG_CODE"
            })

        otp = otps.filter(
            is_activated=False,
            created_at__gte=(datetime.now() - timedelta(minutes=5))
        ).first()

        if otp is None:
            return Response({
                "status": False,
                "detail": "EXPIRED"
            })

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

    @swagger_auto_schema(
        request_body=UserCreateSerializer,
        responses={201: UserSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "detail": f"BAD_REQUEST ({serializer.errors})"
            })
        
        data = {**serializer.validated_data}

        token = data.pop("token", "")
        otp = OTP.objects.filter(
            token=token,
            is_activated=True,
            created_at__gte=(datetime.now() - timedelta(minutes=5))
        ).first()

        if otp is None:
            return Response({
                "status": False,
                "detail": "TIMEOUT"
            })

        user = User(email=otp.email, **data)
        try:
            password = data.pop("password", "")
            user.save()
            user.set_password(password)
            user.save()
        except Exception:
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
        
        data: dict = (
            serializer.validated_data if isinstance(serializer.validated_data, dict)
            else {}
        )

        username = data.get("username", "").strip()
        password = data.get("password", "").strip()

        user = User.objects.filter(
            Q(email=username) |
            Q(phone__icontains=username)
        ).first()

        if user is None:
            return Response({
                "status": False,
                "detail": "USER_NOT_EXISTS"
            })

        if user.check_password(password) is False:
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


class StripeAPIView(APIView):
    serialzer_class = StripeGetLinkPostSerializer

    def post(self, request):
        serializer = self.serialzer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        data: dict = (
            serializer.validated_data if isinstance(serializer.validated_data, dict)
            else {}
        )

        session = stripe.checkout.Session.create(
            line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "T-shirt",
                    },
                    "unit_amount": 2000,
                },
                "quantity": 1,
            }
            ],
            mode="payment",
            payment_method_types=['card'],
            success_url=data["success_url"],
            cancel_url=data["cancel_url"],
        )

        return Response({"checkout_url": session.url})


class FeedbackViewSet(mixins.CreateModelMixin, GenericViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    authentication_classes = []
    permission_classes = []


class UserViewSet(mixins.CreateModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @action(detail=False, methods=["get"], url_path="me")
    def get_my_data(self, request):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        
        serializer = self.get_serializer(request.user)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
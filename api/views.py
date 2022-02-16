from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet
from rest_framework import status
from rest_framework.viewsets import mixins, GenericViewSet
from django.db.models import Avg
from api.filters import *

from api.models import *
from api.pagination import StandardResultsSetPagination
from api.serializers import *


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
        now = timezone.now()
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
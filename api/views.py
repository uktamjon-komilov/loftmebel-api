from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework import status
from django.db.models import Avg

from api.models import *
from api.serializers import *


class CategoryListView(ListAPIView):
    queryset = Category.objects.filter(parent__isnull=True)
    serializer_class = CategorySerializer


class BannerListView(ListAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer


class ProductViewSet(ViewSet):
    @action(detail=False, methods=["get"], url_path="top")
    def top_products(self, request):
        products = Product.objects.annotate(average_rating=Avg("reviews__rating")).order_by("-average_rating")[:20]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
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
    serializer_class = ProductSerializer
    detail_serializer_class = ProductDetailSerializer

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
        products = Product.objects.annotate(average_rating=Avg("reviews__rating")).order_by("-average_rating")[:20]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
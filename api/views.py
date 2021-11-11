from rest_framework.generics import ListAPIView

from api.models import *
from api.serializers import *


class CategoryListView(ListAPIView):
    queryset = Category.objects.filter(parent__isnull=True)
    serializer_class = CategorySerializer


class BannerListView(ListAPIView):
    queryset = Banner.objects.all()
    serializer_class = BannerSerializer
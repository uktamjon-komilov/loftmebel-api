from rest_framework import serializers

from api.models import *


class CategorySimpleSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Category
        fields = ["id", "title", "icon", "slug"]



class CategorySerializer(serializers.ModelSerializer):
    children = CategorySimpleSerializer(many=True)

    class Meta:
        model = Category
        fields = ["id", "title", "icon", "slug", "children"]


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = "__all__"
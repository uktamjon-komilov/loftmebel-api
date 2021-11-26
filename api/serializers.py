from rest_framework import serializers
from django.utils import timezone
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


class SizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Size
        fields = "__all__"


class ProductSerializer(serializers.ModelSerializer):
    size = SizeSerializer(many=True)
    category = CategorySimpleSerializer(many=False)
    discount = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ["id", "title", "photo", "category", "price", "discounted_price", "size", "discount"]
    
    def get_discount_obj(self, obj):
        now = timezone.now()
        today = "{}-{}-{}".format(now.year, now.month, now.day)
        discount = obj.discounts.filter(product=obj, expires_in__gt=today, is_active=True)
        if discount.exists():
            discount = discount.first()
            return discount
        return None

    def get_discount(self, obj):
        discount = self.get_discount_obj(obj)
        if discount:
            return discount.discount
        return None
    

    def get_discounted_price(self, obj):
        discount = self.get_discount_obj(obj)
        if discount:
            return obj.price * (100 - discount.discount) / 100
        return None
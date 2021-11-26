from itertools import product
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from mptt.models import MPTTModel, TreeForeignKey

from .managers import UserManager

class User(AbstractBaseUser, PermissionsMixin):
    phone = models.CharField(max_length=16, unique=True)
    fullname = models.CharField(max_length=255, null=True, blank=True)
    photo = models.FileField(upload_to="users/", null=True, blank=True)

    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True)

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.fullname or self.phone



class Category(MPTTModel):
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True, blank=True, related_name="children")
    icon = models.FileField(upload_to="icons/", null=True, blank=True)
    title = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)

    def __str__(self):
        return self.title


class Banner(models.Model):
    photo = models.FileField(upload_to="banners/")
    heading = models.CharField(max_length=255, null=True, blank=True)
    subheading = models.CharField(max_length=255, null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    button = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.heading or self.subheading


class Color(models.Model):
    title = models.CharField(max_length=255)
    hex_code = models.CharField(max_length=8)

    def __str__(self):
        return self.title


class Size(models.Model):
    height = models.FloatField()
    width = models.FloatField()
    length = models.FloatField()

    def __str__(self):
        return "{}sm x {}sm x {}sm".format(self.height, self.width, self.length)


class Product(models.Model):
    title = models.CharField(max_length=255)
    photo = models.FileField(upload_to="images/")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.FloatField()
    color = models.ManyToManyField(Color)
    size = models.ManyToManyField(Size)
    description = models.TextField()


    def __str__(self):
        return self.title


class Discount(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="discounts")
    discount = models.FloatField(default=0.0)
    expires_in = models.DateField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        discount = Discount.objects.filter(product=self.product, is_active=True, expires_in__gt=self.expires_in)
        if discount.exists():
            for dis in discount:
                dis.is_active = False
                dis.save()
        return super(Discount, self).save(*args, **kwargs)



class Photo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="photos")
    photo = models.FileField(upload_to="images/")

    def __str__(self):
        return "{}'s photo".format(self.product.title)


class Characteristic(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __str__(self):
        return "{}'s {} - {}".format(self.product.title, self.key, self.value)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rating = models.FloatField()
    text = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{}'s review: {}".format(self.user.fullname or self.user.phone, self.rating)


class Wishlist(models.Model):
    ip = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return "{} liked {}".format(self.ip or self.user.fullname or self.user.phone, self.product.title)
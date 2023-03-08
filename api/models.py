from random import randint
from datetime import datetime
from hashlib import md5

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from django.template.defaultfilters import slugify
from mptt.models import MPTTModel, TreeForeignKey

from .utils import generate_random_number
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    GENDERS = [
        ("male", "Male"),
        ("female", "Female")
    ]
    email = models.EmailField(max_length=125, unique=True)
    phone = models.CharField(max_length=20)
    fullname = models.CharField(max_length=255, null=True, blank=True)
    photo = models.FileField(upload_to="users/", null=True, blank=True)
    gender = models.CharField(max_length=15, choices=GENDERS, default="male")

    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.fullname or self.email


class WrongRty(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    user_agent = models.TextField()
    ip = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} | {}".format(self.ip, self.username)


class BlackListAgent(models.Model):
    user_agent = models.TextField()
    ip = models.CharField(max_length=50)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "{} | {}".format(self.user_agent, self.ip)


class OTP(models.Model):
    email = models.CharField(max_length=125)
    code = models.CharField(max_length=6)
    token = models.CharField(max_length=50, null=True, blank=True)
    is_activated = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super(OTP, self).save(*args, **kwargs)
        if not self.token:
            now = datetime.now()
            plain = "{}{}".format(self.id, now.year) # type: ignore
            self.token = md5(plain.encode("utf-8")).hexdigest()
        if not self.code:
            self.code = generate_random_number()
        super(OTP, self).save(*args, **kwargs)

    def __str__(self):
        return "<OTP token={} code={}>".format(self.token, self.code)


class Category(MPTTModel):
    parent = TreeForeignKey("self", on_delete=models.CASCADE, null=True,
                            blank=True, related_name="children")
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
    category = models.ForeignKey(Category, on_delete=models.SET_NULL,
                                 null=True, blank=True)
    price = models.FloatField()
    color = models.ManyToManyField(Color, related_name="products")
    size = models.ManyToManyField(Size, related_name="products")
    description = models.TextField()
    slug = models.CharField(max_length=255)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        slug = slugify(self.title)
        while Product.objects.filter(slug=slug).exists():
            slug += str(timezone.now().year % randint(1, 9))
        self.slug = slug
        return super(Product, self).save(*args, **kwargs)


class Discount(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name="discounts")
    discount = models.FloatField(default=0.0)
    expires_in = models.DateField()
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        discount = Discount.objects.filter(product=self.product, is_active=True,
                                           expires_in__gt=self.expires_in)
        if discount.exists():
            for dis in discount:
                dis.is_active = False
                dis.save()
        return super(Discount, self).save(*args, **kwargs)



class Photo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name="photos")
    photo = models.FileField(upload_to="images/")

    def __str__(self):
        return "{}'s photo".format(self.product.title)


class Characteristic(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name="characteristics")
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

    def __str__(self):
        return "{}'s {} - {}".format(self.product.title, self.key, self.value)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE,
                                related_name="reviews")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    rating = models.FloatField()
    text = models.TextField(null=True, blank=True)

    def __str__(self):
        if self.user is None:
            return "unkwon user's review"

        return "{}'s review: {}".format(self.user.fullname or self.user.phone,
                                        self.rating)


class Wishlist(models.Model):
    ip = models.CharField(max_length=50, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        if self.user is None:
            return "unkwon user's wishlist"

        if self.product is None:
            return "wishlist without a product"

        return "{} liked {}".format(self.ip or self.user.fullname or self.user.phone,
                                    self.product.title)


class Order(models.Model):
    pass


class OrderProduct(models.Model):
    pass


class Feedback(models.Model):
    fullname = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    file = models.FileField()

    def __str__(self):
        return "{} {} {}".format(self.fullname, self.email, self.message).strip()
from django.contrib import admin
from django import forms
from mptt.admin import MPTTModelAdmin


from .models import (
    Category,
    Banner,
    Size,
    Color,
    Photo,
    Characteristic,
    Product,
    User,
    Review,
    Wishlist,
    Discount,
    OTP
)


class CategoryAdmin(MPTTModelAdmin):
    mptt_level_indent = 50

    def get_prepopulated_fields(self, request, obj=None):
        return {"slug": ("title",)}


class ColorAdminForm(forms.ModelForm):
    hex_code = forms.CharField(widget=forms.TextInput(attrs={"type": "color"}))

    class Meta:
        model = Color
        fields = "__all__"


class ColorAdmin(admin.ModelAdmin):
    form = ColorAdminForm


class CharacteristicAdmin(admin.StackedInline):
    fields = ["product", "key", "value"]
    model = Characteristic


class PhotoAdmin(admin.StackedInline):
    fields = ["product", "photo"]
    model = Photo


class ProductAdmin(admin.ModelAdmin):
    inlines = [CharacteristicAdmin, PhotoAdmin]

    def get_prepopulated_fields(self, request, obj=None):
        return {"slug": ("title",)}


class OTPAdmin(admin.ModelAdmin):
    list_display = ["id", "email", "code", "token", "created_at"]


admin.site.register(Product, ProductAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Color, ColorAdmin)
admin.site.register(Size)
admin.site.register(Review)
admin.site.register(Wishlist)
admin.site.register(Banner)
admin.site.register(Discount)
admin.site.register(User)
admin.site.register(OTP, OTPAdmin)
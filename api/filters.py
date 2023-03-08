from django.db.models import Q

from api.models import Category


class ProductFilters:
    @staticmethod
    def apply_filters(queryset, request):
        data = request.query_params

        term = data.get("term", None)
        if term:
            queryset = queryset.filter(
                Q(title__icontains=term)
                |
                Q(description__icontains=term)
            )
        
        min_price = data.get("min_price", None)
        if min_price:
            min_threshold = float(min_price)
            queryset = queryset.filter(price__gte=min_threshold)

        max_price = data.get("max_price", None)
        if max_price:
            max_threshold = float(max_price)
            queryset = queryset.filter(price__lte=max_threshold)
        
        colors_string = data.get("colors", None)
        if colors_string:
            colors_string = colors_string.replace("[", "").replace("]", "")
            color_ids = colors_string.split(",")
            print(color_ids)
            queryset = queryset.filter(color__id__in=color_ids)
        
        size_string = data.get("size", None)
        if size_string:
            size_string = size_string.replace("[", "").replace("]", "")
            size_ids = size_string.split(",")
            print(size_ids)
            queryset = queryset.filter(size__id__in=size_ids)
        
        return queryset.distinct()


class ColorsFilter:
    @staticmethod
    def apply_filters(queryset, request):
        data = request.query_params

        category_id = data.get("category", None)
        if category_id:
            try:
                category_id = int(category_id)
                category = Category.objects.filter(id=category_id) # type: ignore 
            except Exception:
                category = Category.objects.filter(slug=category_id) # type: ignore 
            if category.exists():
                category = category.first()
                queryset = queryset.filter(products__category=category)

        return queryset.distinct()


class SizeFilter:
    @staticmethod
    def apply_filters(queryset, request):
        data = request.query_params

        category_id = data.get("category", None)
        if category_id:
            try:
                category_id = int(category_id)
                category = Category.objects.filter(id=category_id)
            except Exception:
                category = Category.objects.filter(slug=category_id)
            if category.exists():
                category = category.first()
                queryset = queryset.filter(products__category=category)

        return queryset.distinct()
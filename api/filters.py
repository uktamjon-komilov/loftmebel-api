from django.db.models import Q

from api.models import Color


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
            queryset = queryset.filter(color__id__in=color_ids)
        
        size_string = data.get("size", None)
        if size_string:
            size_string = size_string.replace("[", "").replace("]", "")
            size_ids = size_string.split(",")
            queryset = queryset.filter(size__id__id=size_ids)
        

        return queryset.distinct()


class ColorsFilter:
    @staticmethod
    def apply_filters(queryset, request):
        data = request.query_params

        category_id = data.get("category", None)
        if category_id:
            try:
                category_id = int(category_id)
                queryset = queryset.filter(products__category__id=category_id)
            except:
                pass

        return queryset.distinct()


class SizeFilter:
    @staticmethod
    def apply_filters(queryset, request):
        data = request.query_params

        category_id = data.get("category", None)
        if category_id:
            try:
                category_id = int(category_id)
                queryset = queryset.filter(products__category__id=category_id)
            except:
                pass

        return queryset.distinct()
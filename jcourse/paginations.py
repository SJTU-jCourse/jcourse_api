from rest_framework.pagination import PageNumberPagination


class GlobalPageNumberPagination(PageNumberPagination):
    max_page_size = 100
    page_size_query_param = 'size'

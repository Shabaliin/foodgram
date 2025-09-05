from rest_framework.pagination import PageNumberPagination

PAGE_SIZE_DEFAULT = 6


class StandardResultsSetPagination(PageNumberPagination):
    page_query_param = 'page'
    page_size_query_param = 'limit'
    page_size = PAGE_SIZE_DEFAULT

from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """12 записей на страницу; клиент может попросить больше через ?page_size= (до 100)."""

    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100

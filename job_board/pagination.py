from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class BasePagination(PageNumberPagination):
    page_size = 10

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data
        })

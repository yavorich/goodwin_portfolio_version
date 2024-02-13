from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from collections import OrderedDict


class PageNumberSetPagination(PageNumberPagination):
    """
    Convenient and detailed DRF pagination class
    """

    page_size = 20
    page_size_query_param = "page_size"

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("count", self.page.paginator.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("current_page", self.page.number),
                    (
                        "next_page",
                        self.page.next_page_number() if self.page.has_next() else None,
                    ),
                    (
                        "previous_page",
                        self.page.previous_page_number()
                        if self.page.has_previous()
                        else None,
                    ),
                    ("num_pages", self.page.paginator.num_pages),
                    ("results", data),
                ]
            )
        )

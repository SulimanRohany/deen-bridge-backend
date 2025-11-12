from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    # default page size
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100 

    def get_page_size(self, request):
        """
        This method checks whether a custom 'page_size' is provided in the query.
        If no 'page_size' is provided, it returns None, meaning no pagination.
        """

        page_size = request.query_params.get(self.page_size_query_param)

        if page_size:
            try:
                # check if the paeg is an integer and within the allowed range
                page_size = int(page_size)
                if page_size > self.max_page_size:
                    page_size = self.max_page_size
                return page_size
            except ValueError:
                return(self.page_size)
        return None # No pagination (returns all data)

    def get_paginated_response(self, data):
        return Response(
            {
                'links': {
                    "next": self.get_next_link(),
                    "previous": self.get_previous_link()
                },
                "count": self.page.paginator.count,
                'total_pages': self.page.paginator.num_pages,
                'results': data
            }
        )
    


# Example
# GET /api/items/?page=1&page_size=200

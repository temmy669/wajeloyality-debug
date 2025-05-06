from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import AccountantData
from .serializers import AuditorSerializer

class AuditorPagination(PageNumberPagination):
    page_size = 10  # Set the default number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100  # Optionally limit the max page size

class AuditorAPIView(APIView):
    # permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get(self, request, *args, **kwargs):
        # Get all AccountantData
        accountant_data = AccountantData.objects.all()

        # Apply pagination to the query results
        paginator = AuditorPagination()
        paginated_data = paginator.paginate_queryset(accountant_data, request)

        # Serialize the paginated data
        serializer = AuditorSerializer(paginated_data, many=True)

        # Return the paginated and serialized data as a response
        return paginator.get_paginated_response(serializer.data)

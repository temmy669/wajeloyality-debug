from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import AccountantData
from .serializers import AuditorSerializer
from. permissions import IsAuditor

class AuditorAPIView(APIView):
    permission_classes = [IsAuditor]  

    def get(self, request, *args, **kwargs):
        merchID = getattr(request.user, "merchID_from_token", None)

        # Get all AccountantData
        accountant_data = AccountantData.objects.filter(merchID=merchID)

        # Apply pagination to the query results
        paginator = PageNumberPagination()
        paginated_data = paginator.paginate_queryset(accountant_data, request)

        # Serialize the paginated data
        serializer = AuditorSerializer(paginated_data, many=True)

        # Return the paginated and serialized data as a response
        return paginator.get_paginated_response(serializer.data)

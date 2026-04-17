from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from .models import AccountantData
from .serializers import AuditorSerializer
from. permissions import IsAuditor
from django.db.models import Q

class AuditorAPIView(APIView):
    permission_classes = [IsAuditor]  

    def get(self, request, *args, **kwargs):
        merchID = getattr(request.user, "merchID_from_token", None)
        search_query = request.query_params.get("search")

        queryset = AccountantData.objects.filter(
            merchID=merchID
        ).order_by('-dateConfirmed')

        if search_query and len(search_query) >= 2:
            queryset = queryset.filter(
                Q(transactionRef__icontains=search_query) |
                Q(cardName__icontains=search_query) |
                Q(confirmationCode__icontains=search_query) |
                Q(customer__icontains=search_query)
            )

        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)

        serializer = AuditorSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
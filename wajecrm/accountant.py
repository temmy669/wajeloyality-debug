import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import AccountantData, merchant
from .permissions import IsAccountant  # Ensure this is defined in your permissions.py
from .serializers import AccountantDataSerializer, AccountantGetSerializer
from rest_framework import serializers
from drf_spectacular.utils import extend_schema
from rest_framework.pagination import PageNumberPagination


@extend_schema(tags=['Finance'])
class VerifyTransactionAPIView(APIView):
    permission_classes = [IsAccountant] 
    """Verify a transaction and save the data"""

    def post(self, request, *args, **kwargs):
        merchID = getattr(request.user, "merchID_from_token", None)
        userID = request.user
        
        # Convert merchID from int to Merchant instance
        merchant_instance = merchant.objects.get(id=merchID) if merchID else None


        serializer = AccountantDataSerializer(
            data=request.data,
            context={
                'merchID': merchant_instance,
                'userID': userID
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "message": "Transaction verified and recorded.",
            "status": True
        }, status=status.HTTP_201_CREATED)

    def get(self, request):
        merchID = getattr(request.user, "merchID_from_token", None)
        transaction_id = request.query_params.get("id")

        # If a specific transaction is requested
        if transaction_id:
            transaction = AccountantData.objects.filter(id=transaction_id, merchID=merchID).first()
            if transaction:
                serializer = AccountantGetSerializer(transaction)
                return Response({"status": True, "message": serializer.data}, status=status.HTTP_200_OK)
            return Response({"error": "Transaction not found.", "status": False}, status=status.HTTP_404_NOT_FOUND)

        # If fetching all transactions for the merchant
        transactions = AccountantData.objects.filter(merchID=merchID)
        paginator = PageNumberPagination()
        paginated_transactions = paginator.paginate_queryset(transactions, request)
        serializer = AccountantGetSerializer(paginated_transactions, many=True)
        return paginator.get_paginated_response({"status": True, "message": serializer.data})
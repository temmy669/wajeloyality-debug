import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import AccountantData
from .serializers import AuditorDataSerializer
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Finance'])
class AuditorAPIView(APIView):

    def get(self, request):
        """Retrieve all transactions or a specific transaction"""
        transaction_id = request.query_params.get('transaction_id')  # For example, querying by transaction_id
        
        if transaction_id:  # Check if a specific transaction is requested
            try:
                transaction = AccountantData.objects.get(id=transaction_id)
                serializer = AuditorDataSerializer(transaction)
                return Response({
                    "status": True, 
                    "message": "Transaction found.",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            except AccountantData.DoesNotExist:
                return Response({
                    "error": "Transaction not found.", 
                    "status": False
                }, status=status.HTTP_404_NOT_FOUND)
        
        # If no transaction_id is provided, return all transactions
        transactions = AccountantData.objects.all()
        serializer = AuditorDataSerializer(transactions, many=True)
        return Response({
            "status": True,
            "message": "Transactions retrieved successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

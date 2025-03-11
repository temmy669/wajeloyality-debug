import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import AccountantData
from .serializers import AccountantDataSerializer
from rest_framework import serializers
from drf_spectacular.utils import extend_schema

@extend_schema(tags=['Finance'])
class VerifyTransactionAPIView(APIView):
    """Verify a transaction and save the data"""

    def post(self, request, *args, **kwargs):
        serializer = AccountantDataSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            accountant_data = serializer.save()
            return Response({
                "message": "Transaction verified and recorded.",
                "status": True}, status=status.HTTP_201_CREATED)
        return Response({"status":False, "message":serializer.errors})

    def get(self, request):
        """Retrieve a transaction by ID or return all transactions if no ID is provided."""
        transaction_id = request.query_params.get("id")
        if transaction_id:
            transaction = AccountantData.objects.filter(id=transaction_id).first()
            if transaction:
                serializer = AccountantDataSerializer(transaction)
                return Response({"status": True, "message":serializer.data}, status=status.HTTP_200_OK)
            return Response({"error": "Transaction not found.", "status":True}, status=status.HTTP_404_NOT_FOUND)

        transactions = AccountantData.objects.all()
        serializer = AccountantDataSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


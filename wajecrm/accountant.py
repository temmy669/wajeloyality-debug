import requests
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import AccountantData
from .serializers import AccountantDataSerializer
from rest_framework import serializers

class VerifyTransactionAPIView(APIView):
    """Verify a transaction and save the data"""

    def post(self, request, *args, **kwargs):
        serializer = AccountantDataSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            accountant_data = serializer.save()
            return Response({
                "message": "Transaction verified and recorded."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        """Retrieve a transaction by ID or return all transactions if no ID is provided."""
        transaction_id = request.query_params.get("id")

        if transaction_id:
            transaction = AccountantData.objects.filter(id=transaction_id).first()
            if transaction:
                serializer = AccountantDataSerializer(transaction)
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response({"error": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)

        transactions = AccountantData.objects.all()
        serializer = AccountantDataSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


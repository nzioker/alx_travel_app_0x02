# listings/views.py
import requests
import json
import uuid
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Booking, Payment

class InitiatePaymentView(APIView):
    """
    API endpoint to create a Payment record and get a Chapa checkout URL.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking = get_object_or_404(Booking, id=booking_id, user=request.user)
            
            # Check if booking already has a successful payment
            if booking.payments.filter(status='success').exists():
                return Response(
                    {'error': 'This booking is already paid for.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create a new Payment record
            payment = Payment.objects.create(
                booking=booking,
                amount=booking.total_price,
                customer_email=request.user.email,
                customer_first_name=request.user.first_name,
                customer_last_name=request.user.last_name,
                status='initiated',
                tx_ref=f"alxtravel-{uuid.uuid4().hex[:10]}"  # Unique reference
            )

            # Prepare payload for Chapa API[citation:8]
            chapa_payload = {
                "amount": str(payment.amount),
                "currency": "ETB",
                "email": payment.customer_email,
                "first_name": payment.customer_first_name,
                "last_name": payment.customer_last_name,
                "phone_number": payment.customer_phone or "0912345678",  # Example
                "tx_ref": payment.tx_ref,
                "callback_url": f"https://yourdomain.com/api/payments/verify/",  # Your verify endpoint
                "return_url": f"https://yourdomain.com/booking/{booking.id}/success/",  # Your success page
                "customization": {
                    "title": "ALX Travel Booking",
                    "description": f"Payment for booking #{booking.id}"
                }
            }

            # Make request to Chapa
            headers = {
                'Authorization': f'Bearer {settings.CHAPA_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                f"{settings.CHAPA_BASE_URL}/v1/transaction/initialize",
                json=chapa_payload,
                headers=headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data['status'] == 'success':
                    payment.chapa_transaction_id = response_data.get('data', {}).get('id', '')
                    payment.save()
                    
                    # Return the checkout URL to the frontend[citation:8]
                    return Response({
                        'status': 'success',
                        'message': 'Payment initiated successfully.',
                        'checkout_url': response_data['data']['checkout_url'],
                        'tx_ref': payment.tx_ref
                    })
            
            # If Chapa request failed
            payment.status = 'failed'
            payment.save()
            return Response(
                {'error': 'Failed to initiate payment with Chapa.', 'details': response.text},
                status=status.HTTP_502_BAD_GATEWAY
            )

        except Exception as e:
            return Response(
                {'error': 'An internal server error occurred.', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

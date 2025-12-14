# In your listings/models.py
import uuid
from django.db import models
from django.conf import settings

class Payment(models.Model):
    """
    Stores all information related to a payment transaction.
    """
    # Link to the booking this payment is for
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='payments')
    # A unique reference you generate for Chapa
    tx_ref = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    # Chapa's internal transaction ID (filled after initiation)
    chapa_transaction_id = models.CharField(max_length=100, blank=True)
    # Payment amount
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment status tracking
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('initiated', 'Initiated - Sent to Chapa'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Customer info needed for Chapa API
    customer_email = models.EmailField()
    customer_first_name = models.CharField(max_length=100)
    customer_last_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=15, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.tx_ref} - {self.status}"

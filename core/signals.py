from .models import Payment,Address,Order,TransactionRecord,Wallet
from paypal.standard.ipn.signals import valid_ipn_received
import random
import string
from django.dispatch import receiver

def create_charge_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

@receiver(valid_ipn_received)
def payment_notification(sender, **kwargs):
    ipn = sender
    if ipn.payment_status == 'Completed':
        # payment was successful
        order = Order.objects.get(ref_code=ipn.invoice)
        wallet = Wallet.objects.get(user=order.user)
        if order.get_total() == ipn.mc_gross:
            # mark the order as paid
            order.ordered = True
            order.save()

            charge = create_charge_id()
            charge = charge.upper()

            payment = Payment(
                charge_id=charge,
                user=order.user,
                amount=order.get_total()
            )
            payment.save()

            order.payment = payment
            order.save()

            transaction = TransactionRecord(
                wallet=wallet,
                amount=order.get_total(),
                transaction_type='S'
            )

            transaction.save()



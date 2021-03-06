from django.views.generic import ListView,DetailView,View
from core.models import Item, Order, OrderItem,Address,Payment,UserProfile,Coupon,Refund,Wallet,TransactionRecord,DepositRequest
from django.shortcuts import render, redirect, get_object_or_404,reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckoutForm, CouponForm, RefundForm, WalletPaymentForm,WalletDepositForm,WalletWithdrawForm
from django.conf import settings 
from decimal import Decimal
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import string
import json
from django.http import JsonResponse
import random

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

def create_charge_id():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

class ShopView(ListView):
    model = Item
    template_name = 'shop.htm'
   
class ItemDetailView(DetailView):
    model = Item
    template_name = 'product.htm'

class OrderSummaryView(LoginRequiredMixin,View):
    def get(self,*args,**kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'cart.htm', context)
        except ObjectDoesNotExist:
            return redirect("core:shop")


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, order_type ='BG', ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to your cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()

        ref_code = create_ref_code()
        ref_code = ref_code.upper()

        order = Order.objects.create(
            user=request.user, order_type='BG', ordered_date=ordered_date,ref_code = ref_code)
        order.items.add(order_item)
        return redirect("core:order-summary")

@login_required
def remove_from_cart(request,slug):
    item = get_object_or_404(Item,slug=slug)
    order_qs = Order.objects.filter(user=request.user, order_type='BG', ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item =  OrderItem.objects.filter(item=item,user=request.user,ordered=False)[0]
            order.items.remove(order_item)

            return redirect("core:order-summary")
            
        else:
            #msg order does not contain the order item
            return redirect("core:product",{'slug':slug})
    else:
        return redirect("core:product",{'slug':slug})
    return redirect("core:product",{'slug':slug})

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False,
        order_type= 'BG'
    )
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                user=request.user,
                ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            return redirect("core:order-summary")
        else:
            return redirect("core:product", slug=slug)
    else:
        return redirect("core:product", slug=slug)

class CheckoutView(View):
    def get(self,*args,**kwargs):
        try:
            form = CheckoutForm()
            order = Order.objects.get(user=self.request.user,ordered=False)
            
            context = {
                'form':form,
                'order':order,
            }

            # if use default shipping Address
            shipping_address_qs = Address.objects.filter(
                user = self.request.user,
                default=True,
                address_type = 'S'
            )
            if shipping_address_qs.exists():
                context.update(
                    {'default_shipping_address':shipping_address_qs[0]}
                )
            
            #if use default billing Address
            billing_address_qs = Address.objects.filter(
                user = self.request.user,
                default = True,
                address_type = 'B'
            )
            if billing_address_qs.exists():
                context.update(
                    {'default_billing_address':billing_address_qs[0]}
                )

            return render(self.request,'checkout.htm',context)

        except ObjectDoesNotExist:
            return redirect("core:order-summary")

    def post(self,*args,**kwargs):
        form = CheckoutForm(self.request.POST or None)
        
        try:
            order = Order.objects.get(user=self.request.user,ordered=False)
            wallet = Wallet.objects.get(user=self.request.user)
            if form.is_valid():
                if order.order_type == 'BG':
                    use_default_shipping = form.cleaned_data.get('use_default_shipping')
                    if use_default_shipping:
                        print("Using the default shipping address")
                        address_qs = Address.objects.filter(
                            user = self.request.user,
                            default = True,
                            address_type = 'S'
                        )
                        if address_qs.exists():
                            shipping_address = address_qs[0]
                            order.shipping_address = shipping_address
                            order.save()
                        else:
                            return redirect("core:checkout")
                    else:
                        print("user is entering a new shipping address")
                        shipping_address1 = form.cleaned_data.get('shipping_address')
                        shipping_address2 = form.cleaned_data.get('shipping_address2')
                        shipping_zip = form.cleaned_data.get('shipping_zip')

                        # creating a new shipping address
                        shipping_address = Address(
                            user = self.request.user,
                            street_address = shipping_address1,
                            apartment_address = shipping_address2,
                            zip = shipping_zip,
                            address_type = 'S'
                        )

                        shipping_address.save()
                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                use_default_billing = form.cleaned_data.get('use_default_billing')
                same_billing_address = form.cleaned_data.get('same_billing_address')
                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()
                elif use_default_billing:
                    billing_qs = Address.objects.filter(
                        user = self.request.user,
                        address_type = 'B',
                        default = True
                    )
                    if billing_qs.exists():
                        billing_address= billing_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        return redirect("core:checkout")
                else:
                    print("User is entering a new billing address")
                    billing_address1 = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_zip = form.cleaned_data.get('billing_zip')

                    billing_address = Address(
                        user = self.request.user,
                        street_address = billing_address1,
                        apartment_address = billing_address2,
                        zip = billing_zip,
                        address_type = "B"
                    )
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                    set_default_billing = form.cleaned_data.get('set_default_billing')
                    if set_default_billing:
                        billing_address.default = True
                        billing_address.save()

                # Wallet Payment
                if order.order_type == 'BG' and wallet.balance > order.get_total() + 10:
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
                    wallet.balance -= order.get_total()
                    wallet.save()

                    transaction = TransactionRecord(
                        wallet=wallet,
                        amount=order.get_total(),
                        transaction_type= 'S'
                    )
                    transaction.save()

                    return redirect("home")
                return redirect("core:payment")

        except ObjectDoesNotExist:
            return redirect("core:order-summary")

@login_required()
def payment_view(request):
    order = Order.objects.get(user=request.user,ordered=False)
    wallet = Wallet.objects.get(user= request.user)

    context = {
                'wallet':wallet,
                'order':order,
              }

    return render(request,'payment2.htm',context)

def payment_complete(request):
    wallet = Wallet.objects.get(user= request.user)
    orderRefCode = ''
    if 'orderRefCode' in request.COOKIES:
        orderRefCode = request.COOKIES['orderRefCode']
        order = Order.objects.get(ref_code=orderRefCode)

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

        if order.order_type == 'D':

            wallet.balance += order.get_total()

            transaction = TransactionRecord(
                wallet=wallet,
                amount=order.get_total(),
                transaction_type='E'
            )
            transaction.save()

            return redirect("core:wallet")

        transaction = TransactionRecord(
            wallet=wallet,
            amount=order.get_total(),
            transaction_type='S'
        )

        transaction.save()

        return redirect("home")

    return redirect("home")

class WalletView(View):
    def get(self,*args,**kwargs):
        try:
            wallet = Wallet.objects.get(user=self.request.user)
            transactions = TransactionRecord.objects.filter(wallet=wallet).order_by('-date')
            orders = Order.objects.filter(user=self.request.user,
                                        ordered=True)

            context = {
                'wallet':wallet,
                'orders':orders,
                'transactions':transactions,
            }
            return render(self.request,'wallet.htm',context)

        except ObjectDoesNotExist:
            return redirect("core:shop")
    def post(self,*args,**kwargs):
        pass


class WithdrawView(View):
    def get(self,*args,**kwargs):
        try:
            wallet = Wallet.objects.get(user=self.request.user)
            form = WalletWithdrawForm()

            context = {
                'wallet':wallet,
                'form':form,
            }
            return render(self.request,'withdraw.htm',context)

        except ObjectDoesNotExist:
            return redirect("core:shop")

    def post(self,*args,**kwargs):
        form = WalletWithdrawForm(self.request.POST or None)
        try:
            wallet = Wallet.objects.get(user=self.request.user)

            if form.is_valid():
                amount = form.cleaned_data.get('amount')
                if wallet.balance > amount:

                    wallet.balance -= amount
                    wallet.save()

                    transaction_record = TransactionRecord(
                        wallet=wallet,
                        amount=amount,
                        transaction_type='S'
                    )

                    transaction_record.save()

                    return redirect("core:withdraw-funds")
                else:
                    return redirect("core:wallet")
            else:
                return redirect("core:withdraw-funds")
        except ObjectDoesNotExist:
            return redirect("core:wallet")


class DepositView(View):
    def get(self,*args,**kwargs):
        try:
            wallet = Wallet.objects.get(user=self.request.user)
            form = WalletDepositForm()

            context = {
                'wallet':wallet,
                'form':form,
            }
            return render(self.request,'deposit.htm',context)

        except ObjectDoesNotExist:
            return redirect("core:shop")

    def post(self,*args,**kwargs):
        form = WalletDepositForm(self.request.POST or None)
        try:
            wallet = Wallet.objects.get(user=self.request.user)

            if form.is_valid():
                amount = form.cleaned_data.get('amount')
                
                deposit_request = DepositRequest(
                    wallet=wallet,
                    amount=amount
                )
                deposit_request.save()


                ordered_date = timezone.now()
                ref_code = create_ref_code()
                ref_code = ref_code.upper()

                order = Order(
                    value=deposit_request.amount,
                    user=self.request.user,
                    ref_code = ref_code,
                    ordered_date=ordered_date,
                    order_type='D'    
                )
                order.save()

                deposit_request.order = order 
                deposit_request.save()

                return redirect("core:checkout")
            else:
                return redirect("core:deposit-funds")
        except ObjectDoesNotExist:
            return redirect("core:wallet")
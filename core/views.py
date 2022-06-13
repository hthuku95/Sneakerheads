from django.views.generic import ListView,DetailView,View
from core.models import Item, Order, OrderItem,Address,Payment,UserProfile,Coupon,Refund,Wallet,TransactionRecord
from django.shortcuts import render, redirect, get_object_or_404,reverse
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CheckoutForm, CouponForm, RefundForm, WalletPaymentForm,WalletDepositForm,WalletWithdrawForm
from django.conf import settings 
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import string
import json
from django.http import JsonResponse
import random

def create_ref_code():
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
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:shop")


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(
        item=item,
        user=request.user,
        ordered=False
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
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
            user=request.user, ordered_date=ordered_date,ref_code = ref_code)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")

@login_required
def remove_from_cart(request,slug):
    item = get_object_or_404(Item,slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        if order.items.filter(item__slug=item.slug).exists():
            order_item =  OrderItem.objects.filter(item=item,user=request.user,ordered=False)[0]
            order.items.remove(order_item)

            messages.info(request,"This item was removed from your cart")
            return redirect("core:order-summary")
            
        else:
            #msg order does not contain the order item
            messages.info(request,"Your cart does not contain the product")
            return redirect("core:product",{'slug':slug})
    else:
        messages.info(request,"Your cart is empty")
        return redirect("core:product",{'slug':slug})
    return redirect("core:product",{'slug':slug})

@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        user=request.user,
        ordered=False
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
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
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
            messages.warning(self.request,"You do not have an active order")
            return redirect("core:order-summary")

    def post(self,*args,**kwargs):
        form = CheckoutForm(self.request.POST or None)
        
        try:
            order = Order.objects.get(user=self.request.user,ordered=False)
            if form.is_valid():

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
                        messages.info(self.request,"No default shipping Address available")
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
                        messages.info(self.request,"No default billing address available")
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
                return redirect("core:payment")

        except ObjectDoesNotExist:
            messages.warning(self.request,"You do not have an active order")
            return redirect("core:order-summary")

@login_required()
def payment_view(request):
    order = Order.objects.get(user=request.user,ordered=False)
    wallet = Wallet.objects.get(user= request.user)
    
    context = {
                'wallet':wallet,
                'order':order,
              }
    return render(request,'payment.htm',context)




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
            messages.warning(self.request,"You do not have a wallet")
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
            messages.warning(self.request,"You do not have a wallet")
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

                    messages.success(self.request,"Your withdrawal request has been completed succesfully")
                    return redirect("core:withdraw-funds")
                else:
                    messages.warning(self.request,"You do not have enough funds to complete the request" )
                    return redirect("core:wallet")
            else:
                messages.warning(self.request,"Please enter a valid amount" )
                return redirect("core:withdraw-funds")
        except ObjectDoesNotExist:
            messages.warning(self.request,"You do not have enough funds to complete the request" )
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
            messages.warning(self.request,"You do not have a wallet")
            return redirect("core:shop")

    def post(self,*args,**kwargs):
        form = WalletDepositForm(self.request.POST or None)
        try:
            wallet = Wallet.objects.get(user=self.request.user)

            if form.is_valid():
                amount = form.cleaned_data.get('amount')
                wallet.balance+= amount
                wallet.save()

                transaction_record = TransactionRecord(
                        wallet=wallet,
                        amount=amount,
                        transaction_type='E'
                    )

                transaction_record.save()

                messages.success(self.request,"Your Deposit request has been completed succesfully")
                return redirect("core:deposit-funds")
            else:
                messages.warning(self.request, "please enter a valid amount")
                return redirect("core:deposit-funds")
        except ObjectDoesNotExist:
            messages.warning(self.request,"Something went wrong please try again later" )
            return redirect("core:wallet")
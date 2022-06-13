from django.urls import path

from .views import (
    ShopView,
    ItemDetailView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart,
    remove_single_item_from_cart,
    CheckoutView,
    payment_view,
    WalletView,
    WithdrawView,
    DepositView,
)

app_name = 'core'

urlpatterns = [
    path(r'',ShopView.as_view(),name='shop'),
    path(r'cart/',OrderSummaryView.as_view(),name='order-summary'),
    path(r'checkout/',CheckoutView.as_view(),name='checkout'),
    path(r'payment/',payment_view,name='payment'),
    path(r'product/<slug>/', ItemDetailView.as_view(), name='product'),
    path(r'add_to_cart/<slug>/',add_to_cart,name='add-to-cart'),
    path(r'wallet/',WalletView.as_view(),name='wallet'),
    path(r'deposit_funds/',DepositView.as_view() ,name='deposit-funds'),
    path(r'withdraw_funds/',WithdrawView.as_view(),name='withdraw-funds'),
    path(r'remove_from_cart/<slug>/',remove_from_cart,name='remove-from-cart'),
    path(r'remove_single_item_from_cart/<slug>/',remove_single_item_from_cart, name='remove-single-item-from-cart'),
]

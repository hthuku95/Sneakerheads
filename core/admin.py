from django.contrib import admin
from .models import Item, Order, OrderItem,Address,Coupon,Refund,Payment,UserProfile,Wallet,TransactionRecord,DepositRequest

class ItemAdmin(admin.ModelAdmin):
    list_display = ('title','price','category')
    list_filter = ('category',)

admin.site.register(Item,ItemAdmin)
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Coupon)
admin.site.register(Address)
admin.site.register(Refund)
admin.site.register(Payment)
admin.site.register(UserProfile)
admin.site.register(Wallet)
admin.site.register(TransactionRecord)
admin.site.register(DepositRequest)

from django.db import models
from django.conf import settings
from django.shortcuts import reverse

# Create your models here.

CATEGORY_CHOICES = (
    ('M','Men'),
    ('W','Women'),
    ('CH','Children'),
    ('WA','Wathces'),
    ('AJ','Air Jordan'),
    ('SW','Sport wear'),
    ('OW','Out wear')
)

ORDER_TYPE_CHOICES = (
    ('D','Deposit'),
    ('BG','Buy goods')
)

LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)

ADDRESS_CHOICES = (
    ('B','Billing'),
    ('S','Shipping')
)

TRANSACTION_CHOICES = (
    ('E','Earned'),
    ('S','Spent')
)

PAYMENT_CHOICES = (
    ('P','Paypal'),
    ('W','Wallet')
)

class UserProfile(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50,blank=True,null=True)
    paypal_customer_id  = models.CharField(max_length=50,blank=True,null=True)
    
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    id = models.AutoField(primary_key=True)
    charge_id = models.CharField(max_length=50,blank=True,null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username

class Address(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Item(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField( max_length=100)
    price = models.FloatField()
    thumbnail = models.FileField(blank=True,null=True)
    discount_price = models.FloatField(blank=True,null=True)
    label = models.CharField(choices=LABEL_CHOICES,max_length=1)
    category = models.CharField(choices=CATEGORY_CHOICES,max_length=2)
    slug = models.SlugField()
    description = models.TextField()
    date = models.DateTimeField( auto_now_add=True,blank=True,null=True)
    display_image_one = models.FileField( blank=True,null=True)
    display_image_two = models.FileField( blank=True,null=True)
    display_image_three = models.FileField( blank=True,null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={"slug": self.slug})

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart",kwargs={"slug":self.slug})
    
    def remove_from_cart_url(self):
        return reverse("core:remove-from-cart",kwargs={"slug":self.slug})


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,blank=True,null=True)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    def __str__(self):
        return self.item.title

    def get_total_item_price(self):
        return self.item.price * self.quantity

    def get_total_discount_item_price(self):
        return self.item.discount_price * self.quantity

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()
        
    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        else:
            return self.get_total_item_price()

class Order(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    order_type = models.CharField(choices=ORDER_TYPE_CHOICES, max_length=2,blank=True,null=True)
    items = models.ManyToManyField(OrderItem,blank=True)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField(auto_now_add=False)
    ordered = models.BooleanField(default=False)
    ref_code = models.CharField( max_length=50,blank=True,null=True)
    value = models.FloatField(default=0.0)

    #billing and shipping address of the order
    shipping_address = models.ForeignKey(
        Address, related_name='shipping_address', on_delete=models.SET_NULL, blank=True, null=True)
    billing_address = models.ForeignKey(
        Address, related_name='billing_address', on_delete=models.SET_NULL, blank=True, null=True)
    
    payment = models.ForeignKey(Payment,  on_delete=models.SET_NULL, blank=True,null=True)

    def __str__(self):
        return self.user.username
        
    def get_total(self):
        total = self.value
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total

class Wallet(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.FloatField(default=0.0)

    def __str__(self):
        return self.user.username


class Coupon(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=15)
    amount = models.FloatField()

    def __str__(self):
        return self.code

class Refund(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()

    def __str__(self):
        return f"{self.pk}"


class TransactionRecord(models.Model):
    id = models.AutoField(primary_key=True)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    date = models.DateTimeField( auto_now_add=True)
    amount = models.FloatField()
    transaction_type = models.CharField(max_length=1,choices=TRANSACTION_CHOICES)

    def __str__(self):
        return self.wallet.user.username
    

class DepositRequest(models.Model):
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.FloatField()
    order = models.ForeignKey(Order, on_delete=models.CASCADE,blank=True,null=True)
    date = models.DateTimeField( auto_now_add=True)

    def __str__(self):
        return self.wallet.user.username


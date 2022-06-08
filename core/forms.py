from django import forms


PAYMENT_CHOICES = (
    ('S', 'Stripe'),
    ('P', 'PayPal'),
    ('W','Wallet')
)


class CheckoutForm(forms.Form):

    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)

    shipping_zip = forms.CharField(required=False)

    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)

    billing_zip = forms.CharField(required=False)

    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)

class WalletPaymentForm(forms.Form):
    use_default = forms.CharField(required=False)

class RefundForm(forms.Form):
    ref_code = forms.CharField()
    message = forms.CharField(widget=forms.Textarea(attrs={
        'rows': 4
    }))
    email = forms.EmailField()

class CouponForm(forms.Form):
    code = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Promo code',
        'aria-label': 'Recipient\'s username',
        'aria-describedby': 'basic-addon2'
    }))


class WalletWithdrawForm(forms.Form):
    amount = forms.IntegerField(widget=forms.NumberInput(
        attrs={
            'class':'form-control',
            'Placeholder':'Enter the amount you wish to Withdraw'
        }))

class WalletDepositForm(forms.Form):
    amount = forms.IntegerField(widget=forms.NumberInput(
        attrs={
            'class':'form-control',
            'Placeholder':'Enter the amount you wish to Deposit'
        }))
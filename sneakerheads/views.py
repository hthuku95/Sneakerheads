from django.views.generic import ListView,DetailView,View
from core.models import Item, Order, OrderItem,Address,Payment,UserProfile,Coupon,Refund,Wallet,TransactionRecord
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.conf import settings 
import string

import random

def index_view(request):
    watches = Item.objects.filter(category='WA')
    featured_items = Item.objects.all().order_by('-date')[:4]
    items = Item.objects.all().order_by('date')[:8]

    context = {
        'watches':watches,
        'featured_items':featured_items,
        'items':items
    }

    return render(request,'index.htm',context)
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings
from django.conf.urls.static import static
from .views import index_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path(r'',index_view,name='home'),
    path('shop/', include('core.urls')),
    path('paypal/', include('paypal.standard.ipn.urls')),
]

#appending the static files urls to the above media
urlpatterns += staticfiles_urlpatterns()
#how to upload media..appending the media url to the patterns above
urlpatterns += static(settings.MEDIA_URL,document_root = settings.MEDIA_ROOT)
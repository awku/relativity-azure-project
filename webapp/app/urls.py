from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from ms_identity_web.django.msal_views_and_urls import MsalViews

msal_urls = MsalViews(settings.MS_IDENTITY_WEB).url_patterns()

urlpatterns = [
    path('', views.get_categories, name='index'),
    path(f'{settings.AAD_CONFIG.django.auth_endpoints.prefix}/',
         include(msal_urls)),
    *static(settings.STATIC_URL, document_root=settings.STATIC_ROOT),

    path('cart/add/<slug:product_slug>/',
         views.add_product_to_cart, name='add_product_to_cart'),
    path('cart/', views.get_cart, name='get_cart'),
    path('cart/delete/', views.delete_cart, name='delete_cart'),

    path('order/add/', views.add_order, name='add_order'),
    path('order/thanks/<slug:order_id>/',
         views.get_thanks_page, name='get_thanks_page'),
    path('order/history/', views.get_orders_history,
         name='get_orders_history'),
    path('order/<slug:order_id>/', views.get_order,
         name='get_order'),

    path('products/add/', views.add_product, name='add_product'),
    path('products/delete/<slug:product_slug>/', views.delete_product, name='delete_product'),
    path('products/edit/<slug:product_slug>/', views.edit_product, name='edit_product'),
    path('products/view/<slug:product_slug>/', views.get_product, name='get_product'),

    path('categories/add/', views.add_category, name='add_category'),
    path('categories/delete/<slug:category_slug>/', views.delete_category, name='delete_category'),
    path('categories/edit/<slug:category_slug>/', views.edit_category, name='edit_category'),
    path('categories/view/<slug:category_slug>/',
         views.get_products_in_category, name='get_products_in_category'),
]

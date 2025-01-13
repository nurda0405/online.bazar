from django.contrib import admin
from .models import Category, Product, Allowed_Seller

admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Allowed_Seller)


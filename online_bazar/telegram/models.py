from django.db import models

class Category(models.Model):
    cat_id = models.IntegerField(primary_key = True)
    gender_id = models.IntegerField() #0 - men, 1 - women, 3 - kids
    position_id = models.IntegerField()
    cat_name = models.CharField(max_length = 50)

class Product(models.Model):
    product_id = models.IntegerField(primary_key = True)
    seller_username = models.TextField()
    cat_id = models.IntegerField()
    image_path = models.TextField()
    description = models.TextField()
    views = models.IntegerField()

class Allowed_Seller(models.Model):
    id = models.IntegerField(primary_key = True)
    name = models.TextField()
    seller_username = models.TextField(null=True, blank = True)
    phone_number = models.TextField()
    starting_date = models.DateField()

class User(models.Model):
    id = models.IntegerField(primary_key=True)
    

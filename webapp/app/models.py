from djongo import models
from custom.helpers import randomize_path

class Category(models.Model):
    _id = models.ObjectIdField()
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to=randomize_path, blank=True, null=True)
    objects = models.DjongoManager()

    class Meta:
        ordering = ['-_id']

    def __str__(self):
        return self.name


class Product(models.Model):
    _id = models.ObjectIdField()
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    category_slug = models.CharField(max_length=250)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to=randomize_path, blank=True, null=True)
    stock = models.IntegerField()
    is_available = models.BooleanField()
    created = models.DateTimeField(auto_now=True)
    updated = models.DateTimeField(auto_now=True)
    objects = models.DjongoManager()

    class Meta:
        ordering = ['-_id']

    def __str__(self):
        return self.name


class CartItem(models.Model):
    _id = models.ObjectIdField()
    cart_key = models.CharField(max_length=250)
    product_name = models.CharField(max_length=250)
    product_slug = models.CharField(max_length=250)
    product_image = models.ImageField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    objects = models.DjongoManager()

    class Meta:
        ordering = ['-_id']

    def __str__(self):
        return self.product_name


class OrderItem(models.Model):
    _id = models.ObjectIdField()
    order_key = models.CharField(max_length=250)
    product_name = models.CharField(max_length=250)
    product_slug = models.CharField(max_length=250)
    quantity = models.IntegerField()
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ['-_id']

    def __str__(self):
        return self.product_name

class Order(models.Model):
    _id = models.ObjectIdField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    email_address = models.EmailField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    billing_name = models.CharField(max_length=250)
    billing_address = models.CharField(max_length=250)
    billing_city = models.CharField(max_length=250)
    billing_state = models.CharField(max_length=5)
    billing_post_code = models.CharField(max_length=10)
    billing_country = models.CharField(max_length=200)

    shipping_name = models.CharField(max_length=250)
    shipping_address = models.CharField(max_length=250)
    shipping_city = models.CharField(max_length=250)
    shipping_state = models.CharField(max_length=5)
    shipping_post_code = models.CharField(max_length=10)
    shipping_country = models.CharField(max_length=200)

    cc_name = models.CharField(max_length=250)
    cc_number = models.CharField(max_length=20)
    cc_expiration = models.CharField(max_length=5)
    cc_cvv = models.CharField(max_length=3)

    objects = models.DjongoManager()

    class Meta:
        ordering = ['-_id']

    def __str__(self):
        return str(self._id)


from django.core.paginator import Paginator, EmptyPage, InvalidPage
from .models import CartItem, Product, Order, Category, OrderItem
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
from custom.helpers import is_member_of_admins, confirm_order
import logging

ms_identity_web = settings.MS_IDENTITY_WEB
logger = logging.getLogger()

def get_value_from_key(d, val):
    keys = [v for k, v in d.items() if k == val]
    if keys:
        return keys[0]
    return None


def admin_required(view):
    def wrapper(request, *args, **kwargs):
        oid = get_value_from_key(
            request.identity_context_data._id_token_claims, 'oid')
        if not is_member_of_admins(oid, settings.AZURE_CONFIG.azure_aad_b2c_tenant):
            return redirect('sign_in')
        return view(request, *args, **kwargs)
    return wrapper


def get_email_from_claims(claims):
    emails = get_value_from_key(claims, 'emails')
    if emails:
        return emails[0]
    email = get_value_from_key(claims, 'email')
    if email:
        return email
    return None


def _get_cart_key(request):
    if request.identity_context_data.authenticated:
        email = get_email_from_claims(
            request.identity_context_data._id_token_claims)
        if email:
            return email
    session_key = request.session.session_key
    if not session_key:
        session_key = request.session.create()
    return session_key


def add_product_to_cart(request, product_slug):
    product = Product.objects.get(slug=product_slug)
    cart_key = _get_cart_key(request)
    logger.info(f"function: add_product_to_cart, product: {product_slug}, cart: {cart_key}")
    try:
        cart_item = CartItem.objects.get(
            product_slug=product.slug, cart_key=cart_key)
        if cart_item.quantity < cart_item.product.stock:
            cart_item.quantity += 1
        cart_item.save()
        logger.info(f"function: add_product_to_cart, product: {product_slug}, cart: {cart_key} - add 1 to quantity")
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(cart_key=cart_key, product_name=product.name,
                                            product_slug=product.slug, product_image=product.image, product_price=product.price.to_decimal(), quantity=1)
        cart_item.save()
        logger.info(f"function: add_product_to_cart, product: {product_slug}, cart: {cart_key} - save new item")
    return redirect('get_cart')


def get_cart(request):
    cart_items = []
    logger.info(f"function: get_cart")
    try:
        cart_items = CartItem.objects.filter(cart_key=_get_cart_key(request))
        logger.info(f"function: get_cart, got {len(list(cart_items))} items")
    except ObjectDoesNotExist:
        pass
    if request.method == 'POST':
        logger.info(f"function: get_cart, POST method")
        try:
            changes = [{k, v}
                       for k, v in request.POST.items() if k.startswith('quantity_')]
            for quantity_name, input_quantity in changes:
                item_id = quantity_name.split('_')[1]
                try:
                    cart_item = CartItem.objects.get(_id=item_id)
                    product = Product.objects.get(slug=cart_item.product_slug)
                    if input_quantity > 0:
                        if  product.stock > input_quantity:
                            cart_item.quantity = input_quantity
                        else:
                            cart_item.quantity = product.stock
                        cart_item.save()
                    else:
                        cart_item.delete()
                except Exception as e:
                    logger.error(f"function: get_cart, error: {e}")
        except Exception as e:
            logger.error(f"function: get_cart, error: {e}")
    return render(request, 'app/shop/cart.html', {"cart_items" : enumerate(cart_items)})


@ms_identity_web.login_required
def delete_cart(request):
    cart_key = _get_cart_key(request)
    logger.info(f"function: delete_cart, cart_key: {cart_key}")
    cart_items = CartItem.objects.filter(cart_key=cart_key)
    for cart_item in cart_items:
        cart_item.delete()
    return redirect('get_cart')


@ms_identity_web.login_required
def add_order(request):
    cart_key = _get_cart_key(request)
    logger.info(f"function: add_order, cart_key: {cart_key}")
    total = 0
    cart_items = CartItem.objects.filter(cart_key=cart_key)
    for cart_item in cart_items:
        total += cart_item.product_price.to_decimal() * cart_item.quantity

    if request.method == "POST":
        logger.info(f"function: add_order, method POST")
        input_billing_name = request.POST['billing_name']
        input_billing_address = request.POST['billing_address']
        input_billing_city = request.POST['billing_city']
        input_billing_state = request.POST['billing_state']
        input_billing_post_code = request.POST['billing_post_code']
        input_billing_country = request.POST['billing_country']
        input_shipping_name = request.POST['shipping_name']
        input_shipping_address = request.POST['shipping_address']
        input_shipping_city = request.POST['shipping_city']
        input_shipping_state = request.POST['shipping_state']
        input_shipping_post_code = request.POST['shipping_post_code']
        input_shipping_country = request.POST['shipping_country']
        input_cc_name = request.POST['cc_name']
        input_cc_number = request.POST['cc_number']
        input_cc_expiration = request.POST['cc_expiration']
        input_cc_cvv = request.POST['cc_cvv']
        try:
            order = Order.objects.create(total=total, email_address=get_email_from_claims(request.identity_context_data._id_token_claims),
                                         billing_name=input_billing_name, billing_address=input_billing_address, billing_city=input_billing_city, billing_state=input_billing_state,
                                         billing_post_code=input_billing_post_code, billing_country=input_billing_country, shipping_name=input_shipping_name, shipping_address=input_shipping_address, shipping_city=input_shipping_city, shipping_state=input_shipping_state,
                                         shipping_post_code=input_shipping_post_code, shipping_country=input_shipping_country, cc_name=input_cc_name, cc_number=input_cc_number, cc_expiration=input_cc_expiration,
                                         cc_cvv=input_cc_cvv)
            order.save()
            for cart_item in cart_items:
                subtotal = cart_item.product_price.to_decimal() * cart_item.quantity
                OrderItem.objects.create(product_name=cart_item.product_name, product_slug=cart_item.product_slug,
                           quantity=cart_item.quantity, product_price=cart_item.product_price.to_decimal(), subtotal=subtotal, order_key=order._id)
            confirmed = confirm_order(order.email_address, order._id, settings.AZURE_CONFIG.azure_function)
            logger.info(confirmed)
            for cart_item in cart_items:
                product = Product.objects.get(slug=cart_item.product_slug)
                product.stock = product.stock - cart_item.quantity
                if product.stock == 0:
                    product.is_available = False
                product.price = product.price.to_decimal()
                product.save()
                cart_item.delete()
        except Exception as e:
            logger.error(f"function: add_order, error: {e}")
            return render(request, 'app/order/order_form.html', {'cart_items': cart_items, 'error': str(e), 'total': total})
        return redirect('get_thanks_page', order_id=order._id)
    return render(request, 'app/order/order_form.html', {'cart_items': cart_items, 'error': '', 'total': total})


@ms_identity_web.login_required
def get_thanks_page(request, order_id):
    logger.info(f"function: get_thanks_page, order_id: {order_id}")
    if order_id:
        _ = get_object_or_404(Order, _id=order_id)
    return render(request, 'app/order/thanks.html', {'order_id': order_id})


@ms_identity_web.login_required
def get_orders_history(request):
    email_address = get_email_from_claims(request.identity_context_data._id_token_claims)
    logger.info(f"function: get_orders_history, email_address: {email_address}")
    order_details = Order.objects.filter(email_address=email_address)
    output_order = list(order_details)
    print(output_order)
    return render(request, 'app/order/orders_list.html', {'order_details': output_order})


@ms_identity_web.login_required
def get_order(request, order_id):
    logger.info(f"function: get_order, order_id: {order_id}")
    order = get_object_or_404(Order, _id=order_id)
    order_items = OrderItem.objects.filter(order_key=order_id)
    return render(request, 'app/order/order_detail.html', {'order': order, 'order_items': order_items})

def get_categories(request):
    logger.info(f"function: get_categories")
    categories_list = Category.objects.all()
    paginator = Paginator(categories_list, 6)
    try:
        page = int(request.GET.get('page', '1'))
    except:
        page = 1
    try:
        categories = paginator.page(page)
    except (EmptyPage, InvalidPage):
        categories = paginator.page(paginator.num_pages)
    return render(request, 'app/shop/categories.html', {'categories': categories})


@admin_required
@ms_identity_web.login_required
def delete_category(request, category_slug):
    logger.info(f"function: delete_category, category_slug: {category_slug}")
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category_slug=category_slug)
    for product in products:
        product.is_available = False
        product.save()
        cart_items = CartItem.objects.filter(product_slug=product.slug)
        if cart_items:
            cart_items.delete()
    category.delete()
    return redirect('index')


def get_products_in_category(request, category_slug):
    logger.info(f"function: get_products_in_category, category_slug: {category_slug}")
    category = get_object_or_404(Category, slug=category_slug)
    products_list = Product.objects.filter(
        category_slug=category_slug)
    paginator = Paginator(products_list, 6)
    try:
        page = int(request.GET.get('page', '1'))
    except:
        page = 1
    try:
        products = paginator.page(page)
    except (EmptyPage, InvalidPage):
        products = paginator.page(paginator.num_pages)
    return render(request, 'app/shop/category.html', {'category': category, 'products': products})


def get_product(request, product_slug):
    logger.info(f"function: get_product, product_slug: {product_slug}")
    product = get_object_or_404(Product, slug=product_slug)
    return render(request, 'app/shop/product.html', {'product': product})


@admin_required
@ms_identity_web.login_required
def add_category(request):
    logger.info(f"function: add_category")
    if request.method == "POST":
        error = None
        logger.info(f"function: add_category, method POST")
        input_name = request.POST['name']
        input_slug = request.POST['slug']
        input_description = request.POST['description']
        if request.FILES and 'image' in request.FILES:
            input_image = request.FILES['image']
        else:
            input_image = None
        try:
            test_category = Category.objects.filter(slug=input_slug)
            if len(test_category) > 0:
                error = "A category with given slug already exists"
            else:
                category = Category.objects.create(
                    name=input_name, slug=input_slug, description=input_description, image=input_image)
                category.save()
                return redirect('get_products_in_category', category_slug=input_slug)
        except Exception as e:
            logger.error(f"function: add_category, error: {e}")
            error = str(e)
        if error:
            return render(request, 'app/shop/category_form.html', {'title': 'Create a category', 'error': error})
    return render(request, 'app/shop/category_form.html', {'title': 'Create a category'})


@admin_required
@ms_identity_web.login_required
def edit_category(request, category_slug):
    logger.info(f"function: edit_category, category_slug: {category_slug}")
    category = get_object_or_404(Category, slug=category_slug)
    if request.method == "POST":
        logger.info(f"function: edit_category, method POST")
        input_name = request.POST['name']
        input_description = request.POST['description']
        if request.FILES and 'image' in request.FILES:
            input_image = request.FILES['image']
        else:
            input_image = None
        try:
            if input_image:
                category.image = input_image
            category.name=input_name
            category.description=input_description
            category.save()
            return redirect('get_products_in_category', category_slug=category_slug)
        except Exception as e:
            logger.error(f"function: edit_category, error: {e}")
            return render(request, 'app/shop/category_form.html', {'title': 'Edit a category', 'category': category, 'error': str(e)})
    return render(request, 'app/shop/category_form.html', {'title': 'Edit a category', 'category': category})


@admin_required
@ms_identity_web.login_required
def add_product(request):
    logger.info(f"function: add_product")
    category_options = [
        entry for entry in Category.objects.values('slug', 'name')]
    if request.method == "POST":
        error = None
        logger.info(f"function: add_product, method POST")
        input_name = request.POST['name']
        input_slug = request.POST['slug']
        input_description = request.POST['description']
        input_category_slug = request.POST['category_slug']
        input_price = request.POST['price']
        input_stock = request.POST['stock']
        if request.FILES and 'image' in request.FILES:
            input_image = request.FILES['image']
        else:
            input_image = None
        try:
            test_product = Product.objects.filter(slug=input_slug)
            if len(test_product) > 0:
                error = "A product with given slug already exists"
            else:
                product = Product.objects.create(name=input_name, slug=input_slug, description=input_description, category_slug=input_category_slug,
                                             price=input_price, image=input_image, stock=input_stock, is_available=True)
                product.save()
                return redirect('get_product', product_slug=input_slug)
        except Exception as e:
            logger.error(f"function: add_product, error: {e}")
            error = str(e)
        if error:
            return render(request, 'app/shop/product_form.html', {'title': 'Add a product', 'category_options': category_options, 'error': error})
    return render(request, 'app/shop/product_form.html', {'title': 'Add a product', 'category_options': category_options})


@admin_required
@ms_identity_web.login_required
def edit_product(request, product_slug):
    logger.info(f"function: edit_product, product_slug: {product_slug}")
    product = get_object_or_404(Product, slug=product_slug)
    category_options = [
        entry for entry in Category.objects.values('slug', 'name')]
    if request.method == "POST":
        error = None
        logger.info(f"function: edit_product, method POST")
        input_name = request.POST['name']
        input_description = request.POST['description']
        input_category_slug = request.POST['category_slug']
        input_price = request.POST['price']
        input_stock = request.POST['stock']
        if request.FILES and 'image' in request.FILES:
            input_image = request.FILES['image']
        else:
            input_image = None
        try:
            if input_image:
                product.image=input_image
            product.name=input_name
            product.description=input_description
            product.category_slug=input_category_slug
            product.price=input_price
            product.image=input_image
            product.stock=input_stock
            product.save()
            cart_items = CartItem.objects.filter(product_slug = product.slug)
            for cart_item in cart_items:
                cart_item.product_name=product.name
                cart_item.product_slug=product.slug
                cart_item.product_image=product.image
                cart_item.product_price=product.price
                cart_item.save()
            return redirect('get_product', product_slug=product_slug)    
        except Exception as e:
            logger.error(f"function: edit_product, error: {e}")
            error = str(e)
        if error:
            return render(request, 'app/shop/product_form.html', {'title': 'Edit a product', 'category_options': category_options, 'product': product, 'error': error})
    return render(request, 'app/shop/product_form.html', {'title': 'Edit a product', 'category_options': category_options, 'product': product})


@admin_required
@ms_identity_web.login_required
def delete_product(request, product_slug):
    logger.info(f"function: delete_product, product_slug: {product_slug}")
    product = get_object_or_404(Product, slug=product_slug)
    product.is_available = False
    product.save()
    return redirect('get_products_in_category', category_slug=product.category_slug)

from django.urls import reverse
from django.conf import settings
from app.models import CartItem
from app.views import _get_cart_key
from custom.helpers import is_member_of_admins, return_insights_script
import logging

logger = logging.getLogger()

def context(request):
    claims = request.identity_context_data._id_token_claims
    exclude_claims = ['iat', 'exp', 'nbf', 'uti', 'aio', 'rh']
    claims_to_display = {claim: value for claim,
                         value in claims.items() if claim not in exclude_claims}

    logger.debug(f"function: context, claims_to_display: {claims_to_display}")

    if 'oid' in claims_to_display:
        is_admin = is_member_of_admins(
            claims_to_display['oid'], settings.AZURE_CONFIG.azure_aad_b2c_tenant)
    else:
        is_admin = False

    client_id = settings.AAD_CONFIG.client.client_id
    aad_link = "https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/Authentication/appId/" + client_id + "/isMSAApp/"

    item_count = 0
    try:
        cart_items = CartItem.objects.filter(cart_key=_get_cart_key(request))
        if cart_items:
            for cart_item in cart_items:
                item_count += cart_item.quantity
    except CartItem.DoesNotExist:
        item_count = 0

    script = return_insights_script(settings.AZURE_CONFIG.azure_insights.instrumentation_key)

    return dict(is_admin=is_admin, item_count=item_count, claims_to_display=claims_to_display,
                redirect_uri_external_link=request.build_absolute_uri(
                    reverse(settings.AAD_CONFIG.django.auth_endpoints.redirect)),
                aad_link=aad_link, insights_script=script)

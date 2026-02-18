from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.urls import reverse

from .models import LoveLetter

try:
    import mercadopago
except Exception:  # pragma: no cover
    mercadopago = None

try:
    import stripe
except Exception:  # pragma: no cover
    stripe = None


@dataclass
class PaymentLaunchResult:
    checkout_url: str
    external_id: str
    simulated: bool = False


def create_mercado_pago_checkout(request, letter: LoveLetter) -> PaymentLaunchResult:
    if not settings.MERCADO_PAGO_ACCESS_TOKEN or mercadopago is None:
        return PaymentLaunchResult(
            checkout_url=reverse("letters:simulate_payment", kwargs={"letter_id": str(letter.id), "method": "mercado_pago"}),
            external_id=f"sim-mp-{letter.id}",
            simulated=True,
        )

    sdk = mercadopago.SDK(settings.MERCADO_PAGO_ACCESS_TOKEN)
    preference_data = {
        "items": [
            {
                "title": "Carta de Amor Digital",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(letter.price),
            }
        ],
        "external_reference": str(letter.id),
        "back_urls": {"success": settings.MERCADO_PAGO_SUCCESS_URL, "failure": settings.MERCADO_PAGO_SUCCESS_URL},
        "auto_return": "approved",
    }
    preference_response = sdk.preference().create(preference_data)
    body = preference_response["response"]
    return PaymentLaunchResult(checkout_url=body["init_point"], external_id=str(body["id"]))


def create_stripe_checkout(request, letter: LoveLetter) -> PaymentLaunchResult:
    if not settings.STRIPE_SECRET_KEY or stripe is None:
        return PaymentLaunchResult(
            checkout_url=reverse("letters:simulate_payment", kwargs={"letter_id": str(letter.id), "method": "stripe"}),
            external_id=f"sim-st-{letter.id}",
            simulated=True,
        )

    stripe.api_key = settings.STRIPE_SECRET_KEY
    success_url = request.build_absolute_uri(reverse("letters:payment", kwargs={"letter_id": str(letter.id)})) + "?paid=1"
    cancel_url = request.build_absolute_uri(reverse("letters:payment", kwargs={"letter_id": str(letter.id)})) + "?canceled=1"
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "brl",
                    "product_data": {"name": "Carta de Amor Digital"},
                    "unit_amount": int(letter.price * 100),
                },
                "quantity": 1,
            }
        ],
        metadata={"letter_id": str(letter.id)},
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return PaymentLaunchResult(checkout_url=session.url, external_id=session.id)

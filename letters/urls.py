from django.urls import path

from . import views

app_name = "letters"

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("criar/etapa/<int:step>/", views.create_step, name="create_step"),
    path("preview/<uuid:letter_id>/", views.preview, name="preview"),
    path("pagamento/<uuid:letter_id>/", views.payment, name="payment"),
    path("pagamento/<uuid:letter_id>/simular/<str:method>/", views.simulate_payment, name="simulate_payment"),
    path("carta/<uuid:letter_id>/", views.public_letter, name="public_letter"),
    path("carta/<uuid:letter_id>/unlock/", views.unlock_letter, name="unlock_letter"),
    path("carta/<uuid:letter_id>/qr/", views.letter_qr, name="letter_qr"),
    path("webhooks/stripe/", views.stripe_webhook, name="stripe_webhook"),
    path("webhooks/mercadopago/", views.mercado_pago_webhook, name="mercado_pago_webhook"),
]

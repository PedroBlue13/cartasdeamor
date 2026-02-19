from django.contrib.auth import views as auth_views
from django.urls import path
from django.urls import reverse_lazy

from . import views

app_name = "letters"

urlpatterns = [
    path("", views.home, name="home"),
    path("health/", views.health, name="health"),
    path("conta/cadastro/", views.signup_view, name="signup"),
    path("conta/entrar/", views.login_view, name="login"),
    path("conta/sair/", views.logout_view, name="logout"),
    path("conta/perfil/", views.profile_view, name="profile"),
    path(
        "conta/recuperar-senha/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html",
            email_template_name="registration/password_reset_email.html",
            subject_template_name="registration/password_reset_subject.txt",
            success_url=reverse_lazy("letters:password_reset_done"),
        ),
        name="password_reset",
    ),
    path(
        "conta/recuperar-senha/enviado/",
        auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "conta/redefinir/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="registration/password_reset_confirm.html",
            success_url=reverse_lazy("letters:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    path(
        "conta/redefinir/concluido/",
        auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
        name="password_reset_complete",
    ),
    path("minhas-cartas/", views.history, name="history"),
    path("minhas-cartas/<uuid:letter_id>/excluir/", views.delete_letter, name="delete_letter"),
    path("fotos/<int:photo_id>/excluir/", views.delete_photo, name="delete_photo"),
    path("fotos/<int:photo_id>/modo/<str:mode>/", views.set_photo_mode, name="set_photo_mode"),
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

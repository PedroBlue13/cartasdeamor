from __future__ import annotations

import hashlib
import hmac
import json
import logging
import mimetypes
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.views import redirect_to_login
from django.http import FileResponse, Http404, HttpRequest, HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils._os import safe_join
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import (
    LoginForm,
    PasswordProtectionForm,
    ProfileForm,
    PhotoUploadForm,
    SignUpForm,
    Step1Form,
    Step2Form,
    Step3Form,
    Step5Form,
    StyledPasswordChangeForm,
    UnlockForm,
)
from .models import LoveLetter, LovePhoto, PaymentRecord
from .payments import create_mercado_pago_checkout, create_stripe_checkout
from .utils import build_pix_payload, detect_music_provider, generate_qr_base64, generate_qr_bytes, music_embed_url, spotify_deep_link

try:
    import stripe
except Exception:  # pragma: no cover
    stripe = None


WIZARD_STEPS = {1, 2, 3, 4, 5, 6}
logger = logging.getLogger(__name__)


def _current_letter_id(request: HttpRequest) -> str | None:
    return request.session.get("current_letter_id")


def _set_current_letter_id(request: HttpRequest, letter_id: str) -> None:
    request.session["current_letter_id"] = letter_id


def _get_current_letter_or_redirect(request: HttpRequest):
    letter_id = _current_letter_id(request)
    if not letter_id:
        return None
    try:
        queryset = LoveLetter.objects.filter(id=letter_id)
        if request.user.is_authenticated:
            queryset = queryset.filter(user=request.user)
        return queryset.first()
    except LoveLetter.DoesNotExist:
        return None


def _owner_required(request: HttpRequest, letter_id: str) -> LoveLetter:
    if not request.user.is_authenticated:
        raise Http404
    return get_object_or_404(LoveLetter, id=letter_id, user=request.user)


def home(request: HttpRequest) -> HttpResponse:
    examples = LoveLetter.objects.filter(is_paid=True)[:3]
    return render(request, "letters/home.html", {"examples": examples})


@require_http_methods(["GET", "POST"])
def signup_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("letters:history")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Conta criada com sucesso.")
        return redirect("letters:history")
    return render(request, "letters/signup.html", {"form": form})


@require_http_methods(["GET", "POST"])
def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect("letters:history")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        messages.success(request, "Sessão iniciada.")
        next_url = request.GET.get("next") or reverse("letters:history")
        return redirect(next_url)
    return render(request, "letters/login.html", {"form": form})


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, "Você saiu da sua conta.")
    return redirect("letters:home")


@require_GET
def history(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), login_url=reverse("letters:login"))
    letters = LoveLetter.objects.filter(user=request.user).prefetch_related("photos")
    return render(request, "letters/history.html", {"letters": letters})


@require_POST
def delete_letter(request: HttpRequest, letter_id: str) -> HttpResponse:
    letter = _owner_required(request, letter_id)
    letter.delete()
    messages.success(request, "Carta removida com sucesso.")
    return redirect("letters:history")


@require_POST
def delete_photo(request: HttpRequest, photo_id: int) -> HttpResponse:
    if not request.user.is_authenticated:
        raise Http404
    photo = get_object_or_404(LovePhoto, id=photo_id, letter__user=request.user)
    photo.delete()
    messages.success(request, "Foto removida com sucesso.")
    next_url = request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("letters:create_step", step=4)


@require_POST
def set_photo_mode(request: HttpRequest, photo_id: int, mode: str) -> HttpResponse:
    if not request.user.is_authenticated:
        raise Http404
    if mode not in {"contain", "cover"}:
        return HttpResponseForbidden("Modo invalido.")
    photo = get_object_or_404(LovePhoto, id=photo_id, letter__user=request.user)
    photo.display_mode = mode
    photo.save(update_fields=["display_mode"])
    messages.success(request, "Ajuste da foto atualizado.")
    next_url = request.GET.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("letters:create_step", step=4)


@require_http_methods(["GET", "POST"])
def profile_view(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), login_url=reverse("letters:login"))

    profile_form = ProfileForm(request.POST or None, instance=request.user, prefix="profile")
    password_form = StyledPasswordChangeForm(user=request.user, data=request.POST or None, prefix="password")

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "profile" and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Perfil atualizado com sucesso.")
            return redirect("letters:profile")
        if form_type == "password" and password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Senha alterada com sucesso.")
            return redirect("letters:profile")

    return render(
        request,
        "letters/profile.html",
        {"profile_form": profile_form, "password_form": password_form},
    )


@require_http_methods(["GET", "POST"])
def create_step(request: HttpRequest, step: int) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), login_url=reverse("letters:login"))

    if step not in WIZARD_STEPS:
        raise Http404("Etapa inválida")

    letter = _get_current_letter_or_redirect(request)
    if step > 1 and not letter:
        return redirect("letters:create_step", step=1)

    if step == 1:
        form = Step1Form(request.POST or None, instance=letter)
        if request.method == "POST" and form.is_valid():
            letter = form.save(commit=False)
            letter.user = request.user
            letter.save()
            _set_current_letter_id(request, str(letter.id))
            return redirect("letters:create_step", step=2)
        return render(request, "letters/wizard_step_1.html", {"form": form, "step": step})

    if step == 2:
        form = Step2Form(request.POST or None, instance=letter)
        if request.method == "POST" and form.is_valid():
            form.save()
            return redirect("letters:create_step", step=3)
        return render(request, "letters/wizard_step_2.html", {"form": form, "step": step, "letter": letter})

    if step == 3:
        form = Step3Form(request.POST or None, instance=letter)
        if request.method == "POST" and form.is_valid():
            form.save()
            return redirect("letters:create_step", step=4)
        return render(request, "letters/wizard_step_3.html", {"form": form, "step": step, "letter": letter})

    if step == 4:
        form = PhotoUploadForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            files = form.cleaned_data["photos"]
            try:
                for image in files:
                    LovePhoto.objects.create(letter=letter, image=image)
            except Exception:
                logger.exception("Erro ao salvar fotos da carta %s", letter.id)
                messages.error(
                    request,
                    "Nao foi possivel salvar as fotos agora. Tente novamente em alguns instantes.",
                )
                return render(
                    request,
                    "letters/wizard_step_4.html",
                    {"form": form, "step": step, "letter": letter, "photos": letter.photos.all()},
                    status=500,
                )
            if files:
                messages.success(request, f"{len(files)} foto(s) adicionada(s) com sucesso.")
            else:
                messages.info(request, "Nenhuma foto adicionada. Voce pode continuar sem fotos.")
            return redirect("letters:create_step", step=5)
        return render(
            request,
            "letters/wizard_step_4.html",
            {"form": form, "step": step, "letter": letter, "photos": letter.photos.all()},
        )

    if step == 5:
        form = Step5Form(request.POST or None, instance=letter)
        if request.method == "POST" and form.is_valid():
            letter = form.save(commit=False)
            letter.music_provider = detect_music_provider(letter.music_url)
            letter.save(update_fields=["music_url", "music_provider", "updated_at"])
            return redirect("letters:create_step", step=6)
        return render(request, "letters/wizard_step_5.html", {"form": form, "step": step, "letter": letter})

    password_form = PasswordProtectionForm(request.POST or None)
    if request.method == "POST" and password_form.is_valid():
        password = password_form.cleaned_data.get("password")
        letter.password_hash = make_password(password) if password else ""
        letter.save(update_fields=["password_hash", "updated_at"])
        messages.success(request, "Privacidade atualizada.")
        return redirect("letters:preview", letter_id=str(letter.id))
    return render(
        request,
        "letters/wizard_step_6.html",
        {
            "step": step,
            "letter": letter,
            "password_form": password_form,
            "music_embed": music_embed_url(letter.music_url, letter.music_provider),
        },
    )


@require_GET
def preview(request: HttpRequest, letter_id: str) -> HttpResponse:
    letter = _owner_required(request, letter_id)
    _set_current_letter_id(request, str(letter.id))
    return render(
        request,
        "letters/preview.html",
        {"letter": letter, "music_embed": music_embed_url(letter.music_url, letter.music_provider)},
    )


@require_http_methods(["GET", "POST"])
def payment(request: HttpRequest, letter_id: str) -> HttpResponse:
    letter = _owner_required(request, letter_id)

    pix_payload = build_pix_payload(
        key=settings.PIX_KEY,
        amount=Decimal(letter.price),
        description=f"Carta {letter.id}",
    )
    pix_qr_base64 = generate_qr_base64(pix_payload)

    if request.method == "POST":
        method = request.POST.get("method")
        if method == "pix":
            payment_record, _ = PaymentRecord.objects.get_or_create(letter=letter, method="pix", defaults={"amount": letter.price})
            payment_record.raw_payload = {"pix_payload": pix_payload}
            payment_record.save(update_fields=["raw_payload", "updated_at"])
            messages.info(request, "Use o PIX para concluir. Você pode simular confirmação abaixo.")
            return redirect("letters:payment", letter_id=str(letter.id))
        if method == "mercado_pago":
            launch = create_mercado_pago_checkout(request, letter)
            PaymentRecord.objects.create(
                letter=letter,
                method="mercado_pago",
                provider_payment_id=launch.external_id,
                amount=letter.price,
                status="pending",
                raw_payload={"simulated": launch.simulated},
            )
            return redirect(launch.checkout_url)
        if method == "stripe":
            launch = create_stripe_checkout(request, letter)
            PaymentRecord.objects.create(
                letter=letter,
                method="stripe",
                provider_payment_id=launch.external_id,
                amount=letter.price,
                status="pending",
                raw_payload={"simulated": launch.simulated},
            )
            return redirect(launch.checkout_url)
        return HttpResponseForbidden("Método inválido")

    public_link = request.build_absolute_uri(reverse("letters:public_letter", kwargs={"letter_id": str(letter.id)})) + "?auto_play=1"
    letter_qr = generate_qr_base64(public_link) if letter.is_paid else ""
    return render(
        request,
        "letters/payment.html",
        {
            "letter": letter,
            "pix_payload": pix_payload,
            "pix_qr_base64": pix_qr_base64,
            "public_link": public_link,
            "letter_qr": letter_qr,
        },
    )


@require_POST
def simulate_payment(request: HttpRequest, letter_id: str, method: str) -> HttpResponse:
    letter = _owner_required(request, letter_id)
    if method not in {"pix", "stripe", "mercado_pago"}:
        return HttpResponseForbidden("Método inválido")
    payment_record, _ = PaymentRecord.objects.get_or_create(letter=letter, method=method, defaults={"amount": letter.price})
    payment_record.status = "paid"
    payment_record.provider_payment_id = payment_record.provider_payment_id or f"sim-{method}-{letter.id}"
    payment_record.raw_payload = {"simulated": True, "confirmed_at": timezone.now().isoformat()}
    payment_record.save(update_fields=["status", "provider_payment_id", "raw_payload", "updated_at"])
    _mark_letter_paid(letter)
    return redirect("letters:payment", letter_id=str(letter.id))


def _mark_letter_paid(letter: LoveLetter) -> None:
    if not letter.is_paid:
        letter.is_paid = True
        letter.paid_at = timezone.now()
        letter.save(update_fields=["is_paid", "paid_at", "updated_at"])


@require_GET
def public_letter(request: HttpRequest, letter_id: str) -> HttpResponse:
    letter = get_object_or_404(LoveLetter, id=letter_id)
    if not letter.is_paid:
        return redirect("letters:payment", letter_id=str(letter.id))
    unlock_session_key = f"letter_unlocked_{letter.id}"
    if letter.password_hash and not request.session.get(unlock_session_key):
        return redirect("letters:unlock_letter", letter_id=str(letter.id))
    auto_play = request.GET.get("auto_play", "1") == "1"
    return render(
        request,
        "letters/public_letter.html",
        {
            "letter": letter,
            "music_embed": music_embed_url(letter.music_url, letter.music_provider),
            "spotify_deep_link": spotify_deep_link(letter.music_url) if letter.music_provider == "spotify" else "",
            "auto_play": auto_play,
        },
    )


@require_http_methods(["GET", "POST"])
def unlock_letter(request: HttpRequest, letter_id: str) -> HttpResponse:
    letter = get_object_or_404(LoveLetter, id=letter_id)
    if not letter.password_hash:
        return redirect("letters:public_letter", letter_id=str(letter.id))

    form = UnlockForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        password = form.cleaned_data["password"]
        if check_password(password, letter.password_hash):
            request.session[f"letter_unlocked_{letter.id}"] = True
            return redirect("letters:public_letter", letter_id=str(letter.id))
        form.add_error("password", "Senha inválida.")
    return render(request, "letters/unlock.html", {"form": form, "letter": letter})


@require_GET
def letter_qr(request: HttpRequest, letter_id: str) -> HttpResponse:
    letter = get_object_or_404(LoveLetter, id=letter_id)
    if not letter.is_paid:
        return HttpResponseForbidden("Pagamento pendente.")
    public_link = request.build_absolute_uri(reverse("letters:public_letter", kwargs={"letter_id": str(letter.id)})) + "?auto_play=1"
    image_bytes = generate_qr_bytes(public_link, box_size=10)
    response = HttpResponse(image_bytes, content_type="image/png")
    response["Content-Disposition"] = f'attachment; filename="carta-{letter.id}.png"'
    return response


@csrf_exempt
@require_POST
def stripe_webhook(request: HttpRequest) -> HttpResponse:
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    if settings.STRIPE_WEBHOOK_SECRET and stripe is not None:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except Exception:
            return HttpResponse(status=400)
    else:
        event = json.loads(payload.decode("utf-8") or "{}")

    event_type = event.get("type")
    if event_type == "checkout.session.completed":
        data_object = event.get("data", {}).get("object", {})
        letter_id = data_object.get("metadata", {}).get("letter_id")
        session_id = data_object.get("id")
        if letter_id:
            letter = LoveLetter.objects.filter(id=letter_id).first()
            if letter:
                PaymentRecord.objects.filter(provider_payment_id=session_id).update(status="paid")
                _mark_letter_paid(letter)
    return HttpResponse(status=200)


@csrf_exempt
@require_POST
def mercado_pago_webhook(request: HttpRequest) -> HttpResponse:
    body = request.body.decode("utf-8")
    received_sig = request.META.get("HTTP_X_SIGNATURE", "")
    if settings.MERCADO_PAGO_WEBHOOK_SECRET:
        expected = hmac.new(
            settings.MERCADO_PAGO_WEBHOOK_SECRET.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, received_sig):
            return HttpResponse(status=403)

    event = json.loads(body or "{}")
    external_reference = event.get("data", {}).get("external_reference") or event.get("external_reference")
    if external_reference:
        letter = LoveLetter.objects.filter(id=external_reference).first()
        if letter:
            PaymentRecord.objects.filter(letter=letter, method="mercado_pago").update(status="paid")
            _mark_letter_paid(letter)
    return HttpResponse(status=200)


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok", "time": datetime.utcnow().isoformat()})


@require_GET
def media_file(request: HttpRequest, file_path: str) -> HttpResponse:
    # Try current and legacy media roots to avoid broken links after deploy/storage changes.
    candidates: list[Path] = []
    for root in settings.MEDIA_FALLBACK_DIRS:
        try:
            candidates.append(Path(safe_join(root, file_path)))
        except Exception:
            continue

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            content_type, _ = mimetypes.guess_type(candidate.name)
            response = FileResponse(open(candidate, "rb"), content_type=content_type or "application/octet-stream")
            response["Cache-Control"] = "public, max-age=3600"
            return response

    raise Http404("Arquivo de midia nao encontrado.")

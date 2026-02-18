import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models


class LoveLetter(models.Model):
    REL_CHOICES = [
        ("ficando", "ficando"),
        ("namorando", "namorando"),
        ("noivos", "noivos"),
        ("casados", "casados"),
        ("apaixonados", "apaixonados"),
        ("outro", "outro"),
    ]
    TONE_CHOICES = [
        ("romantico", "romântico"),
        ("intenso", "intenso"),
        ("fofo", "fofo"),
        ("divertido", "divertido"),
    ]
    MUSIC_CHOICES = [
        ("youtube", "YouTube"),
        ("spotify", "Spotify"),
        ("apple_music", "Apple Music"),
        ("deezer", "Deezer"),
        ("amazon_music", "Amazon Music"),
        ("unknown", "Outro"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="love_letters",
        null=True,
        blank=True,
    )
    beloved_name = models.CharField(max_length=120)
    beloved_nickname = models.CharField(max_length=120, blank=True)
    sender_name = models.CharField(max_length=120, blank=True)
    relationship_status = models.CharField(max_length=20, choices=REL_CHOICES, blank=True)
    relationship_custom = models.CharField(max_length=120, blank=True)
    message = models.TextField(blank=True)
    tone = models.CharField(max_length=20, choices=TONE_CHOICES, default="romantico")
    music_url = models.URLField(blank=True)
    music_provider = models.CharField(max_length=20, choices=MUSIC_CHOICES, default="unknown")
    password_hash = models.CharField(max_length=255, blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(settings.LOVE_LETTER_PRICE))
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Carta para {self.beloved_name} ({self.id})"


class LovePhoto(models.Model):
    letter = models.ForeignKey(LoveLetter, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="letters/photos/")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]


class PaymentRecord(models.Model):
    METHOD_CHOICES = [
        ("pix", "PIX"),
        ("mercado_pago", "Mercado Pago"),
        ("stripe", "Stripe"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pendente"),
        ("paid", "Pago"),
        ("failed", "Falhou"),
    ]

    id = models.BigAutoField(primary_key=True)
    letter = models.ForeignKey(LoveLetter, on_delete=models.CASCADE, related_name="payments")
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    provider_payment_id = models.CharField(max_length=120, blank=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal(settings.LOVE_LETTER_PRICE))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

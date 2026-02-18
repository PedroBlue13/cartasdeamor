from django.contrib import admin

from .models import LoveLetter, LovePhoto, PaymentRecord


@admin.register(LoveLetter)
class LoveLetterAdmin(admin.ModelAdmin):
    list_display = ("id", "beloved_name", "sender_name", "is_paid", "price", "created_at")
    list_filter = ("is_paid", "relationship_status", "tone", "music_provider")
    search_fields = ("beloved_name", "sender_name", "message")


@admin.register(LovePhoto)
class LovePhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "letter", "created_at")


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "letter", "method", "status", "amount", "provider_payment_id", "created_at")
    list_filter = ("method", "status")

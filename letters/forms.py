from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.contrib.auth.models import User
from PIL import Image

from .models import LoveLetter


BASE_INPUT_CLASS = (
    "w-full rounded-2xl border border-base-300 bg-base-200 px-4 py-3 text-base-500 "
    "placeholder-base-400 focus:border-love-300 focus:outline-none focus:ring-2 focus:ring-love-400/50"
)


class StyledFormMixin:
    def _style_fields(self) -> None:
        for field in self.fields.values():
            if isinstance(field.widget, (forms.TextInput, forms.URLInput, forms.PasswordInput, forms.Textarea)):
                field.widget.attrs["class"] = BASE_INPUT_CLASS
            if isinstance(field.widget, forms.Select):
                field.widget.attrs["class"] = BASE_INPUT_CLASS


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]

        cleaned_files = []
        errors = []
        for uploaded in data:
            try:
                cleaned = single_clean(uploaded, initial)
                image = Image.open(cleaned)
                image.verify()
                cleaned.seek(0)
                cleaned_files.append(cleaned)
            except Exception:
                errors.append(forms.ValidationError("Envie apenas arquivos de imagem válidos."))
        if errors:
            raise forms.ValidationError(errors)
        return cleaned_files


class Step1Form(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = LoveLetter
        fields = ["beloved_name"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["beloved_name"].widget.attrs["placeholder"] = "Nome do seu amor"
        self._style_fields()


class Step2Form(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = LoveLetter
        fields = ["beloved_nickname", "sender_name", "relationship_status", "relationship_custom"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["beloved_nickname"].widget.attrs["placeholder"] = "Meu bem, meu amor..."
        self.fields["sender_name"].widget.attrs["placeholder"] = "Seu nome (opcional)"
        self.fields["relationship_custom"].widget.attrs["placeholder"] = "Descreva o status"
        self._style_fields()

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("relationship_status")
        custom = cleaned_data.get("relationship_custom")
        if status == "outro" and not custom:
            self.add_error("relationship_custom", "Descreva o status quando selecionar 'outro'.")
        return cleaned_data


class Step3Form(StyledFormMixin, forms.ModelForm):
    message = forms.CharField(
        required=True,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 8, "maxlength": 2000, "id": "id_message"}),
    )

    class Meta:
        model = LoveLetter
        fields = ["message", "tone"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class PhotoUploadForm(StyledFormMixin, forms.Form):
    photos = MultipleImageField(
        required=False,
        widget=MultipleFileInput(attrs={"multiple": True, "accept": "image/*", "class": BASE_INPUT_CLASS}),
    )

    def __init__(self, *args, **kwargs):
        self.max_files = kwargs.pop("max_files", 6)
        self.max_size_mb = kwargs.pop("max_size_mb", 5)
        super().__init__(*args, **kwargs)

    def clean_photos(self):
        files = self.cleaned_data.get("photos", [])
        if len(files) > self.max_files:
            raise forms.ValidationError(f"Envie no máximo {self.max_files} fotos.")
        for image in files:
            if image.size > self.max_size_mb * 1024 * 1024:
                raise forms.ValidationError(f"Cada foto deve ter até {self.max_size_mb}MB.")
        return files


class Step5Form(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = LoveLetter
        fields = ["music_url"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["music_url"].widget.attrs["placeholder"] = (
            "Cole uma URL do YouTube, Spotify, Apple Music, Deezer ou Amazon Music"
        )
        self._style_fields()


class PasswordProtectionForm(StyledFormMixin, forms.Form):
    password = forms.CharField(
        required=False,
        min_length=4,
        widget=forms.PasswordInput(attrs={"placeholder": "Senha (opcional, mínimo 4 caracteres)"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class UnlockForm(StyledFormMixin, forms.Form):
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={"placeholder": "Digite a senha da carta"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class SignUpForm(StyledFormMixin, UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "Seu usuario"
        self.fields["email"].widget.attrs["placeholder"] = "Seu email (opcional)"
        self.fields["password1"].widget.attrs["placeholder"] = "Senha"
        self.fields["password2"].widget.attrs["placeholder"] = "Confirmar senha"
        self._style_fields()


class LoginForm(StyledFormMixin, AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Usuario"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"placeholder": "Senha"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style_fields()


class ProfileForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "Seu usuario"
        self.fields["email"].widget.attrs["placeholder"] = "Seu email"
        self._style_fields()


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].widget.attrs["placeholder"] = "Senha atual"
        self.fields["new_password1"].widget.attrs["placeholder"] = "Nova senha"
        self.fields["new_password2"].widget.attrs["placeholder"] = "Confirmar nova senha"
        self._style_fields()

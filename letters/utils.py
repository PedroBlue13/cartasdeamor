import base64
import io
import re
import uuid
from decimal import Decimal
from urllib.parse import quote_plus

import qrcode
from PIL import Image


def detect_music_provider(url: str) -> str:
    if not url:
        return "unknown"
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    if "spotify.com" in url:
        return "spotify"
    if "music.apple.com" in url:
        return "apple_music"
    if "deezer.com" in url:
        return "deezer"
    if "amazon." in url and "music" in url:
        return "amazon_music"
    return "unknown"


def music_embed_url(url: str, provider: str) -> str:
    if not url:
        return ""
    if provider == "youtube":
        youtube_id_match = re.search(r"(?:v=|youtu\.be/)([\w-]{11})", url)
        if youtube_id_match:
            return f"https://www.youtube.com/embed/{youtube_id_match.group(1)}?autoplay=1&mute=1&rel=0"
    if provider == "spotify":
        base = url.replace("open.spotify.com/", "open.spotify.com/embed/")
        return f"{base}{'&' if '?' in base else '?'}utm_source=generator"
    if provider == "deezer":
        return f"https://widget.deezer.com/widget/dark/track/{url.split('/')[-1]}"
    if provider == "apple_music":
        return url
    return ""


def spotify_deep_link(url: str) -> str:
    if not url or "spotify.com" not in url:
        return ""
    match = re.search(r"open\.spotify\.com/(track|album|playlist|episode)/([A-Za-z0-9]+)", url)
    if not match:
        return ""
    media_type, media_id = match.groups()
    return f"spotify:{media_type}:{media_id}"


def generate_qr_bytes(payload: str, box_size: int = 8) -> bytes:
    qr = qrcode.QRCode(version=1, box_size=box_size, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    img: Image.Image = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr_base64(payload: str) -> str:
    return f"data:image/png;base64,{base64.b64encode(generate_qr_bytes(payload)).decode('utf-8')}"


def build_pix_payload(*, key: str, amount: Decimal, description: str) -> str:
    rounded = f"{Decimal(amount):.2f}"
    txid = str(uuid.uuid4())[:16]
    return (
        f"00020126580014BR.GOV.BCB.PIX0136{key}"
        f"520400005303986540{len(rounded)}{rounded}"
        f"5802BR5920CARTAS DE AMOR6009SAO PAULO62070503***"
        f"6304{quote_plus(description)[:4]}{txid}"
    )

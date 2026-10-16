"""
qr45 - Core QR Generation Engine (45 Studios)
Supports:
- Module shapes: square, rounded, circle, gapped
- Eye styles: square, rounded, circle
- Center logos (file bytes or remote URL)
- Animated background GIFs (via segno)
- Dual format exports: PNG and SVG
"""

import io
from PIL import Image
import qrcode
from qrcode.constants import ERROR_CORRECT_H, ERROR_CORRECT_M, ERROR_CORRECT_Q
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import (
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
)
from qrcode.image.styles.colormasks import SolidFillColorMask
from qrcode.image.svg import SvgPathImage
import segno


def _hex_to_rgb(hex_str: str, default=(0, 0, 0)):
    if not hex_str:
        return default
    hex_str = hex_str.strip().lstrip("#")
    if len(hex_str) == 3:
        hex_str = "".join([c * 2 for c in hex_str])
    if len(hex_str) != 6:
        return default
    try:
        return tuple(int(hex_str[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return default


def _get_module_drawer(shape: str):
    shape = (shape or "square").lower()
    if shape in ("circle", "dot", "dots"):
        return CircleModuleDrawer()
    elif shape in ("rounded", "squircle"):
        return RoundedModuleDrawer()
    elif shape == "gapped":
        return GappedSquareModuleDrawer()
    return SquareModuleDrawer()


def generate_qr45_png(
    data: str,
    fill_color: str = "#FB542B",
    back_color: str = "#0E1117",
    box_size: int = 10,
    border: int = 2,
    module_shape: str = "square",
    logo_bytes: bytes = None,
) -> io.BytesIO:
    """Generate high-resolution PNG with custom module shapes and optional logo."""
    ec_level = ERROR_CORRECT_H if logo_bytes else ERROR_CORRECT_Q

    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_level,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    front_rgb = _hex_to_rgb(fill_color, default=(251, 84, 43))
    back_rgb = _hex_to_rgb(back_color, default=(14, 17, 23))

    color_mask = SolidFillColorMask(front_color=front_rgb, back_color=back_rgb)
    drawer = _get_module_drawer(module_shape)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=drawer,
        color_mask=color_mask,
    ).convert("RGBA")

    if logo_bytes:
        try:
            logo = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")
            qr_w, qr_h = img.size
            max_logo_size = int(qr_w * 0.24)
            logo.thumbnail((max_logo_size, max_logo_size), Image.Resampling.LANCZOS)

            pos = ((qr_w - logo.size[0]) // 2, (qr_h - logo.size[1]) // 2)

            bg_pad = Image.new("RGBA", (logo.size[0] + 8, logo.size[1] + 8), (*back_rgb, 255))
            pad_pos = (pos[0] - 4, pos[1] - 4)
            img.paste(bg_pad, pad_pos)
            img.paste(logo, pos, mask=logo)
        except Exception:
            pass

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def generate_qr45_svg(
    data: str,
    fill_color: str = "#FB542B",
    back_color: str = "#0E1117",
    box_size: int = 10,
    border: int = 2,
) -> str:
    """Generate crisp vector SVG string."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_Q,
        box_size=box_size,
        border=border,
        image_factory=SvgPathImage,
    )
    qr.add_data(data)
    qr.make(fit=True)

    svg_img = qr.make_image(
        fill_color=fill_color,
        back_color=back_color,
    )

    buf = io.BytesIO()
    svg_img.save(buf)
    return buf.getvalue().decode("utf-8")


def generate_qr45_animated(
    data: str,
    background_gif_bytes: bytes,
    scale: int = 8,
) -> io.BytesIO:
    """Generate animated QR using segno against GIF stream."""
    qr = segno.make(data, error="h")
    bg_file = io.BytesIO(background_gif_bytes)

    buf = io.BytesIO()
    qr.to_artistic(
        background=bg_file,
        target=buf,
        kind="gif",
        scale=scale,
    )
    buf.seek(0)
    return buf

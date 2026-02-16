import re


FALLBACK_DARK_COLOR = "#2563EB"
FALLBACK_LIGHT_COLOR = "#60A5FA"
HEX_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")


def normalize_hex(color: str | None) -> str:
    if not color:
        return ""

    normalized = color.strip()
    if not normalized:
        return ""

    if not normalized.startswith("#"):
        normalized = f"#{normalized}"

    if not HEX_COLOR_RE.fullmatch(normalized):
        return ""

    return normalized.upper()


def lighten_hex(hex_color: str, amount: float = 0.55) -> str:
    normalized = normalize_hex(hex_color)
    if not normalized:
        normalized = FALLBACK_DARK_COLOR

    bounded_amount = max(0.0, min(1.0, amount))

    red = int(normalized[1:3], 16)
    green = int(normalized[3:5], 16)
    blue = int(normalized[5:7], 16)

    light_red = round(red + (255 - red) * bounded_amount)
    light_green = round(green + (255 - green) * bounded_amount)
    light_blue = round(blue + (255 - blue) * bounded_amount)

    return f"#{light_red:02X}{light_green:02X}{light_blue:02X}"


from homeassistant.core import HomeAssistant
from .dictionaries import (
    BASE_SYNONYMS,
    AUTO_TRANSLATE,
    PURIFIER_MODES,
    HUMIDIFIER_FAN_LEVELS,
    HUMIDIFIER_MODES,
    LIGHT_COLORS,
    LIGHT_COLOR_TEMP,
    LIGHT_EFFECTS,
    LIGHT_BRIGHTNESS,
    STATE_QUERY_KEYWORDS,
    SPLITTERS,
    STATE_STOP_WORDS,
    MEDIA_KEYWORDS,
    MEDIA_STOP_KEYWORDS,
    MEDIA_TYPES,
    YANDEX_SPECIAL,
    MEDIA_STOP_WORDS,
VOLUME_KEYWORDS,
)


def detect_command_type(tokens: list[str]) -> str:
    has_state_query = any(t in STATE_QUERY_KEYWORDS for t in tokens)
    has_media = any(t in MEDIA_KEYWORDS for t in tokens)
    has_media_stop = any(t in MEDIA_STOP_KEYWORDS for t in tokens)
    has_volume = any(t in VOLUME_KEYWORDS for t in tokens)

    if has_state_query:
        return "state_query"
    if has_media or has_media_stop or has_volume:
        return "music"
    return "device"


def extract_state_query(tokens: list[str]) -> str | None:
    query_tokens = [t for t in tokens if t not in STATE_STOP_WORDS and len(t) > 2]
    return " ".join(query_tokens) if query_tokens else None


def extract_number(tokens: list[str]) -> int | None:
    for token in tokens:
        clean = token.rstrip("%")
        if clean.isdigit():
            return int(clean)
    return None


def extract_preset_mode(tokens: list[str], domain: str) -> str | None:
    if domain == "fan":
        for token in tokens:
            if token in PURIFIER_MODES:
                return PURIFIER_MODES[token]
    if domain == "select":
        for token in tokens:
            if token in HUMIDIFIER_FAN_LEVELS:
                return HUMIDIFIER_FAN_LEVELS[token]
    if domain == "humidifier":
        for token in tokens:
            if token in HUMIDIFIER_MODES:
                return HUMIDIFIER_MODES[token]
    return None


def extract_light_params(tokens: list[str]) -> dict:
    """Извлекаем параметры лампы из токенов"""
    params = {}

    for token in tokens:
        if token in LIGHT_COLORS:
            r, g, b = LIGHT_COLORS[token]
            params["hs_color"] = _rgb_to_hs(r, g, b)
            return params

    for token in tokens:
        if token in LIGHT_COLOR_TEMP:
            params["color_temp_kelvin"] = LIGHT_COLOR_TEMP[token]
            return params

    for token in tokens:
        if token in LIGHT_EFFECTS:
            params["effect"] = LIGHT_EFFECTS[token]
            return params

    for token in tokens:
        if token in LIGHT_BRIGHTNESS:
            params["brightness"] = LIGHT_BRIGHTNESS[token]
            return params

    number = extract_number(tokens)
    if number:
        params["brightness"] = int(number * 2.55)

    return params


def extract_media_info(tokens: list[str]) -> dict:
    """Извлекаем информацию о медиа из токенов"""
    result = {
        "media_id": None,
        "media_type": None,
    }

    text = " ".join(tokens)
    for key, value in YANDEX_SPECIAL.items():
        if key in text:
            result["media_id"] = value
            result["media_type"] = "playlist"
            return result

    for token in tokens:
        if token in MEDIA_TYPES:
            result["media_type"] = MEDIA_TYPES[token]
            break

    title_tokens = [t for t in tokens if t not in MEDIA_STOP_WORDS and len(t) > 1]
    if title_tokens:
        result["media_id"] = " ".join(title_tokens)

    return result


def _rgb_to_hs(r: int, g: int, b: int) -> tuple[float, float]:
    """Конвертируем RGB в HS (Hue, Saturation)"""
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    diff = max_c - min_c

    if diff == 0:
        h = 0
    elif max_c == r:
        h = (60 * ((g - b) / diff) + 360) % 360
    elif max_c == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    else:
        h = (60 * ((r - g) / diff) + 240) % 360

    s = 0 if max_c == 0 else (diff / max_c) * 100
    return round(h, 1), round(s, 1)


def build_action_index(hass: HomeAssistant) -> dict[str, str]:
    index = dict(BASE_SYNONYMS)
    services = hass.services.async_services()
    for domain_services in services.values():
        for service in domain_services:
            if service in AUTO_TRANSLATE:
                for synonym in AUTO_TRANSLATE[service]:
                    index[synonym] = service
    return index


def find_action(tokens: list[str], action_index: dict[str, str]) -> str | None:
    for token in tokens:
        if token in action_index:
            return action_index[token]
    return None


def split_commands(text: str) -> list[str]:
    for splitter in SPLITTERS:
        text = text.replace(f" {splitter} ", "|")
    return [t.strip() for t in text.split("|")]
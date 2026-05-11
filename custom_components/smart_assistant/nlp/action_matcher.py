from homeassistant.core import HomeAssistant

MEDIA_KEYWORDS = ["музыку", "музыка", "песню", "песня", "трек", "сыграть"]

STATE_QUERY_KEYWORDS = [
    "какой", "какая", "какое", "сколько", "что",
    "температура", "влажность", "состояние", "статус",
    "включён", "выключен", "работает", "показывает"
]

BASE_SYNONYMS = {
    "включить": "turn_on",
    "включать": "turn_on",
    "врубить": "turn_on",
    "запустить": "turn_on",
    "активировать": "turn_on",
    "выключить": "turn_off",
    "выключать": "turn_off",
    "вырубить": "turn_off",
    "отключить": "turn_off",
    "остановить": "turn_off",
    "убавить": "volume_down",
    "приглушить": "volume_down",
    "потише": "volume_down",
    "громче": "volume_up",
    "прибавить": "volume_up",
    "погромче": "volume_up",
    "пауза": "media_pause",
    "играть": "play_media",
    "сыграть": "play_media",
    "воспроизвести": "play_media",
    "следующий": "media_next_track",
    "предыдущий": "media_previous_track",
    "стоп": "media_stop",
    "переключить": "toggle",
}

AUTO_TRANSLATE = {
    "turn_on": ["включить", "врубить", "запустить"],
    "turn_off": ["выключить", "вырубить", "отключить"],
    "volume_up": ["громче", "прибавить", "погромче"],
    "volume_down": ["тише", "убавить", "приглушить"],
    "media_pause": ["пауза"],
    "media_play": ["продолжить"],
    "play_media": ["играть", "сыграть", "воспроизвести"],
    "media_next_track": ["следующий", "дальше"],
    "toggle": ["переключить"],
    "set_percentage": ["установить", "поставить"],
    "set_preset_mode": ["режим"],
}

SPLITTERS = ["и", "а также", "потом", "затем", "а ещё"]


def detect_command_type(tokens: list[str]) -> str:
    """Определяем тип команды: device / music / state_query"""
    has_media = any(t in MEDIA_KEYWORDS for t in tokens)
    has_state_query = any(t in STATE_QUERY_KEYWORDS for t in tokens)
    has_action = any(t in BASE_SYNONYMS for t in tokens)

    if has_state_query and not has_action:
        return "state_query"
    if has_media or any(t in ("играть", "сыграть", "воспроизвести") for t in tokens):
        return "music"
    return "device"


def extract_state_query(tokens: list[str]) -> str | None:
    """Извлекаем объект запроса состояния"""
    STOP_WORDS = {"какой", "какая", "какое", "сколько", "что", "у", "в", "на", "сейчас"}
    query_tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
    return " ".join(query_tokens) if query_tokens else None


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
    has_media = any(t in MEDIA_KEYWORDS for t in tokens)
    for token in tokens:
        if token in action_index:
            service = action_index[token]
            if has_media and service == "turn_on":
                return "play_media"
            return service
    return None


def extract_media_title(tokens: list[str]) -> str | None:
    STOP_WORDS = {
        "включить", "включи", "сыграть", "сыграй", "играть",
        "воспроизвести", "поставить", "алиса", "станция",
        "колонка", "яндекс", "музыку", "музыка", "песню",
        "на", "у", "в", "по", "трек"
    }
    title_tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 1]
    return " ".join(title_tokens) if title_tokens else None


def split_commands(text: str) -> list[str]:
    for splitter in SPLITTERS:
        text = text.replace(f" {splitter} ", "|")
    return [t.strip() for t in text.split("|")]
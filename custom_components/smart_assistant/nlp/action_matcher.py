from homeassistant.core import HomeAssistant

BASE_SYNONYMS = {
    # Включить
    "включить":     "turn_on",
    "включать":     "turn_on",
    "врубить":      "turn_on",
    "запустить":    "turn_on",
    "активировать": "turn_on",

    # Выключить
    "выключить": "turn_off",
    "выключать": "turn_off",
    "вырубить":  "turn_off",
    "отключить": "turn_off",
    "остановить": "turn_off",

    # Громкость
    "убавить":    "volume_down",
    "приглушить": "volume_down",
    "потише":     "volume_down",
    "громче":     "volume_up",
    "прибавить":  "volume_up",
    "погромче":   "volume_up",

    # Медиа
    "пауза":      "media_pause",
    "играть":     "media_play",
    "следующий":  "media_next_track",
    "предыдущий": "media_previous_track",
    "стоп":       "media_stop",

    # Переключить
    "переключить": "toggle",
}

AUTO_TRANSLATE = {
    "turn_on":          ["включить", "врубить", "запустить"],
    "turn_off":         ["выключить", "вырубить", "отключить"],
    "volume_up":        ["громче", "прибавить", "погромче"],
    "volume_down":      ["тише", "убавить", "приглушить"],
    "media_pause":      ["пауза", "стоп"],
    "media_play":       ["играть", "продолжить"],
    "media_next_track": ["следующий", "дальше"],
    "toggle":           ["переключить"],
    "set_percentage":   ["установить", "поставить"],
    "set_preset_mode":  ["режим"],
}

SPLITTERS = ["и", "а также", "потом", "затем", "а ещё"]


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
BASE_SYNONYMS = {
    # Включить
    "включить":     "turn_on",
    "включать":     "turn_on",
    "врубить":      "turn_on",
    "запустить":    "turn_on",
    "активировать": "turn_on",

    # Выключить
    "выключить":  "turn_off",
    "выключать":  "turn_off",
    "вырубить":   "turn_off",
    "отключить":  "turn_off",
    "остановить": "turn_off",

    # Переключить
    "переключить": "toggle",

    # Режим
    "режим":      "set_preset_mode",
    "поставить":  "set_preset_mode",
    "установить": "set_preset_mode",

    # Влажность
    "влажность": "set_humidity",

    # Скорость
    "скорость": "set_percentage",
    "мощность": "set_percentage",
}

AUTO_TRANSLATE = {
    "turn_on":         ["включить", "врубить", "запустить"],
    "turn_off":        ["выключить", "вырубить", "отключить"],
    "toggle":          ["переключить"],
    "set_preset_mode": ["режим", "поставить", "установить"],
    "set_humidity":    ["влажность"],
    "set_percentage":  ["скорость", "мощность"],
}
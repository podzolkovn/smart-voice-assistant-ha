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

    # Лампа — яркость
    "ярче":    "light_brightness_up",
    "темнее":  "light_brightness_down",
    "яркость": "light_set_brightness",

    # Лампа — цвет
    "цвет":    "light_set_color",
    "покрась": "light_set_color",

    # Лампа — эффект
    "эффект":  "light_set_effect",
    "режим":   "light_set_effect",
}

AUTO_TRANSLATE = {
    "turn_on":              ["включить", "врубить", "запустить"],
    "turn_off":             ["выключить", "вырубить", "отключить"],
    "toggle":               ["переключить"],
    "set_preset_mode":      ["режим", "поставить", "установить"],
    "set_humidity":         ["влажность"],
    "set_percentage":       ["скорость", "мощность"],
    "light_brightness_up":  ["ярче", "светлее"],
    "light_brightness_down":["темнее", "приглуши"],
    "light_set_brightness": ["яркость"],
    "light_set_color":      ["цвет", "покрась", "сделай"],
    "light_set_effect":     ["эффект"],
}
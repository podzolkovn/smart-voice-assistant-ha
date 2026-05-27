'''
Словарь синонимов для действий (на русском языке)
'''
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

    # Музыка
    "играть":        "ma_play",
    "сыграть":       "ma_play",
    "воспроизвести": "ma_play",
    "стоп":          "media_stop",
    "замолчи":       "media_pause",
    "останови":      "media_pause",
    "хватит":        "media_pause",
    "тихо":          "media_pause",

    # Громкость (нормальные формы после pymorphy3)
    "громкость":    "volume_set",   # громкость → громкость
    "громкий":      "volume_up",    # громче/погромче → громкий
    "тихий":        "volume_down",  # тише/потише → тихий
    "прибавить":    "volume_up",    # прибавь → прибавить
    "убавить":      "volume_down",  # убавь → убавить
}

AUTO_TRANSLATE = {
    "turn_on":              ["включить", "врубить", "запустить"],
    "turn_off":             ["выключить", "вырубить", "отключить"],
    "toggle":               ["переключить"],
    "set_preset_mode":      ["режим", "поставить", "установить"],
    "set_humidity":         ["влажность"],
    "set_percentage":       ["скорость", "мощность"],
    "light_brightness_up":  ["ярче", "светлее"],
    "light_brightness_down": ["темнее", "приглуши"],
    "light_set_brightness": ["яркость"],
    "light_set_color":      ["цвет", "покрась", "сделай"],
    "light_set_effect":     ["эффект"],
    "ma_play":              ["играть", "сыграть", "воспроизвести"],
    "volume_set":           ["громкость"],
    "volume_up":            ["громкий", "прибавить"],    # громче → громкий
    "volume_down":          ["тихий", "убавить"],        # тише → тихий
}

# Именованные уровни громкости (0.0 – 1.0)
VOLUME_LEVELS = {
    "максимальный": 1.0,    # максимальная → максимальный
    "максимум":     1.0,
    "полный":       1.0,    # полная → полный
    "полностью":    1.0,
    "высокий":      0.8,    # высокая → высокий
    "средний":      0.5,    # средняя → средний
    "половина":     0.5,
    "низкий":       0.3,    # низкая → низкий
    "минимальный":  0.1,    # минимальная → минимальный
    "минимум":      0.1,
    "тихий":        0.2,    # тихая → тихий (но тихий уже volume_down — осторожно)
}

''' 
Словарь синонимов для действий (на казахском языке) 
'''
BASE_SYNONYMS_KZ = {
    # Включить
    "қосу":     "turn_on",
    "қос":     "turn_on",
    "іске қосу":   "turn_on",
    "жүргізу":    "turn_on",

    # Выключить
    "өшіру":  "turn_off",
    "өшір":  "turn_off",
    "тоқтату": "turn_off",
    "тоқтат": "turn_off",

    # Переключить
    "ауыстыру": "toggle",
    "aуыстырыңыз": "toggle",
    "ауыстыр": "toggle",
    "аудар": "toggle",

    # Режим
    "режим":      "set_preset_mode",
    "қою":  "set_preset_mode",
    "қойдыру":  "set_preset_mode",

    # Влажность
    "ылғалдылық": "set_humidity",

    # Скорость
    "жылдамдық": "set_percentage",
    "қуат": "set_percentage",

    # Лампа — яркость
    "анық":    "light_brightness_up",
    "қараю":  "light_brightness_down",
    "жарықтық": "light_set_brightness",

    # Лампа — цвет
    "түс":    "light_set_color",
    "бояу": "light_set_color",

    # Лампа — эффект
    "нәтиже":  "light_set_effect",

    # Музыка
    "ойнау":        "ma_play",
    "жаңғырту": "ma_play",
    "стоп":          "media_stop",
    "үндемей қал":       "media_pause",
    "тоқтат":      "media_pause",
    "жетер":        "media_pause",
    "тыныш":          "media_pause",

    # Громкость (нормальные формы после pymorphy3)
    "дыбыс":    "volume_set",   # громкость → громкость
    "қатты":      "volume_up",    # громче/погромче → громкий
    "ақырын":        "volume_down",  # тише/потише → тихий
}

AUTO_TRANSLATE_KZ = {
    "turn_on":              ["қосу", "қос", "іске қосу", "жүргізу"],
    "turn_off":             ["өшіру", "өшір", "тоқтату", "тоқтат"],
    "toggle":               ["ауыстыру", "aуыстырыңыз", "ауыстыр", "аудар"],
    "set_preset_mode":      ["режим", "қою", "қойдыру"],
    "set_humidity":         ["ылғалдылық"],
    "set_percentage":       ["жылдамдық", "қуат"],
    "light_brightness_up":  ["анық"],
    "light_brightness_down": ["қараю"],
    "light_set_brightness": ["жарықтық"],
    "light_set_color":      ["түс", "бояу"],
    "light_set_effect":     ["нәтиже"],
    "ma_play":              ["ойнау", "жаңғырту"],
    "volume_set":           ["дыбыс"],
    "volume_up":            ["қатты"],    # громче → громкий
    "volume_down":          ["ақырын"],        # тише → тихий
}

# Именованные уровни громкости (0.0 – 1.0)
VOLUME_LEVELS_KZ = {
    "максималды": 1.0,    # максимальная → максимальный
    "максимум":     1.0,
    "толы":       1.0,    # полная → полный
    "толық":    1.0,
    "жоғары":      0.8,    # высокая → высокий
    "орташа":      0.5,    # средняя → средний
    "жартысы":     0.5,
    "төмен":       0.3,    # низкая → низкий
    "минималды":  0.1,    # минимальная → минимальный
    "минимум":      0.1,
    "тыныш":        0.2,    # тихая → тихий (но тихий уже volume_down — осторожно)
}


'''
Словарь синонимов для действий (на английском языке)
'''
BASE_SYNONYMS_EN = {
    # Turn on
    "turn on":         "turn_on",
    "switch on":       "turn_on",
    "activate":        "turn_on",
    "start":           "turn_on",

    # Turn off
    "turn off":        "turn_off",
    "switch off":      "turn_off",
    "shut down":       "turn_off",
    "stop":            "turn_off",
    "deactivate":      "turn_off",

    # Toggle
    "toggle":          "toggle",

    # Preset mode
    "mode":            "set_preset_mode",
    "set mode":        "set_preset_mode",
    "preset":          "set_preset_mode",

    # Humidity
    "humidity":        "set_humidity",

    # Percentage / speed
    "speed":           "set_percentage",
    "power":           "set_percentage",

    # Light brightness
    "brighter":        "light_brightness_up",
    "darker":          "light_brightness_down",
    "brightness":      "light_set_brightness",

    # Light color
    "color":           "light_set_color",
    "paint":           "light_set_color",
    "set color":       "light_set_color",

    # Light effect
    "effect":          "light_set_effect",

    # Music
    "play":            "ma_play",
    "start music":     "ma_play",
    "play music":      "ma_play",
    "stop music":      "media_stop",
    "pause":           "media_pause",
    "mute":            "media_pause",

    # Volume
    "volume":          "volume_set",
    "louder":          "volume_up",
    "quieter":         "volume_down",
    "increase volume": "volume_up",
    "decrease volume": "volume_down",
}

AUTO_TRANSLATE_EN = {
    "turn_on":              ["turn on", "switch on", "start"],
    "turn_off":             ["turn off", "switch off", "shut down"],
    "toggle":               ["toggle"],
    "set_preset_mode":      ["mode", "set mode", "preset"],
    "set_humidity":         ["humidity"],
    "set_percentage":       ["speed", "power"],
    "light_brightness_up":  ["brighter", "increase brightness"],
    "light_brightness_down": ["darker", "decrease brightness"],
    "light_set_brightness": ["brightness"],
    "light_set_color":      ["color", "paint", "set color"],
    "light_set_effect":     ["effect"],
    "ma_play":              ["play", "start music", "play music"],
    "media_stop":           ["stop music", "stop"],
    "media_pause":          ["pause", "mute"],
    "volume_set":           ["volume"],
    "volume_up":            ["louder", "increase volume"],
    "volume_down":          ["quieter", "decrease volume"],
}

# Named volume levels (0.0 – 1.0)
VOLUME_LEVELS_EN = {
    "maximum": 1.0,
    "max":     1.0,
    "full":    1.0,
    "high":    0.8,
    "medium":  0.5,
    "half":    0.5,
    "low":     0.3,
    "minimum": 0.1,
    "min":     0.1,
    "quiet":   0.2,
}

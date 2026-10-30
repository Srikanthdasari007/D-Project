# Telugu calendar data extracted from the 2026 and 2027 PDFs
#
# Add verified information from the PDFs to this structure.
# Do not enter guessed dates or Panchangam details.

TELUGU_CALENDAR_DATA = {
    2026: {
        1: {
            "month_name": "జనవరి",
            "days": {
                # Example structure:
                # 1: {
                #     "tithi": "Verified Telugu Tithi",
                #     "nakshatram": "Verified Nakshatram",
                #     "festivals": ["Verified festival"],
                #     "is_amavasya": False,
                #     "is_poornima": False,
                # },
            },
        },
    },
    2027: {
        1: {
            "month_name": "జనవరి",
            "days": {},
        },
    },
}

# Telugu weekday names, beginning with Sunday.
TELUGU_WEEKDAYS = [
    "ఆది",
    "సోమ",
    "మంగళ",
    "బుధ",
    "గురు",
    "శుక్ర",
    "శని",
]

# Telugu interface labels.
TELUGU_LABELS = {
    "back": "అన్ని క్యాలెండర్లకు తిరిగి వెళ్ళండి",
    "previous": "గత నెల",
    "next": "తదుపరి నెల",
    "select_year": "సంవత్సరాన్ని ఎంచుకోండి",
    "show_calendar": "క్యాలెండర్ చూపించు",
    "amavasya": "అమావాస్య",
    "poornima": "పౌర్ణమి",
    "date_details": "రోజు వివరాలు",
    "tithi": "తిథి",
    "nakshatram": "నక్షత్రం",
    "festivals": "పండుగలు",
    "upcoming_festivals": "రాబోయే పండుగలు",
    "date": "తేదీ",
    "temple": "దేవాలయం",
    "no_festivals": "ఈ నెలకు సంబంధించిన ధృవీకరించిన పండుగల సమాచారం అందుబాటులో లేదు.",
}

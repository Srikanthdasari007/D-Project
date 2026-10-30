from datetime import date
import re
import requests

from bs4 import BeautifulSoup
from django.core.cache import cache
from datetime import datetime
from django.utils import timezone

TELUGU_MONTHS = {
    1: "జనవరి",
    2: "ఫిబ్రవరి",
    3: "మార్చి",
    4: "ఏప్రిల్",
    5: "మే",
    6: "జూన్",
    7: "జూలై",
    8: "ఆగస్టు",
    9: "సెప్టెంబర్",
    10: "అక్టోబర్",
    11: "నవంబర్",
    12: "డిసెంబర్",
}

# Complete Telugu festival events dictionary mapping string dates to lists of events
TELUGU_TEMPLE_EVENTS = {
    # November 2026
    "2026-11-07": ["విశాఖ కార్తె", "ధన్వంతరీ జయంతి", "ధనత్రయోదశి", "మాస శివరాత్రి"],
    "2026-11-08": ["కేదార గౌరీ వ్రతం", "దీపావళి", "నరక చతుర్దశి"],
    "2026-11-09": ["అమావాస్య", "సోమవారం వ్రతం"],
    "2026-11-10": ["ఆకాశ దీప ప్రారంభం", "చంద్రోదయం", "గోవర్ధన పూజ"],
    "2026-11-11": ["యమ ద్వితీయ", "భగినీహస్త భోజనం"],
    "2026-11-12": ["నాగుల చవితి"],
    "2026-11-13": ["చతుర్థి వ్రతం"],
    "2026-11-14": ["జవహర్ లాల్ నెహ్రూ జయంతి", "బాలల దినోత్సవం"],
    "2026-11-15": ["స్కంద షష్టి", "సూర్య షష్టి"],
    "2026-11-16": ["వృశ్చిక సంక్రమణం"],
    "2026-11-17": ["దుర్గాష్టమి వ్రతం", "గోపాష్టమి", "మండల కలం ఆరంభం"],
    "2026-11-20": ["ప్రబోధిని ఏకాదశి", "కార్తీక శుద్ధ ఏకాదశి", "అనురాధ కార్తె"],
    "2026-11-21": ["క్షీరాబ్ది ద్వాదశి", "కైశిక ద్వాదశి", "చాతుర్మాస్య వ్రత సమాప్తి", "తులసి వివాహం"],
    "2026-11-22": ["ప్రదోష వ్రతం", "విశ్వేశ్వర వ్రతం"],
    "2026-11-23": ["శ్రీ సత్యసాయిబాబా జయంతి"],
    "2026-11-24": ["పౌర్ణమి వ్రతం", "పౌర్ణమి", "జ్వాలా తోరణం", "కార్తీక పౌర్ణమి", "గురునానక్ జయంతి", "శ్రీ సత్యనారాయణ పూజ", "ఉమామహేశ్వర వ్రతం"],
    "2026-11-27": ["సంకటహర చతుర్థి", "సౌభాగ్య సుందరి తీజ్"],

    # December 2026
    "2026-12-01": ["ఎయిడ్స్ డే"],
    "2026-12-03": ["జ్యేష్ఠ కార్తె"],
    "2026-12-04": ["ఉత్పన్న ఏకాదశి"],
    "2026-12-06": ["ప్రదోష వ్రతం"],
    "2026-12-07": ["మాస శివరాత్రి"],
    "2026-12-08": ["అమావాస్య"],
    "2026-12-10": ["చంద్రోదయం"],
    "2026-12-13": ["చతుర్థి వ్రతం"],
    "2026-12-14": ["సోమవారం వ్రతం"],
    "2026-12-15": ["సుబ్రహ్మణ్య షష్టి", "స్కంద షష్టి"],
    "2026-12-16": ["ధనుస్సంక్రమణం", "మూల కార్తె", "ధనుర్మాస పూజ"],
    "2026-12-17": ["దుర్గాష్టమి వ్రతం"],
    "2026-12-20": ["ముక్కోటి ఏకాదశి", "మోక్షద ఏకాదశి", "గీతా జయంతి"],
    "2026-12-21": ["సోమ ప్రదోష వ్రతం", "ప్రదోష వ్రతం"],
    "2026-12-22": ["హనుమద్వ్రతం"],
    "2026-12-23": ["దత్త జయంతి", "హజరత్ అలీ జయంతి", "శ్రీ సత్యనారాయణ పూజ", "పౌర్ణమి వ్రతం"],
    "2026-12-24": ["పౌర్ణమి", "క్రిస్మస్ ఈవ్"],
    "2026-12-25": ["క్రిస్మస్"],
    "2026-12-26": ["సంకటహర చతుర్థి", "బాక్సింగ్ డే"],
    "2026-12-27": ["మండల పూజ"],
    "2026-12-29": ["పూర్వాషాఢ కార్తె"],
    "2026-12-30": ["బుద్ధ అష్టమి"],

    # October 2027
    "2027-10-01": ["చంద్ర దర్శనం", "ఆశ్వయుజ మాసం ప్రారంభం"],
    "2027-10-02": ["మహాత్మా గాంధీ జయంతి"],
    "2027-10-05": ["స్కంద షష్ఠి"],
    "2027-10-07": ["దుర్గాష్టమి (మహాష్టమి, మహా దుర్గాష్టమి)"],
    "2027-10-08": ["సద్దుల బతుకమ్మ (బతుకమ్మ పండుగ)", "మహర్నవమి"],
    "2027-10-09": ["बुद्ध జయంతి", "విజయదశమి", "అపరాజితా జయంతి", "దసరా"],
    "2027-10-10": ["మైసూర్ దసరా"],
    "2027-10-11": ["ఏకాదశి", "పాపాంకుశ ఏకాదశి", "పద్మనాభ ద్వాదశి"],
    "2027-10-12": ["ప్రదోష వ్రతం", "భౌమ ప్రదోషం"],
    "2027-10-15": ["పౌర్ణమి", "పౌర్ణమి వ్రతం", "మీరాబాయి జయంతి", "వాల్మీకి జయంతి", "అన్వాధానం", "ఆశ్వయుజ పౌర్ణమి"],
    "2027-10-18": ["సంకష్టహర చతుర్థి", "అట్ల తద్దె", "तुला సంక్రమణం", "तुला సంక్రమణం (తులే రవి)"],
    "2027-10-22": ["మాసిక కృష్ణ జన్మాష్టమి"],
    "2027-10-25": ["ఏకాదశి", "రమా ఏకాదశి"],
    "2027-10-26": ["కృష్ణ పద్మనాభ ద్వాదశి"],
    "2027-10-27": ["మాస శివరాత్రి", "ప్రదోష వ్రతం", "హనుమాన్ పూజ"],
    "2027-10-28": ["ధనత్రయోదశి (ధంతేరస్ / నీరు జ్యోతి)"],
    "2027-10-29": ["అమావాస్య", "దీపావళి", "కేదార గౌరీ వ్రతం", "అన్వాధానం", "ఆశ్వయుజ అమావాస్య"],
    "2027-10-30": ["ఇష్టి", "గోవర్ధన పూజ", "కార్తీక మాసం ప్రారంభం"],
    "2027-10-31": ["బలిపాడ్యమి (భగినీ హస్తభోజనం)", "చంద్ర దర్శనం", "సర్దార్ వల్లభభాయి పటేల్ జయంతి", "జాతీయ ఐక్యతా దినోత్సవం", "ఇందిరా గాంధీ వర్ధంతి"],

    # November 2027
    "2027-11-01": ["ఆంధ్ర ప్రదేశ్ అవతరణోత్సవము (1956)"],
    "2027-11-02": ["నాగుల చвиతి"],
    "2027-11-04": ["స్కంద షష్ఠి"],
    "2027-11-06": ["మాసిక దుర్గాష్టమి"],
    "2027-11-10": ["ఏకాదశి", "ప్రబోధిని ఏకాదశి", "యోగేశ్వర ద్వాదశి"],
    "2027-11-11": ["క్షీరాబ్ది ద్వాదశి (చిలుక ద్వాదశి / తులసి కొరకంచె)", "ప్రదోష వ్రతం"],
    "2027-11-13": ["పౌర్ణమి వ్రతం", "అన్వాధానం"],
    "2027-11-14": ["పౌర్ణమి", "గురునానక్ జయంతి", "ఇష్టి", "నెహ్రూ జయంతి", "బాలల దినోత్సవం (చిల్డ్రన్స్デー)", "కార్తీక పౌర్ణమి"],
    "2027-11-17": ["సంకష్టహర చతుర్థి", "వృశ్చిక సంక్రమణం", "వృశ్చిక సంక్రమణం (వృశ్చికే రవి)"],
    "2027-11-20": ["మాసిక కృష్ణ జన్మాష్టమి", "కాలభైరవ జయంతి"],
    "2027-11-23": ["శ్రీ సత్యసాయిబాబా జయంతి"],
    "2027-11-24": ["ఏకాదశి", "उत्पన్న ఏకాదశి", "కృష్ణ యోగేశ్వర ద్వాదశి"],
    "2027-11-25": ["ప్రదోష వ్రతం"],
    "2027-11-26": ["మాస శివరాత్రి"],
    "2027-11-27": ["కాల జయంతి", "అన్వాధానం"],
    "2027-11-28": ["అమావాస్య", "ఇష్టి", "కార్తీక అమావాస్య"],
    "2027-11-29": ["చంద్ర దర్శనం", "మార్గశిర మాసం ప్రారంభం"],

    # December 2027
    "2027-12-01": ["ప్రపంచ ఎయిడ్స్ దినోత్సవం"],
    "2027-12-03": ["స్కంద షష్ఠి", "సుబ్రహ్మణ్య షష్టి"],
    "2027-12-06": ["మాసిక దుర్గాష్టమి"],
    "2027-12-09": ["వైకుంఠ ఏకాదశి (ముక్కోటి ఏకాదశి)", "ఏకాదశి", "మోక్షద ఏకాదశి"],
    "2027-12-10": ["మత్స్య ద్వాదశి"],
    "2027-12-11": ["ప్రదోష వ్రతం", "శని ప్రదోష వ్రతం", "శని త్రయోదశి"],
    "2027-12-12": ["హజరత్ అలీ జయంతి"],
    "2027-12-13": ["పౌర్ణమి", "పౌర్ణమి వ్రతం", "దత్తాత్రేయ జయంతి", "అన్నపూర్ణా జయంతి", "భైరవి జయంతి", "అన్వాధానం", "మార్గశిర పౌర్ణమి"],
    "2027-12-16": ["సంకష్టహర చతుర్థి", "ధనూ సంక్రమణం", "ధనుస్సంక్రమణం (ధనుర్మాసారంభం)"],
    "2027-12-20": ["మాసిక కృష్ణ జన్మాష్టమి"],
    "2027-12-21": ["ప్రపంచ ధ్యాన దినోత్సవం"],
    "2027-12-22": ["జాతీయ గణిత దినోత్సవం"],
    "2027-12-23": ["ఏకాదశి", "సఫల ఏకాదశి"],
    "2027-12-25": ["మాస శివరాత్రి", "ప్రదోష వ్రతం", "శని ప్రదోష వ్రతం", "శని త్రయోదశి", "క్రిస్మస్"],
    "2027-12-27": ["అమావాస్య", "అన్వాధానం", "మార్గశిర అమావాస్య"],
    "2027-12-28": ["ఇష్టి", "పుష్య మాసం ప్రారంభం"],
    "2027-12-29": ["చంద్ర దర్శనం"],
}

def get_monthly_temple_events(year=None, month=None):
    """Filters and returns formatted events for a given year and month."""
    today = date.today()

    if year is None:
        year = today.year

    if month is None:
        month = today.month

    if month not in range(1, 13):
        return []

    monthly_events = []

    for date_string, event_names in sorted(TELUGU_TEMPLE_EVENTS.items()):
        event_date = date.fromisoformat(date_string)

        if event_date.year == year and event_date.month == month:
            monthly_events.append({
                "date": event_date,
                "day": event_date.day,
                "date_display": f"{event_date.day} {TELUGU_MONTHS[event_date.month]} {event_date.year}",
                "events": event_names,
            })

    return monthly_events

def get_all_temple_events():
    """Returns all mapped calendar events sorted chronologically."""
    all_events = []

    for date_string, event_names in sorted(TELUGU_TEMPLE_EVENTS.items()):
        event_date = date.fromisoformat(date_string)

        all_events.append({
            "date": event_date,
            "day": event_date.day,
            "date_display": f"{event_date.day} {TELUGU_MONTHS[event_date.month]} {event_date.year}",
            "events": event_names,
        })

    return all_events

# Example Usage Execution:
if __name__ == "__main__":
    # Test lookup for December 2026
    dec_2026_events = get_monthly_temple_events(2026, 12)
    print(f"Found {len(dec_2026_events)} event dates in December 2026:")
    for entry in dec_2026_events[:3]:  # Display first 3 elements as a sample
        print(f" -> {entry['date_display']}: {entry['events']}")


# ==========================================================
# OFFICIAL TTD TEMPLE EVENTS
# Source: https://news.tirumala.org/
# ==========================================================

TTD_NEWS_URL = "https://news.tirumala.org/"

TTD_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; DarshanTemplePortal/1.0)"
}


def get_ttd_latest_article():

    """
    Finds the latest TTD article about important religious
    events and festivals.
    """

    cache_key = "darshan_ttd_latest_article"

    cached_article = cache.get(cache_key)

    if cached_article:
        return cached_article

    try:
        response = requests.get(
            TTD_NEWS_URL,
            headers=TTD_HEADERS,
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        article_url = None
        article_title = None

        for link in soup.find_all("a", href=True):

            title = link.get_text(" ", strip=True)

            title_lower = title.lower()

            if (
                "important religious events" in title_lower
                and "festivals" in title_lower
            ):
                article_url = link["href"]
                article_title = title
                break

        if not article_url:
            return None

        article_response = requests.get(
            article_url,
            headers=TTD_HEADERS,
            timeout=20
        )

        article_response.raise_for_status()

        article_soup = BeautifulSoup(
            article_response.text,
            "html.parser"
        )

        content = article_soup.find(
            "div",
            class_="entry-content"
        )

        if not content:
            return None

        article_text = content.get_text(
            "\n",
            strip=True
        )

        result = {
            "title": article_title,
            "url": article_url,
            "content": article_text,
        }

        cache.set(
            cache_key,
            result,
            21600
        )

        return result

    except requests.RequestException as error:

        print("TTD News Error:", error)

        return None


def extract_ttd_events():

    """
    Extracts only upcoming TTD events from the current month.
    """

    today = date.today()
    current_year = today.year
    current_month = today.month

    cache_key = f"darshan_ttd_events_v3_{today}"

    cached_events = cache.get(cache_key)

    if cached_events is not None:
        return cached_events

    article = get_ttd_latest_article()

    if not article:
        return []

    try:

        article_response = requests.get(
            article["url"],
            headers=TTD_HEADERS,
            timeout=20
        )

        article_response.raise_for_status()

        soup = BeautifulSoup(
            article_response.text,
            "html.parser"
        )

        content = soup.find(
            "div",
            class_="entry-content"
        )

        if not content:
            return []

        english_section = content.find(
            "div",
            attrs={"dir": "ltr"}
        )

        if not english_section:
            return []

        paragraphs = english_section.find_all("p")

        if not paragraphs:
            return []

        # Extract announcement year and month

        introduction = paragraphs[0].get_text(
            " ",
            strip=True
        )

        year_match = re.search(
            r"Tirumala,\s*\d{1,2}\s+[A-Za-z]+\s+(\d{4})",
            introduction,
            re.IGNORECASE
        )

        month_match = re.search(
            r"during the month of\s+([A-Za-z]+)",
            introduction,
            re.IGNORECASE
        )

        if not year_match or not month_match:
            return []

        year = int(year_match.group(1))

        month_name = month_match.group(1)

        month_number = datetime.strptime(
            month_name,
            "%B"
        ).month

        events = []

        # Extract events

        for paragraph in paragraphs[1:]:

            text = paragraph.get_text(
                " ",
                strip=True
            )

            match = re.search(
                r"^\s*[•·\-]?\s*"
                + re.escape(month_name)
                + r"\s+(\d{1,2})\s*:\s*(.+)$",
                text,
                re.IGNORECASE
            )

            if not match:
                continue

            day = int(match.group(1))

            event_name = match.group(2).strip()

            try:

                event_date = date(
                    year,
                    month_number,
                    day
                )

            except ValueError:
                continue

            # Only current-month future events

            if event_date <= today:
                continue

            events.append({
                "date": event_date,
                "day": day,
                "date_display": event_date.strftime(
                    "%d %B %Y"
                ),
                "name": event_name,
                "temple": "Sri Venkateswara Swamy Temple, Tirumala",
                "source": "TTD Official News",
                "url": article["url"],
            })

        events.sort(
            key=lambda item: item["date"]
        )

        cache.set(
            cache_key,
            events,
            60 * 60 * 6
        )

        return events

    except (
        requests.RequestException,
        ValueError,
        TypeError
    ) as error:

        print("TTD Event Extraction Error:", error)

        return []

    
def get_monthly_ttd_events(year=None, month=None):

    """
    Returns TTD events for a selected year and month.
    """

    today = date.today()

    if year is None:
        year = today.year

    if month is None:
        month = today.month

    if month not in range(1, 13):
        return []

    events = extract_ttd_events()

    return [
        event
        for event in events
        if (
            event["date"].year == year
            and event["date"].month == month
        )
    ]

# ==========================================================
# PURI JAGANNATH TEMPLE EVENTS
# ==========================================================

PURI_CALENDAR_URL = (
    "https://www.shreejagannatha.in/"
    "calendar-of-festive-occasion-2026-2027/"
)


def get_puri_jagannath_events():

    """
    Extracts all upcoming Puri events from the official calendar.
    """

    today = timezone.localdate()

    current_year = today.year
    current_month = today.month

    cache_key = f"puri_jagannath_events_v3_{today}"
    cached_events = cache.get(cache_key)

    if cached_events is not None:
        return cached_events

    try:

        response = requests.get(
            PURI_CALENDAR_URL,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        rows = soup.find_all("tr")

        events = []

        month_names = {
            "JAN": 1, "JANUARY": 1,
            "FEB": 2, "FEBRUARY": 2,
            "MAR": 3, "MARCH": 3,
            "APR": 4, "APRIL": 4,
            "MAY": 5,
            "JUN": 6, "JUNE": 6,
            "JUL": 7, "JULY": 7,
            "AUG": 8, "AUGUST": 8,
            "SEP": 9, "SEPT": 9, "SEPTEMBER": 9,
            "OCT": 10, "OCTOBER": 10,
            "NOV": 11, "NOVEMBER": 11,
            "DEC": 12, "DECEMBER": 12,
        }

        for row in rows:

            columns = row.find_all("td")

            if len(columns) < 3:
                continue

            festival_name = columns[0].get_text(
                " ",
                strip=True
            )

            festival_date = columns[1].get_text(
                " ",
                strip=True
            )

            weekday = columns[2].get_text(
                " ",
                strip=True
            )

            try:

                parts = festival_date.upper().split()

                if len(parts) != 3:
                    continue

                day = int(parts[0])

                month = month_names.get(parts[1])

                year = int(parts[2])

                if month is None:
                    continue

                event_date = date(
                    year,
                    month,
                    day
                )

            except (ValueError, TypeError):
                continue

            # Only current-month future events

            # Display all future Puri events

            if event_date <= today:
                continue

            events.append({
                "date": event_date,
                "day": day,
                "date_display": event_date.strftime(
                    "%d %B %Y"
                ),
                "name": festival_name,
                "weekday": weekday,
                "temple": "Shree Jagannath Temple, Puri",
                "source": "Official Temple Calendar",
                "url": PURI_CALENDAR_URL,
            })

        events.sort(
            key=lambda event: event["date"]
        )

        cache.set(
            cache_key,
            events,
            60 * 60 * 6
        )

        return events

    except Exception as e:

        print("Puri Temple Events Error:", e)

        return []


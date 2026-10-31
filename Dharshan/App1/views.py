from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.http import Http404
from django.utils import timezone

from requests.exceptions import RequestException
from datetime import date
import calendar
import requests

from .models import Registration, Festival

from .calendar_data import (
    TELUGU_CALENDAR_DATA,
    TELUGU_WEEKDAYS,
    TELUGU_LABELS,
)


from .temple_events import (
    extract_ttd_events,
    get_puri_jagannath_events,
)

def Register(request):

    if request.method == "POST":

        Username = request.POST.get("Username", "").strip()
        password = request.POST.get("password", "")
        email = request.POST.get("email", "").strip()
        mobileNumber = request.POST.get("mobileNumber", "").strip()

        # Check empty fields
        if not all([Username, password, email, mobileNumber]):

            return render(request, "Auth/register.html", {
                "error": "All fields are required."
            })

        # Check username
        if Registration.objects.filter(Username=Username).exists():

            return render(request, "Auth/register.html", {
                "error": "Username already exists."
            })

        # Check email
        if Registration.objects.filter(email=email).exists():

            return render(request, "Auth/register.html", {
                "error": "Email already registered."
            })

        # Password validation
        if len(password) < 8:

            return render(request, "Auth/register.html", {
                "error": "Password must contain at least 8 characters."
            })

        # Save user
        user = Registration(
            Username=Username,
            password=make_password(password),
            email=email,
            mobileNumber=mobileNumber
        )

        user.save()

        return redirect("login")

    return render(request, "Auth/register.html")


def login_view(request):

    if request.method == "POST":

        Username = request.POST.get("Username", "").strip()
        password = request.POST.get("password", "")

        try:

            user = Registration.objects.get(
                Username=Username
            )

            if check_password(password, user.password):

                # Prevent session fixation
                request.session.cycle_key()

                request.session["user_id"] = user.id
                request.session["username"] = user.Username

                return redirect("home")

            return render(request, "Auth/login.html", {
                "error": "Invalid password."
            })

        except Registration.DoesNotExist:

            return render(request, "Auth/login.html", {
                "error": "Please enter a valid username."
            })

    return render(request, "Auth/login.html")


def log_out(request):
    request.session.flush()
    return redirect("login")


def home_view(request):

    today = timezone.localdate()

    current_month = today.strftime("%B")
    current_year = today.year

    # Get verified festivals for the current month
    monthly_festivals = Festival.objects.filter(
        festival_date__year=current_year,
        festival_date__month=today.month,
        location__iexact="Telangana",
        is_verified=True
    ).order_by("festival_date")

    monthly_festivals = [
        {
            "name": festival.name,
            "festival_date": festival.festival_date,
            "formatted_date": festival.festival_date.strftime(
                "%A, %d %B %Y"
            ),
            "description": "",
            "image": "",
        }
        for festival in monthly_festivals
    ]

    try:
        ttd_events = extract_ttd_events()
    except Exception:
        ttd_events = []

    try:
        puri_events = get_puri_jagannath_events()
    except Exception:
        puri_events = []

    context = {
        "current_month": current_month,
        "current_year": current_year,
        "monthly_festivals": monthly_festivals,
        "ttd_events": ttd_events,
        "puri_events": puri_events,
    }

    return render(
        request,
        "Auth/home.html",
        context
    )


def temple_events_view(request, temple_type):

    # ==========================================
    # TTD EVENTS
    # ==========================================

    if temple_type == "ttd":

        events = extract_ttd_events()

        temple_name = "Tirumala Sri Venkateswara Swamy Temple"

        page_title = "TTD Upcoming Events"

        temple_image = "App_Images/Tirumala.jpg"

        source_name = "TTD Official News"

    # ==========================================
    # PURI JAGANNATH EVENTS
    # ==========================================

    elif temple_type == "puri":

        events = get_puri_jagannath_events()

        temple_name = "Shree Jagannath Temple, Puri"

        page_title = "Puri Jagannath Upcoming Events"

        temple_image = "App_Images/puri jaganath.jpeg"

        source_name = "Puri Official Events"

    else:

        raise Http404("Temple events not found")

    # ==========================================
    # SEND DATA TO HTML
    # ==========================================

    context = {
        "events": events,
        "temple_name": temple_name,
        "page_title": page_title,
        "temple_image": temple_image,
        "source_name": source_name,
    }

    return render(
        request,
        "Auth/temple_events.html",
        context
    )

def about_view(request):
    return render(request, "Auth/about.html")


def Temples_view(request):

    temples = [

        {
            "name": "Tirupati",
            "image": "App_Images/Tirumala.jpg",
            "timings": "Varies according to daily TTD schedule",
            "city": "Tirumala",
            "district": "Tirupati",
            "state": "Andhra Pradesh",
            "map_query": "Sri Venkateswara Temple Tirumala",
            "website": "https://ttdevasthanams.ap.gov.in/home/dashboard",
        },

        {
            "name": "Padmanabhaswamy",
            "image": "App_Images/Padmanabhaswamy.jpg",
            "timings": "Multiple morning and evening sessions",
            "city": "Thiruvananthapuram",
            "district": "Thiruvananthapuram",
            "state": "Kerala",
            "map_query": "Padmanabhaswamy Temple Thiruvananthapuram",
            "website": "https://spst.in/",
        },

        {
            "name": "Yadagirigutta",
            "image": "App_Images/Yadagirigutta.jpg",
            "timings": "Check official temple schedule",
            "city": "Yadagirigutta",
            "district": "Yadadri Bhuvanagiri",
            "state": "Telangana",
            "map_query": "Yadadri Lakshmi Narasimha Swamy Temple",
            "website": "https://yadagiriguttatemple.telangana.gov.in/",
        },

        {
            "name": "Hampi Virupaksha",
            "image": "App_Images/hampi.webp",
            "timings": "Check official temple schedule",
            "city": "Hampi",
            "district": "Vijayanagara",
            "state": "Karnataka",
            "map_query": "Virupaksha Temple Hampi",
            "website": "https://karnatakatourism.org/en/destinations/hampi",
        },

        {
            "name": "Ayodhya Ram Mandir",
            "image": "App_Images/Ayodhya.jpg",
            "timings": "Check official temple schedule",
            "city": "Ayodhya",
            "district": "Ayodhya",
            "state": "Uttar Pradesh",
            "map_query": "Ram Mandir Ayodhya",
            "website": "https://srjbtkshetra.org/",
        },

        {
            "name": "Jogulamba",
            "image": "App_Images/jogulamba.jpg",
            "timings": "Check official temple schedule",
            "city": "Alampur",
            "district": "Jogulamba Gadwal",
            "state": "Telangana",
            "map_query": "Jogulamba Temple Alampur",
            "website": "https://www.srijogulamba.com/public/",
        },

        {
            "name": "Tulja Bhavani",
            "image": "App_Images/Tuljapur.jpg",
            "timings": "Check official temple schedule",
            "city": "Tuljapur",
            "district": "Dharashiv",
            "state": "Maharashtra",
            "map_query": "Tulja Bhavani Temple Tuljapur",
            "website": "https://shrituljabhavani.org/en",
        },

        {
            "name": "Kanchi Kamakshi Amman",
            "image": "App_Images/Kanchi.jpg",
            "timings": "Check official temple schedule",
            "city": "Kanchipuram",
            "district": "Kanchipuram",
            "state": "Tamil Nadu",
            "map_query": "Kamakshi Amman Temple Kanchipuram",
            "website": "https://hrce.tn.gov.in/hrcehome/index_temple.php?tid=1865",
        },

        {
            "name": "Brihadeeswara",
            "image": "App_Images/Brihadeeswara.jpg",
            "timings": "Check official temple schedule",
            "city": "Thanjavur",
            "district": "Thanjavur",
            "state": "Tamil Nadu",
            "map_query": "Brihadeeswara Temple Thanjavur",
            "website": "https://www.brihadeeswaratemple.com/",
        },

        {
            "name": "Sri Ranganathaswamy",
            "image": "App_Images/Sri Ranganathaswamy.jpg",
            "timings": "Check official temple schedule",
            "city": "Srirangam",
            "district": "Tiruchirappalli",
            "state": "Tamil Nadu",
            "map_query": "Sri Ranganathaswamy Temple Srirangam",
            "website": "https://srirangamranganathar.hrce.tn.gov.in/",
        },

        {
            "name": "Arunachalam",
            "image": "App_Images/arunachalam.jpg",
            "timings": "Check official temple schedule",
            "city": "Tiruvannamalai",
            "district": "Tiruvannamalai",
            "state": "Tamil Nadu",
            "map_query": "Arunachaleswarar Temple Tiruvannamalai",
            "website": "https://annamalaiyar.hrce.tn.gov.in/",
        },

        {
            "name": "Srisailam Mallikarjuna Swamy",
            "image": "App_Images/Srisailam.jpg",
            "timings": "Check official temple schedule",
            "city": "Srisailam",
            "district": "Nandyal",
            "state": "Andhra Pradesh",
            "map_query": "Mallikarjuna Swamy Temple Srisailam",
            "website": "https://www.srisailadevasthanam.org/en-in/home",
        },

        {
            "name": "Sri Raghavendra Swamy Mantralayam",
            "image": "App_Images/Mantralayam.jpg",
            "timings": "Check official temple schedule",
            "city": "Mantralayam",
            "district": "Kurnool",
            "state": "Andhra Pradesh",
            "map_query": "Raghavendra Swamy Temple Mantralayam",
            "website": "https://srsmatha.org/",
        },

        {
            "name": "Thousand Pillar Temple",
            "image": "App_Images/Thousand Pillar Temple.jpg",
            "timings": "Check official temple schedule",
            "city": "Hanamkonda",
            "district": "Hanamkonda",
            "state": "Telangana",
            "map_query": "Thousand Pillar Temple Hanamkonda",
            "website": "https://hanumakonda.telangana.gov.in/tourist-place/thousand-pillar-temple/",
        },

        {
            "name": "Sri Gnana Saraswathi Temple",
            "image": "App_Images/Basara.jpg",
            "timings": "Check official temple schedule",
            "city": "Basara",
            "district": "Nirmal",
            "state": "Telangana",
            "map_query": "Gnana Saraswathi Temple Basara",
            "website": "https://basaratemple.org/",
        },

        {
            "name": "Sri Seetha Ramachandra Swamy",
            "image": "App_Images/Badrachalam.avif",
            "timings": "Check official temple schedule",
            "city": "Bhadrachalam",
            "district": "Bhadradri Kothagudem",
            "state": "Telangana",
            "map_query": "Sita Ramachandraswamy Temple Bhadrachalam",
            "website": "https://bhadradritemple.telangana.gov.in/timings/",
        },

    ]

    return render(request,"Auth/Temples.html",{"temples": temples})


# ==========================================
# WIKIPEDIA API CONFIGURATION
# ==========================================

WIKIPEDIA_API_URL = "https://en.wikipedia.org/w/api.php"

HEADERS = {
    "User-Agent": "DarshanTemplePortal/1.0 (Django temple information website)"
}


# ==========================================
# SEARCH TEMPLES USING WIKIPEDIA API
# ==========================================

def get_temple_information(query):

    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f'intitle:temple OR "{query}"',
        "gsrnamespace": 0,
        "gsrlimit": 20,
        "prop": "extracts|pageimages|info|categories",
        "exintro": 1,
        "explaintext": 1,
        "exchars": 1500,
        "piprop": "thumbnail",
        "pithumbsize": 600,
        "inprop": "url",
        "cllimit": 20,
        "format": "json",
        "formatversion": 2,
    }

    try:
        response = requests.get(
            WIKIPEDIA_API_URL,
            params=params,
            headers=HEADERS,
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        pages = data.get("query", {}).get("pages", [])

        temples = []

        # Terms that commonly identify temple-related articles.
        temple_terms = (
            "temple",
            "mandir",
            "devasthanam",
            "devasthana",
            "shrine",
            "pagoda",
        )

        for page in pages:

            title = page.get("title", "")
            description = page.get("extract", "")

            categories = page.get("categories", [])

            category_text = " ".join(
                category.get("title", "")
                for category in categories
            ).lower()

            title_lower = title.lower()
            description_lower = description.lower()

            # Check whether the article is temple-related.
            title_matches = any(
                term in title_lower
                for term in temple_terms
            )

            category_matches = any(
                term in category_text
                for term in temple_terms
            )

            description_matches = any(
                term in description_lower
                for term in (
                    "hindu temple",
                    "buddhist temple",
                    "jain temple",
                    "sikh temple",
                    "place of worship",
                    "temple dedicated to",
                    "temple complex",
                    "temple in india",
                    "temple located",
                )
            )

            if not (
                title_matches
                or category_matches
                or description_matches
            ):
                continue

            temples.append({
                "pageid": page.get("pageid"),
                "title": title,
                "description": description,
                "image": page.get("thumbnail", {}).get(
                    "source", ""
                ),
                "url": page.get("fullurl", ""),
            })

        return temples, None

    except RequestException:
        return [], (
            "Wikipedia is temporarily unavailable. "
            "Please try again."
        )

    except (ValueError, TypeError):
        return [], (
            "Unable to process Wikipedia results. "
            "Please try again."
        )

# ==========================================
# TEMPLE SEARCH VIEW
# ==========================================

def temple_search(request):
    query = request.GET.get("q", "").strip()

    local_temples = []
    error_message = None

    if query:
        if len(query) > 150:
            error_message = "Please enter a shorter search query."
        else:
            local_temples, error_message = get_temple_information(query)

            if not error_message and not local_temples:
                error_message = (
                    "Please search for temple-related information only."
                )

    context = {
        "query": query,
        "local_temples": local_temples,
        "error_message": error_message,
    }

    return render(request, "Auth/temple_search.html", context)
# ==========================================
# TEMPLE DETAILS VIEW
# ==========================================



def temple_details(request):
    title = request.GET.get("title", "").strip()
    search_query = request.GET.get("q", "").strip()

    if not title:
        raise Http404("Temple information was not provided.")

    params = {
        "action": "parse",
        "page": title,
        "prop": "text|displaytitle",
        "format": "json",
        "formatversion": 2,
    }

    try:
        response = requests.get(
            WIKIPEDIA_API_URL,
            params=params,
            headers=HEADERS,
            timeout=15
        )

        response.raise_for_status()
        data = response.json()

        if "error" in data:
            return render(
                request,
                "Auth/temple_details.html",
                {
                    "temple": None,
                    "error_message": "The requested Wikipedia article was not found.",
                    "query": search_query,
                    "search_query": search_query,
                }
            )

        parsed = data.get("parse", {})
        article_html = parsed.get("text", "")

        if not article_html:
            return render(
                request,
                "Auth/temple_details.html",
                {
                    "temple": None,
                    "error_message": "No article content was returned.",
                    "query": search_query,
                    "search_query": search_query,
                }
            )

        # Fetch the article's thumbnail separately.
        image_params = {
            "action": "query",
            "prop": "pageimages",
            "titles": title,
            "piprop": "thumbnail",
            "pithumbsize": 1000,
            "format": "json",
            "formatversion": 2,
        }

        image_response = requests.get(
            WIKIPEDIA_API_URL,
            params=image_params,
            headers=HEADERS,
            timeout=10
        )

        image_response.raise_for_status()
        image_data = image_response.json()

        pages = image_data.get("query", {}).get("pages", [])
        image = ""

        if pages:
            image = pages[0].get("thumbnail", {}).get("source", "")

        temple = {
            "title": parsed.get("title", title),
            "image": image,
            "article_html": article_html,
        }

        return render(
            request,
            "Auth/temple_details.html",
            {
                "temple": temple,
                "error_message": None,
                "query": search_query,
                "search_query": search_query,
            }
        )

    except requests.RequestException:
        return render(
            request,
            "Auth/temple_details.html",
            {
                "temple": None,
                "error_message": (
                    "Wikipedia is temporarily unavailable. "
                    "Please try again."
                ),
                "query": search_query,
                "search_query": search_query,
            }
        )

    except (ValueError, TypeError):
        return render(
            request,
            "Auth/temple_details.html",
            {
                "temple": None,
                "error_message": "Unable to process the Wikipedia article.",
                "query": search_query,
                "search_query": search_query,
            }
        )


# =====================================================
# CALENDAR TYPES
# =====================================================

CALENDAR_TYPES = [
    {
        "id": "gregorian",
        "name": "Gregorian Calendar",
        "native_name": "Gregorian Calendar",
        "description": "View dates, weekdays, and months of the standard international calendar.",
        "icon": "🌍",
        "color": "blue",
    },
    
    {
        "id": "telugu",
        "name": "Telugu Calendar",
        "native_name": "తెలుగు క్యాలెండర్",
        "description": "Explore Telugu months, festivals, and regional observances.",
        "icon": "🛕",
        "color": "red",
    },
    {
        "id": "hindi",
        "name": "Hindi Calendar",
        "native_name": "हिंदी कैलेंडर",
        "description": "Explore calendar information and festivals for Hindi-speaking regions.",
        "icon": "🪷",
        "color": "orange",
    },
    {
        "id": "tamil",
        "name": "Tamil Calendar",
        "native_name": "தமிழ் நாட்காட்டி",
        "description": "Explore Tamil months, important days, and regional festivals.",
        "icon": "🌺",
        "color": "pink",
    },
    {
        "id": "kannada",
        "name": "Kannada Calendar",
        "native_name": "ಕನ್ನಡ ಕ್ಯಾಲೆಂಡರ್",
        "description": "Explore Kannada calendar information and regional festivals.",
        "icon": "🌼",
        "color": "yellow",
    },
    {
        "id": "malayalam",
        "name": "Malayalam Calendar",
        "native_name": "മലയാളം കലണ്ടർ",
        "description": "Explore Malayalam months, important days, and regional observances.",
        "icon": "🌴",
        "color": "green",
    },
    {
        "id": "bengali",
        "name": "Bengali Calendar",
        "native_name": "বাংলা ক্যালেন্ডার",
        "description": "Explore Bengali calendar information and regional festivals.",
        "icon": "🌸",
        "color": "pink",
    },
    {
        "id": "marathi",
        "name": "Marathi Calendar",
        "native_name": "मराठी दिनदर्शिका",
        "description": "Explore Marathi calendar information and important observances.",
        "icon": "🙏",
        "color": "orange",
    },
    {
        "id": "gujarati",
        "name": "Gujarati Calendar",
        "native_name": "ગુજરાતી કેલેન્ડર",
        "description": "Explore Gujarati calendar information and regional festivals.",
        "icon": "🪔",
        "color": "yellow",
    },
]


# =====================================================

# REGIONAL CALENDAR LANGUAGES

# =====================================================

REGIONAL_CALENDAR_LANGUAGES = {
"gregorian": {
"months": [
"January", "February", "March", "April",
"May", "June", "July", "August",
"September", "October", "November", "December"
],
"weekdays": [
"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"
],
"labels": {
"back": "Back to All Calendars",
"previous": "Previous",
"next": "Next",
"select_year": "Select Year",
"show_calendar": "Show Calendar",
"amavasya": "Amavasya",
"poornima": "Poornima",
"date_details": "Date Details",
"tithi": "Tithi",
"nakshatram": "Nakshatram",
"festivals": "Festivals",
"upcoming_festivals": "Upcoming Festivals",
"date": "Date",
"temple": "Temple",
"no_festivals": "No verified festival information is available."
}
},


"telugu": {
    "months": [
        "జనవరి", "ఫిబ్రవరి", "మార్చి", "ఏప్రిల్",
        "మే", "జూన్", "జూలై", "ఆగస్టు",
        "సెప్టెంబర్", "అక్టోబర్", "నవంబర్", "డిసెంబర్"
    ],
    "weekdays": [
        "ఆది", "సోమ", "మంగళ", "బుధ",
        "గురు", "శుక్ర", "శని"
    ],
    "labels": {
        "back": "అన్ని క్యాలెండర్లకు వెళ్ళండి",
        "previous": "మునుపటి",
        "next": "తదుపరి",
        "select_year": "సంవత్సరాన్ని ఎంచుకోండి",
        "show_calendar": "క్యాలెండర్ చూపించు",
        "amavasya": "అమావాస్య",
        "poornima": "పౌర్ణమి",
        "date_details": "తేదీ వివరాలు",
        "tithi": "తిథి",
        "nakshatram": "నక్షత్రం",
        "festivals": "పండుగలు",
        "upcoming_festivals": "రాబోయే పండుగలు",
        "date": "తేదీ",
        "temple": "దేవాలయం",
        "no_festivals": "ధృవీకరించిన పండుగల సమాచారం అందుబాటులో లేదు."
    }
},

"hindi": {
    "months": [
        "जनवरी", "फ़रवरी", "मार्च", "अप्रैल",
        "मई", "जून", "जुलाई", "अगस्त",
        "सितंबर", "अक्टूबर", "नवंबर", "दिसंबर"
    ],
    "weekdays": [
        "रवि", "सोम", "मंगल", "बुध",
        "गुरु", "शुक्र", "शनि"
    ],
    "labels": {
        "back": "सभी कैलेंडर पर वापस जाएँ",
        "previous": "पिछला",
        "next": "अगला",
        "select_year": "वर्ष चुनें",
        "show_calendar": "कैलेंडर दिखाएँ",
        "amavasya": "अमावस्या",
        "poornima": "पूर्णिमा",
        "date_details": "तिथि विवरण",
        "tithi": "तिथि",
        "nakshatram": "नक्षत्र",
        "festivals": "त्योहार",
        "upcoming_festivals": "आगामी त्योहार",
        "date": "तारीख",
        "temple": "मंदिर",
        "no_festivals": "सत्यापित त्योहार की जानकारी उपलब्ध नहीं है।"
    }
},

"tamil": {
    "months": [
        "ஜனவரி", "பிப்ரவரி", "மார்ச்", "ஏப்ரல்",
        "மே", "ஜூன்", "ஜூலை", "ஆகஸ்ட்",
        "செப்டம்பர்", "அக்டோபர்", "நவம்பர்", "டிசம்பர்"
    ],
    "weekdays": [
        "ஞாயிறு", "திங்கள்", "செவ்வாய்", "புதன்",
        "வியாழன்", "வெள்ளி", "சனி"
    ],
    "labels": {
        "back": "அனைத்து நாட்காட்டிகளுக்கும் திரும்பு",
        "previous": "முந்தைய",
        "next": "அடுத்தது",
        "select_year": "ஆண்டைத் தேர்ந்தெடுக்கவும்",
        "show_calendar": "நாட்காட்டியைக் காட்டு",
        "amavasya": "அமாவாசை",
        "poornima": "பௌர்ணமி",
        "date_details": "தேதி விவரங்கள்",
        "tithi": "திதி",
        "nakshatram": "நட்சத்திரம்",
        "festivals": "திருவிழாக்கள்",
        "upcoming_festivals": "வரவிருக்கும் திருவிழாக்கள்",
        "date": "தேதி",
        "temple": "கோவில்",
        "no_festivals": "சரிபார்க்கப்பட்ட திருவிழாத் தகவல் கிடைக்கவில்லை."
    }
},

"kannada": {
    "months": [
        "ಜನವರಿ", "ಫೆಬ್ರವರಿ", "ಮಾರ್ಚ್", "ಏಪ್ರಿಲ್",
        "ಮೇ", "ಜೂನ್", "ಜುಲೈ", "ಆಗಸ್ಟ್",
        "ಸೆಪ್ಟೆಂಬರ್", "ಅಕ್ಟೋಬರ್", "ನವೆಂಬರ್", "ಡಿಸೆಂಬರ್"
    ],
    "weekdays": [
        "ಭಾನು", "ಸೋಮ", "ಮಂಗಳ", "ಬುಧ",
        "ಗುರು", "ಶುಕ್ರ", "ಶನಿ"
    ],
    "labels": {
        "back": "ಎಲ್ಲಾ ಕ್ಯಾಲೆಂಡರ್‌ಗಳಿಗೆ ಹಿಂತಿರುಗಿ",
        "previous": "ಹಿಂದಿನ",
        "next": "ಮುಂದಿನ",
        "select_year": "ವರ್ಷವನ್ನು ಆಯ್ಕೆಮಾಡಿ",
        "show_calendar": "ಕ್ಯಾಲೆಂಡರ್ ತೋರಿಸಿ",
        "amavasya": "ಅಮಾವಾಸ್ಯೆ",
        "poornima": "ಹುಣ್ಣಿಮೆ",
        "date_details": "ದಿನಾಂಕದ ವಿವರಗಳು",
        "tithi": "ತಿಥಿ",
        "nakshatram": "ನಕ್ಷತ್ರ",
        "festivals": "ಹಬ್ಬಗಳು",
        "upcoming_festivals": "ಮುಂಬರುವ ಹಬ್ಬಗಳು",
        "date": "ದಿನಾಂಕ",
        "temple": "ದೇವಾಲಯ",
        "no_festivals": "ಪರಿಶೀಲಿಸಿದ ಹಬ್ಬಗಳ ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ."
    }
},

"malayalam": {
    "months": [
        "ജനുവരി", "ഫെബ്രുവരി", "മാർച്ച്", "ഏപ്രിൽ",
        "മേയ്", "ജൂൺ", "ജൂലൈ", "ഓഗസ്റ്റ്",
        "സെപ്റ്റംബർ", "ഒക്ടോബർ", "നവംബർ", "ഡിസംബർ"
    ],
    "weekdays": [
        "ഞായർ", "തിങ്കൾ", "ചൊവ്വ", "ബുധൻ",
        "വ്യാഴം", "വെള്ളി", "ശനി"
    ],
    "labels": {
        "back": "എല്ലാ കലണ്ടറുകളിലേക്കും മടങ്ങുക",
        "previous": "മുമ്പത്തെ",
        "next": "അടുത്തത്",
        "select_year": "വർഷം തിരഞ്ഞെടുക്കുക",
        "show_calendar": "കലണ്ടർ കാണിക്കുക",
        "amavasya": "അമാവാസി",
        "poornima": "പൗർണ്ണമി",
        "date_details": "തീയതി വിവരങ്ങൾ",
        "tithi": "തിഥി",
        "nakshatram": "നക്ഷത്രം",
        "festivals": "ഉത്സവങ്ങൾ",
        "upcoming_festivals": "വരാനിരിക്കുന്ന ഉത്സവങ്ങൾ",
        "date": "തീയതി",
        "temple": "ക്ഷേത്രം",
        "no_festivals": "പരിശോധിച്ച ഉത്സവ വിവരങ്ങൾ ലഭ്യമല്ല."
    }
},

"bengali": {
    "months": [
        "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল",
        "মে", "জুন", "জুলাই", "আগস্ট",
        "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর"
    ],
    "weekdays": [
        "রবি", "সোম", "মঙ্গল", "বুধ",
        "বৃহস্পতি", "শুক্র", "শনি"
    ],
    "labels": {
        "back": "সব ক্যালেন্ডারে ফিরে যান",
        "previous": "আগের",
        "next": "পরবর্তী",
        "select_year": "বছর নির্বাচন করুন",
        "show_calendar": "ক্যালেন্ডার দেখান",
        "amavasya": "অমাবস্যা",
        "poornima": "পূর্ণিমা",
        "date_details": "তারিখের বিবরণ",
        "tithi": "তিথি",
        "nakshatram": "নক্ষত্র",
        "festivals": "উৎসব",
        "upcoming_festivals": "আসন্ন উৎসব",
        "date": "তারিখ",
        "temple": "মন্দির",
        "no_festivals": "যাচাইকৃত উৎসবের তথ্য উপলব্ধ নেই।"
    }
},

"gujarati": {
    "months": [
        "જાન્યુઆરી", "ફેબ્રુઆરી", "માર્ચ", "એપ્રિલ",
        "મે", "જૂન", "જુલાઈ", "ઑગસ્ટ",
        "સપ્ટેમ્બર", "ઑક્ટોબર", "નવેમ્બર", "ડિસેમ્બર"
    ],
    "weekdays": [
        "રવિ", "સોમ", "મંગળ", "બુધ",
        "ગુરુ", "શુક્ર", "શનિ"
    ],
    "labels": {
        "back": "બધા કેલેન્ડર પર પાછા જાઓ",
        "previous": "પહેલાંનું",
        "next": "આગળનું",
        "select_year": "વર્ષ પસંદ કરો",
        "show_calendar": "કેલેન્ડર બતાવો",
        "amavasya": "અમાસ",
        "poornima": "પૂનમ",
        "date_details": "તારીખની વિગતો",
        "tithi": "તિથિ",
        "nakshatram": "નક્ષત્ર",
        "festivals": "તહેવારો",
        "upcoming_festivals": "આગામી તહેવારો",
        "date": "તારીખ",
        "temple": "મંદિર",
        "no_festivals": "ચકાસેલી તહેવારની માહિતી ઉપલબ્ધ નથી."
    }
},

"marathi": {
    "months": [
        "जानेवारी", "फेब्रुवारी", "मार्च", "एप्रिल",
        "मे", "जून", "जुलै", "ऑगस्ट",
        "सप्टेंबर", "ऑक्टोबर", "नोव्हेंबर", "डिसेंबर"
    ],
    "weekdays": [
        "रवि", "सोम", "मंगळ", "बुध",
        "गुरु", "शुक्र", "शनि"
    ],
    "labels": {
        "back": "सर्व दिनदर्शिकांकडे परत जा",
        "previous": "मागील",
        "next": "पुढील",
        "select_year": "वर्ष निवडा",
        "show_calendar": "दिनदर्शिका दाखवा",
        "amavasya": "अमावस्या",
        "poornima": "पौर्णिमा",
        "date_details": "तारखेचा तपशील",
        "tithi": "तिथी",
        "nakshatram": "नक्षत्र",
        "festivals": "सण",
        "upcoming_festivals": "आगामी सण",
        "date": "तारीख",
        "temple": "मंदिर",
        "no_festivals": "सत्यापित सणांची माहिती उपलब्ध नाही."
    }
}


}


# =====================================================
# CALENDAR SELECTION PAGE
# =====================================================

def calendar_languages(request):

    context = {
        "calendar_types": CALENDAR_TYPES,
    }

    return render(
        request,
        "Auth/calendar_languages.html",
        context
    )


# =====================================================
# SELECTED CALENDAR PAGE
# =====================================================



def calendar_detail(request, calendar_type):

    # FIND THE SELECTED CALENDAR
    selected_calendar = next(
        (
            item for item in CALENDAR_TYPES
            if item["id"] == calendar_type
        ),
        None
    )

    if selected_calendar is None:
        raise Http404("Calendar not found")

    today = timezone.localdate()

    # GET SELECTED YEAR AND MONTH
    try:
        year = int(request.GET.get("year", today.year))
        month = int(request.GET.get("month", today.month))

        if not 1900 <= year <= 2100:
            raise ValueError

        if not 1 <= month <= 12:
            raise ValueError

    except (ValueError, TypeError):
        year = today.year
        month = today.month

    # PREVIOUS MONTH
    if month == 1:
        previous_month = 12
        previous_year = year - 1
    else:
        previous_month = month - 1
        previous_year = year

    # NEXT MONTH
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    # LANGUAGE CONFIGURATION
    language_config = REGIONAL_CALENDAR_LANGUAGES.get(
        calendar_type,
        REGIONAL_CALENDAR_LANGUAGES["gregorian"]
    )

    month_name = language_config["months"][month - 1]
    weekdays = language_config["weekdays"]
    labels = language_config["labels"]

    days_data = {}
    upcoming_festivals = []

    # LOAD TELUGU CALENDAR INFORMATION
    if calendar_type == "telugu":

        weekdays = TELUGU_WEEKDAYS
        labels = TELUGU_LABELS

        year_data = TELUGU_CALENDAR_DATA.get(year, {})
        month_data = year_data.get(month, {})

        month_name = month_data.get(
            "month_name",
            language_config["months"][month - 1]
        )

        original_days = month_data.get("days", {})

        for day_number, details in original_days.items():

            day_number = int(day_number)

            days_data[day_number] = dict(details)

            # Festival dates come from the verified database.
            days_data[day_number]["festivals"] = []

    # LOAD VERIFIED FESTIVALS FROM DATABASE
    monthly_festivals = Festival.objects.filter(
        festival_date__year=year,
        festival_date__month=month,
        location__iexact="Telangana",
        is_verified=True
    ).order_by("festival_date")

    for festival in monthly_festivals:

        festival_day = festival.festival_date.day

        if festival_day not in days_data:
            days_data[festival_day] = {}

        existing_festivals = days_data[festival_day].get(
            "festivals", []
        )

        if isinstance(existing_festivals, str):
            existing_festivals = [existing_festivals]

        if existing_festivals is None:
            existing_festivals = []

        if festival.name not in existing_festivals:
            existing_festivals.append(festival.name)

        days_data[festival_day]["festivals"] = existing_festivals

    # BUILD CALENDAR GRID
    month_calendar = calendar.Calendar(
        firstweekday=6
    ).monthdayscalendar(year, month)

    weeks = []

    for week in month_calendar:

        week_data = []

        for day_number in week:

            if day_number == 0:
                week_data.append({
                    "day": ""
                })
                continue

            day_details = days_data.get(
                day_number,
                {}
            )

            day_festivals = day_details.get(
                "festivals",
                []
            )

            if isinstance(day_festivals, str):
                day_festivals = [day_festivals]

            elif day_festivals is None:
                day_festivals = []

            day_item = {
                "day": day_number,

                "is_today": (
                    year == today.year
                    and month == today.month
                    and day_number == today.day
                ),

                "tithi": day_details.get("tithi", ""),

                "nakshatram": day_details.get(
                    "nakshatram", ""
                ),

                "festivals": day_festivals,

                "is_amavasya": day_details.get(
                    "is_amavasya", False
                ),

                "is_poornima": day_details.get(
                    "is_poornima", False
                ),
            }

            week_data.append(day_item)

            # UPCOMING FESTIVAL LIST
            for festival_name in day_festivals:

                upcoming_festivals.append({
                    "title": festival_name,

                    "date": (
                        f"{day_number:02d}-"
                        f"{month:02d}-"
                        f"{year}"
                    ),

                    "temple_name": "",

                    "description": "",
                })

        weeks.append(week_data)

    # TEMPLATE CONTEXT
    context = {
        "calendar": selected_calendar,
        "today": today,
        "year": year,
        "month": month,
        "month_name": month_name,
        "weekdays": weekdays,
        "weeks": weeks,
        "labels": labels,
        "selected_date_info": None,
        "upcoming_festivals": upcoming_festivals,

        "previous_month": previous_month,
        "previous_year": previous_year,

        "next_month": next_month,
        "next_year": next_year,

        "year_options": range(
            max(1900, today.year - 5),
            min(2100, today.year + 5) + 1
        ),
    }

    return render(
        request,
        "Auth/calendar_detail.html",
        context
    )
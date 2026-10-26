from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password, check_password
from .models import Registration
import random
import requests
from django.shortcuts import render
from django.http import Http404
from requests.exceptions import RequestException
from datetime import date
import calendar


def Register(request):

    if request.method == "POST":

        Username = request.POST.get("Username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        mobileNumber = request.POST.get("mobileNumber")

        # Check whether username already exists
        if Registration.objects.filter(Username=Username).exists():
            return render(request, "Auth/register.html", {
                "error": "Username already exists"
            })

        # Generate 6 digit OTP
        otp = random.randint(100000, 999999)

        # Store registration data temporarily in session
        request.session["Username"] = Username
        request.session["password"] = password
        request.session["email"] = email
        request.session["mobileNumber"] = mobileNumber
        request.session["otp"] = str(otp)

        # Send OTP to email
        send_mail(
            "Darshan - Email Verification OTP",
            f"Your OTP is: {otp}",
            "your_email@gmail.com",
            [email],
            fail_silently=False
        )

        # Go to OTP verification page
        return redirect("verifyotp")

    return render(request, "Auth/register.html")


def verify_otp(request):

    if request.method == "POST":

        entered_otp = request.POST.get("otp")

        stored_otp = request.session.get("otp")

        if entered_otp == stored_otp:

            # Get registration data from session
            Username = request.session.get("Username")
            password = request.session.get("password")
            email = request.session.get("email")
            mobileNumber = request.session.get("mobileNumber")

            # Create user after OTP verification
            user = Registration(
                Username=Username,
                password=make_password(password),
                email=email,
                mobileNumber=mobileNumber
            )

            user.save()

            # Remove OTP and registration data from session
            request.session.pop("otp", None)
            request.session.pop("Username", None)
            request.session.pop("password", None)
            request.session.pop("email", None)
            request.session.pop("mobileNumber", None)

            return redirect("login")

        else:

            return render(request, "Auth/verifyotp.html", {
                "error": "Invalid OTP"
            })

    return render(request, "Auth/verifyotp.html")


def login_view(request):

    if request.method == "POST":

        Username = request.POST.get("Username")
        password = request.POST.get("password")

        try:

            user = Registration.objects.get(Username=Username)

            if check_password(password, user.password):
                return redirect("home")

            return render(request, "Auth/login.html", {
                "error": "Invalid password"
            })

        except Registration.DoesNotExist:

            return render(request, "Auth/login.html", {
                "error": "Please enter a valid username"
            })

    return render(request, "Auth/login.html")

def log_out(request):
    return render(request,"Auth/login.html")


def home_view(request):
    return render(request, "Auth/home.html")


def profile_view(request):
    return render(request, "Auth/profile.html")


def about_view(request):
    return render(request, "Auth/about.html")


def Temples_view(request):
    return render(request, "Auth/Temples.html")


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
        "gsrsearch": query,
        "gsrnamespace": 0,
        "gsrlimit": 8,
        "prop": "extracts|pageimages|info",
        "exintro": 1,
        "explaintext": 1,
        "exchars": 1000,
        "piprop": "thumbnail",
        "pithumbsize": 600,
        "inprop": "url",
        "format": "json",
        "formatversion": 2
    }

    try:
        response = requests.get(
            WIKIPEDIA_API_URL,
            params=params,
            headers=HEADERS,
            timeout=8
        )

        response.raise_for_status()

        data = response.json()

        pages = data.get("query", {}).get("pages", [])

        temples = []

        for page in pages:

            temple = {
                "pageid": page.get("pageid"),
                "title": page.get("title", ""),
                "description": page.get("extract", ""),
                "image": page.get("thumbnail", {}).get("source", ""),
                "url": page.get("fullurl", "")
            }

            temples.append(temple)

        return temples, None

    except RequestException:
        return [], "Wikipedia is temporarily unavailable. Please try again."

    except (ValueError, TypeError):
        return [], "Unable to process Wikipedia results. Please try again."


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

            if not local_temples and not error_message:
                error_message = (
                    "No Wikipedia results found. "
                    "Please try another temple name."
                )

    context = {
        "query": query,
        "local_temples": local_temples,
        "error_message": error_message
    }

    return render(
        request,
        "Auth/temple_search.html",
        context
    )


# ==========================================
# TEMPLE DETAILS VIEW
# ==========================================



def temple_details(request):
    title = request.GET.get("title", "").strip()

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
                    "error_message": "The requested Wikipedia article was not found."
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
                    "error_message": "No article content was returned."
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
                )
            }
        )

    except (ValueError, TypeError):
        return render(
            request,
            "Auth/temple_details.html",
            {
                "temple": None,
                "error_message": "Unable to process the Wikipedia article."
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
        "id": "hindu-panchangam",
        "name": "Hindu Panchangam",
        "native_name": "हिन्दू पंचांग",
        "description": "Explore Tithi, Nakshatra, Yoga, Karana, and other Panchang details.",
        "icon": "🪔",
        "color": "orange",
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

    selected_calendar = next(
        (
            item for item in CALENDAR_TYPES
            if item["id"] == calendar_type
        ),
        None
    )

    if selected_calendar is None:
        raise Http404("Calendar not found")

    today = date.today()

    # Get selected year and month.
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

    # Previous month
    if month == 1:
        previous_month = 12
        previous_year = year - 1
    else:
        previous_month = month - 1
        previous_year = year

    # Next month
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year

    # Gregorian monthly grid for the initial version.
    month_calendar = calendar.Calendar(
        firstweekday=6
    ).monthdayscalendar(year, month)

    weeks = []

    for week in month_calendar:
        week_data = []

        for day in week:
            week_data.append({
                "day": day if day else "",
                "is_today": (
                    bool(day)
                    and year == today.year
                    and month == today.month
                    and day == today.day
                ),
            })

        weeks.append(week_data)

    context = {
        "calendar": selected_calendar,
        "today": today,
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "weeks": weeks,
        "previous_month": previous_month,
        "previous_year": previous_year,
        "next_month": next_month,
        "next_year": next_year,
        "year_options": range(today.year - 30, today.year + 11),
    }

    return render(
        request,
        "Auth/calendar_detail.html",
        context
    )
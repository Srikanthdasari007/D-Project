import requests
from datetime import date, datetime
from django.core.cache import cache


FESTIVAL_API_URL = (
    "https://indian-festival-api.vercel.app/api/festivals"
)


def get_monthly_festivals(
    year=None,
    month=None,
    language="english"
):
    # Use current year and month by default.
    # This keeps the existing Home page function working.
    if year is None:
        year = date.today().year

    if month is None:
        month = date.today().month

    language = language.lower()

    cache_key = (
        f"monthly_festivals_{year}_{month}_{language}"
    )

    cached_festivals = cache.get(cache_key)

    if cached_festivals is not None:
        return cached_festivals

    try:
        response = requests.get(
            FESTIVAL_API_URL,
            params={
                "month": month,
                "religion": "hindu",
                "state": "Telangana",
            },
            timeout=10,
        )

        response.raise_for_status()

        result = response.json()

        festivals = []

        for item in result.get("data", []):

            # Get the festival date for the selected year.
            date_string = item.get(f"date_{year}")

            if not date_string:
                continue

            try:
                festival_date = datetime.strptime(
                    date_string,
                    "%Y-%m-%d"
                ).date()

            except ValueError:
                continue

            # Make sure the festival belongs to
            # the requested month and year.
            if (
                festival_date.year != year
                or festival_date.month != month
            ):
                continue

            # Get the festival name in selected language.
            local_names = item.get("local_names", {})

            festival_name = (
                local_names.get(language)
                or item.get("name", "Festival")
            )

            festivals.append({
                "name": festival_name,
                "english_name": item.get("name", "Festival"),
                "festival_date": festival_date,
                "formatted_date": festival_date.strftime(
                    "%A, %d %B %Y"
                ),
                "description": item.get("description", ""),
                "image": "",
            })

        festivals.sort(
            key=lambda festival: festival["festival_date"]
        )

        # Cache for six hours.
        cache.set(cache_key, festivals, 21600)

        return festivals

    except (
        requests.RequestException,
        ValueError,
        TypeError,
    ):
        return []
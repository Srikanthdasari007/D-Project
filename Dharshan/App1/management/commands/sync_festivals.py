import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from App1.models import Festival, FestivalSync


CALENDAR_URL = "https://www.telangana.gov.in/downloads/calendar-2026/"

MONTHS = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}


class Command(BaseCommand):

    help = "Import Telangana government festival calendar"

    def add_arguments(self, parser):

        parser.add_argument(
            "--year",
            type=int,
            required=True
        )

    def handle(self, *args, **options):

        year = options["year"]

        # Check whether the year was already imported.
        if FestivalSync.objects.filter(
            year=year,
            completed=True
        ).exists():

            self.stdout.write(
                self.style.WARNING(
                    f"{year} calendar already imported. No request made."
                )
            )

            return

        # Currently configured for 2026 only.
        if year != 2026:

            raise CommandError(
                "Calendar source is currently configured only for 2026."
            )

        self.stdout.write("Fetching Telangana calendar...")

        try:

            response = requests.get(
                CALENDAR_URL,
                headers={
                    "User-Agent": "DarshanTemplePortal/1.0"
                },
                timeout=20
            )

            response.raise_for_status()

        except requests.RequestException as error:

            raise CommandError(
                f"Calendar request failed: {error}"
            )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        page_text = soup.get_text(
            separator="\n",
            strip=True
        )

        print("STATUS CODE:", response.status_code)

        print(
            "PAGE TITLE:",
            soup.title.get_text(strip=True)
            if soup.title else "No title"
        )

        # Extract dates and festival names.
        pattern = re.compile(
            r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})$"
        )

        lines = [
            line.strip()
            for line in page_text.splitlines()
            if line.strip()
        ]

        records = []

        for index, line in enumerate(lines):

            match = pattern.match(line)

            if not match:
                continue

            month_name = match.group(1)
            day = int(match.group(2))

            if index + 1 >= len(lines):
                continue

            festival_name = lines[index + 1].strip()

            if festival_name.isdigit():
                continue

            if festival_name in [
                "Sun", "Mon", "Tue", "Wed",
                "Thu", "Fri", "Sat"
            ]:
                continue

            month = MONTHS[month_name]

            try:

                festival_date = datetime(
                    year,
                    month,
                    day
                ).date()

            except ValueError:
                continue

            records.append({
                "name": festival_name,
                "festival_date": festival_date
            })

        # Display extracted records.
        print("\nEXTRACTED FESTIVALS:\n")

        for record in records:

            print(
                record["festival_date"],
                "-",
                record["name"]
            )

        print("\nTOTAL RECORDS:", len(records))

        if not records:

            raise CommandError(
                "No calendar entries found. Database was not updated."
            )

        # Save records into the database.
        with transaction.atomic():

            for record in records:

                Festival.objects.update_or_create(

                    name=record["name"],

                    festival_date=record["festival_date"],

                    location="Telangana",

                    defaults={
                        "category": "Other",
                        "source": CALENDAR_URL,
                        "is_verified": True,
                    }
                )

            # Mark the year as successfully imported.
            FestivalSync.objects.update_or_create(

                year=year,

                defaults={
                    "completed": True
                }
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(records)} entries for {year}."
            )
        )
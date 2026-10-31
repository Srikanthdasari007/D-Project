import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from App1.models import TempleEvent

from App1.temple_events import (
    get_ttd_latest_article,
    TTD_NEWS_URL,
    TTD_HEADERS,
    PURI_CALENDAR_URL,
)


MONTHS = {
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


class Command(BaseCommand):

    help = "Import TTD and Puri temple events into the database"

    def add_arguments(self, parser):

        parser.add_argument(
            "--temple",
            choices=["TTD", "PURI", "ALL"],
            default="ALL",
            help="Select which temple events to import"
        )

    def handle(self, *args, **options):

        temple = options["temple"]

        if temple in ["TTD", "ALL"]:
            self.import_ttd_events()

        if temple in ["PURI", "ALL"]:
            self.import_puri_events()

    # ==========================================
    # TTD EVENT IMPORT
    # ==========================================

    def import_ttd_events(self):

        self.stdout.write("\nFetching TTD announcement...")

        article = get_ttd_latest_article()

        if not article:
            raise CommandError(
                "Could not retrieve the TTD announcement."
            )

        article_url = article["url"]
        article_text = article["content"]

        year_match = re.search(
            r"Tirumala,\s*\d{1,2}\s+[A-Za-z]+\s+(\d{4})",
            article_text,
            re.IGNORECASE
        )

        month_match = re.search(
            r"during the month of\s+([A-Za-z]+)",
            article_text,
            re.IGNORECASE
        )

        if not year_match or not month_match:
            raise CommandError(
                "Could not identify the month and year "
                "in the TTD announcement."
            )

        year = int(year_match.group(1))
        month_name = month_match.group(1)

        try:
            month_number = datetime.strptime(
                month_name,
                "%B"
            ).month
        except ValueError:
            raise CommandError(
                f"Invalid TTD announcement month: {month_name}"
            )

        pattern = re.compile(
            r"^\s*[•·\-]?\s*"
            + re.escape(month_name)
            + r"\s+(\d{1,2})\s*:\s*(.+)$",
            re.IGNORECASE
        )

        records = []

        for line in article_text.splitlines():

            match = pattern.match(line.strip())

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

            if not event_name:
                continue

            records.append({
                "name": event_name,
                "event_date": event_date,
                "weekday": event_date.strftime("%A"),
            })

        if not records:
            raise CommandError(
                "No TTD events extracted. Database was not changed."
            )

        self.save_events(
            temple="TTD",
            records=records,
            source_url=article_url
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(records)} TTD events."
            )
        )

        self.stdout.write(f"Source: {article_url}")

    # ==========================================
    # PURI EVENT IMPORT
    # ==========================================

    def import_puri_events(self):

        self.stdout.write("\nFetching Puri calendar...")

        try:

            response = requests.get(
                PURI_CALENDAR_URL,
                headers={
                    "User-Agent": "Mozilla/5.0 "
                    "(compatible; DarshanTemplePortal/1.0)"
                },
                timeout=30
            )

            response.raise_for_status()

        except requests.RequestException as error:

            raise CommandError(
                f"Puri calendar request failed: {error}"
            )

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        rows = soup.find_all("tr")

        records = []

        for row in rows:

            columns = row.find_all("td")

            if len(columns) < 3:
                continue

            event_name = columns[0].get_text(
                " ",
                strip=True
            )

            date_text = columns[1].get_text(
                " ",
                strip=True
            )

            weekday = columns[2].get_text(
                " ",
                strip=True
            )

            try:

                parts = date_text.upper().split()

                if len(parts) != 3:
                    continue

                day = int(parts[0])
                month = MONTHS.get(parts[1])
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

            if not event_name:
                continue

            records.append({
                "name": event_name,
                "event_date": event_date,
                "weekday": weekday,
            })

        if not records:
            raise CommandError(
                "No Puri events extracted. Database was not changed."
            )

        self.save_events(
            temple="PURI",
            records=records,
            source_url=PURI_CALENDAR_URL
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully imported {len(records)} Puri events."
            )
        )

        self.stdout.write(f"Source: {PURI_CALENDAR_URL}")

    # ==========================================
    # SAVE EVENTS INTO DATABASE
    # ==========================================

    def save_events(self, temple, records, source_url):

        with transaction.atomic():

            # Replace records from this same source.
            TempleEvent.objects.filter(
                temple=temple,
                source_url=source_url
            ).delete()

            objects = []

            for record in records:

                objects.append(
                    TempleEvent(
                        temple=temple,
                        name=record["name"],
                        event_date=record["event_date"],
                        weekday=record["weekday"],
                        source_url=source_url,
                    )
                )

            TempleEvent.objects.bulk_create(
                objects,
                ignore_conflicts=True
            )

        self.stdout.write(
            f"Saved {len(records)} {temple} records."
        )
import json
import httpx
from bs4 import BeautifulSoup
import pendulum
from rich import print
import hashlib
import warnings
import importlib.metadata
import argparse

from . import config
from .db.models import setup_database, connect_database
from .google_client.auth import Metadata, reset_auth_cache, import_client_secret
from .google_client.google_client import GoogleClient
from .db.models import reset_database

# TODO: Allow user to specifiy destination calendar rather than the default of 'primary'


def pendulum_tz_warning_handler(message, category, filename, lineno, file=None, line=None):
    if "defaulting to UTC" in str(message):
        raise UserWarning(message)

warnings.showwarning = pendulum_tz_warning_handler

def cli():
    parser = argparse.ArgumentParser(description="Homebase/Google Calendar Sync CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=importlib.metadata.version("homebase_calendar_sync"),
        help="print package version to console."
    )
    parser.add_argument(
        "--import-secret",
        nargs="?",
        const=True,
        default=False,
        help="Path to 'client_secret.json'",
    )
    parser.add_argument(
        "--reset-remote",
        action="store_true",
        help="Remove all homebase events from Google Calendar for current user and calendar",
    )
    parser.add_argument(
        "--reset-db", action="store_true", help="reset the events database"
    )
    parser.add_argument(
        "--reset-events", action="store_true", help="reset both local and remote events"
    )
    parser.add_argument(
        "--reset-auth", action="store_true", help="reset the authentication cache"
    )
    parser.add_argument(
        "--reset-local", action="store_true", help="reset local files and configuration"
    )
    parser.add_argument(
        "--reset-all", action="store_true", help="reset auth config and events database"
    )

    config.ARGS = parser.parse_args()

    if config.ARGS.import_secret:
        import_client_secret(config.ARGS.import_secret)
        raise SystemExit

    if config.ARGS.reset_remote:
        remove = HomebaseCalendarSync()
        remove.remove_remote_homebase_events()
        raise SystemExit()

    if config.ARGS.reset_db:
        reset_database()
        raise SystemExit

    if config.ARGS.reset_events:
        remove = HomebaseCalendarSync()
        remove.remove_remote_homebase_events()
        reset_database()
        raise SystemExit()

    if config.ARGS.reset_auth:
        reset_auth_cache()
        raise SystemExit

    if config.ARGS.reset_local:
        reset_auth_cache()
        reset_database()
        raise SystemExit

    if config.ARGS.reset_all:
        remove = HomebaseCalendarSync()
        remove.remove_remote_homebase_events()
        reset_auth_cache()
        reset_database()
        raise SystemExit


class HomebaseScheduleScraper:
    def __init__(
        self, username, password, first_name, last_name, start_date, end_date
    ) -> None:
        self.username = username
        self.password = password
        self.start_date, self.end_date = self.initialize_date_range(
            start_date, end_date
        )
        self.login_url = "https://app.joinhomebase.com/accounts/sign-in"
        self.base_schedule_url = (
            "https://app.joinhomebase.com/api/fe/schedule_builder/schedule?"
        )
        self.client = httpx.Client()
        self.login_payload = {
            "authenticity_token": self.get_authenticity_token(),
            "account[login]": username,
            "account[password]": password,
            "account[remember_me]": 0,
        }
        self.login()
        self.calendar_json = json.loads(self.get_calendar_json())
        self.employee_first_name = first_name
        self.employee_last_name = last_name
        self.employee_id = self.get_employee_id()
        self.employee_jobs = self.get_employee_jobs()
        self.employee_shifts = self.get_employee_shifts()
        self.employee_shifts_in_range = self.filter_shifts_by_date()
        self.close()

    def close(self):
        self.client.close()

    def get_login_form(self):
        response = self.client.get(self.login_url)

        if response.status_code == 200:
            html_content = BeautifulSoup(response.text, "html.parser")

            return html_content.find("form", method="post")
        else:
            print(f"Failed to retrieve the page. Status Code: {response.status_code}")

    def get_authenticity_token(self):
        login_form = self.get_login_form()
        if login_form:
            input_element = login_form.find(
                "input", attrs={"name": "authenticity_token", "type": "hidden"}
            )
            return input_element.get("value")
        else:
            print("No input element with `name='authenticity_token'` found.")

    def login(self):
        response = self.client.post(self.login_url, data=self.login_payload)

        if response.status_code == 200:
            print(f"Homebase Login Successful. Status Code: {response.status_code}")
        else:
            print(f"Homebase Login failed. Status Code: {response.status_code}")

    def get_schedule_route(self):
        route = f"{self.base_schedule_url}end_date={self.end_date.to_date_string()}&start_date={self.start_date.to_date_string()}"
        print(route)
        return route

    def get_calendar_json(self):
        response = self.client.get(self.get_schedule_route())

        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve the page. Status Code: {response.status_code}")

    def get_employee_id(self):
        for _ in self.calendar_json["included"]:
            if _["type"] == "user" and (
                str(_["attributes"]["firstName"]).lower()
                == self.employee_first_name.lower()
                and str(_["attributes"]["lastName"]).lower()
                == self.employee_last_name.lower()
            ):
                return _["id"]

    def get_employee_jobs(self):
        return [
            _["id"]
            for _ in self.calendar_json["included"]
            if _["type"] == "job"
            and _["relationships"]["user"]["data"]["id"] == self.employee_id
        ]

    def get_employee_shifts(self):
        return (
            _
            for _ in self.calendar_json["included"]
            if _["type"] == "shift"
            and _["relationships"]["owner"]["data"]["id"] in self.employee_jobs
        )

    def initialize_date_range(self, start_date, end_date):

        try:
            if start_date == "today":
                start = pendulum.now().start_of("day")
            else:
                start = pendulum.parse(start_date).start_of("day")
            if end_date == "today":
                end = pendulum.now().end_of("day")
            else:
                end = pendulum.parse(end_date).end_of("day")

            if config.LOOKAHEAD:
                start = start.start_of("week")
                end = end.add(days=config.LOOKAHEAD_DAYS).end_of("week")
        except UserWarning as e:
            pendulum.set_local_timezone(config.TIMEZONE)
            print(f"Modified ")
            self.initialize_date_range(start_date, end_date)

        return start, end

    def filter_shifts_by_date(self):
        return (
            _
            for _ in self.employee_shifts
            if self.start_date
            <= pendulum.parse(_["attributes"]["startAt"])
            <= self.end_date
        )

    def get_employee_shifts_json(self):
        shifts = []

        for _ in self.employee_shifts_in_range:
            shift = {
                "shiftId": _["id"],
                "firstName": self.employee_first_name,
                "lastName": self.employee_last_name,
                "jobRole": _["attributes"]["roleName"],
                "shiftDate": pendulum.parse(
                    _["attributes"]["startAt"]
                ).to_date_string(),
                "startTime": pendulum.parse(
                    _["attributes"]["startAt"]
                ).to_time_string(),
                "endTime": pendulum.parse(_["attributes"]["endAt"]).to_time_string(),
            }

            shifts.append(shift)

        return json.dumps(shifts)


class HomebaseCalendarSync:
    def __init__(self) -> None:
        config.META = Metadata.metadata_singleton_factory()
        config.META.check_for_client_secret_and_import()
        config.GOOGLE = GoogleClient()
        setup_database()
        self.scraper = HomebaseScheduleScraper(
            config.HOMEBASE_USERNAME,
            config.HOMEBASE_PASSWORD,
            config.EMPLOYEE_FIRSTNAME,
            config.EMPLOYEE_LASTNAME,
            config.START_DATE,
            config.END_DATE,
        )
        self.primary_calendar = config.GOOGLE.get_primary_calendar()
        self.primary_calendar_events = config.GOOGLE.get_calendar_events(
            self.primary_calendar["id"]
        )
        self.primary_calendar_event_ids = {
            _["id"] for _ in self.primary_calendar_events
        }
        self.remote_homebase_shifts = json.loads(
            self.scraper.get_employee_shifts_json()
        )
        self.remote_homebase_shift_ids = {
            _["shiftId"] for _ in self.remote_homebase_shifts
        }
        self.remote_homebase_events = self.get_homebase_events()

    def __call__(self):
        self.update_events_db_from_remote()
        self.add_homebase_shifts()

    def get_event_hash(self, event: dict) -> str:
        event_str = json.dumps(event, sort_keys=True)
        return hashlib.sha512(event_str.encode("utf-8")).hexdigest()

    def update_events_db_from_remote(self):
        connect_database()

        for event in self.primary_calendar_events:
            event_id = event["id"]
            event_hash = self.get_event_hash(event)
            from_homebase = 0  # 0/1 - False/True
            homebase_shift_id = None

            homebase_event = event.get("source")
            if homebase_event:
                shift_id_source = homebase_event["title"].split("-")

                if len(shift_id_source) > 1 and shift_id_source[0] == "homebaseShiftId":
                    homebase_shift_id = shift_id_source[1]
                    from_homebase = 1

            config.DB_CURSOR.execute(
                "SELECT hash FROM events WHERE event_id = ?", (event_id,)
            )
            row = config.DB_CURSOR.fetchone()

            if row is None:
                config.DB_CURSOR.execute(
                    "INSERT INTO events (event_id, hash, from_homebase, homebase_shift_id) VALUES (?, ?, ?, ?)",
                    (event_id, event_hash, from_homebase, homebase_shift_id),
                )
                # print(f"New event added: {event_id}")
            elif row[0] != event_hash:
                config.DB_CURSOR.execute(
                    "UPDATE events SET hash = ? WHERE event_id = ?",
                    (event_hash, event_id),
                )
                print(f"Event updated: {event_id}")
            config.DB.commit()
        self.prune_events_table()

    def get_homebase_events(self) -> set:
        homebase_events = set()

        for _ in self.primary_calendar_events:
            if _.get("source"):
                shift_id_source = _["source"]["title"].split("-")

                if len(shift_id_source) > 1 and shift_id_source[0] == "homebaseShiftId":
                    homebase_events.add(shift_id_source[1])
        return homebase_events

    def add_homebase_shifts(self):
        connect_database()

        for shift in self.remote_homebase_shifts:
            shift_hash = self.get_event_hash(shift)
            config.DB_CURSOR.execute(
                "SELECT hash FROM shifts WHERE homebase_shift_id = ?",
                (shift["shiftId"],),
            )
            shifts_row = config.DB_CURSOR.fetchone()

            local_time = pendulum.now()
            start = pendulum.parse(
                f"{shift["shiftDate"]} {shift["startTime"]}",
                tz=local_time.timezone_name,
            )
            end = pendulum.parse(
                f"{shift["shiftDate"]} {shift["endTime"]}", tz=local_time.timezone_name
            )
            event = {
                "summary": f"Homebase - {shift["jobRole"]}",
                "description": f"{shift["firstName"]} {shift["lastName"]}",
                "start": {
                    "dateTime": start.to_iso8601_string(),
                    "timeZone": local_time.timezone_name,
                },
                "end": {
                    "dateTime": end.to_iso8601_string(),
                    "timeZone": local_time.timezone_name,
                },
                "source": {
                    "title": f"homebaseShiftId-{shift["shiftId"]}",
                    "url": "https://app.joinhomebase.com/",
                },
            }

            if shifts_row is None:
                config.DB_CURSOR.execute(
                    "INSERT INTO shifts (homebase_shift_id, hash) VALUES (?, ?)",
                    (shift["shiftId"], shift_hash),
                )
                print(f"New shift added: {shift_hash}")
                config.DB.commit()

                config.DB_CURSOR.execute(
                    "SELECT hash FROM events WHERE homebase_shift_id = ?",
                    (shift["shiftId"],),
                )
                events_row = config.DB_CURSOR.fetchone()

                if (
                    events_row is None
                    and shift["shiftId"] not in self.remote_homebase_events
                ):
                    event_result = config.GOOGLE.create_new_event(
                        self.primary_calendar["id"], event
                    )
                    config.DB_CURSOR.execute(
                        "INSERT INTO events (event_id, hash, from_homebase, homebase_shift_id) VALUES (?, ?, ?, ?)",
                        (
                            event_result["id"],
                            self.get_event_hash(event_result),
                            1,
                            shift["shiftId"],
                        ),
                    )
                    self.primary_calendar_events.append(event_result)
                    self.primary_calendar_event_ids.add(event_result["id"])
                    config.DB.commit()
            elif shifts_row[0] != shift_hash:
                config.DB_CURSOR.execute(
                    "UPDATE shifts SET hash = ? WHERE homebase_shift_id = ?",
                    (shift_hash, shift["shiftId"]),
                )
                print(f"Shift updated: {shift_hash}")
                # TODO: for CRUD operations, this is where integration code for UPDATES to
                # TODO  homebase's shift times would be processed.
                config.DB.commit()
            else:
                if shift["shiftId"] not in self.remote_homebase_events:
                    event_result = config.GOOGLE.create_new_event(
                        self.primary_calendar["id"], event
                    )
                    config.DB_CURSOR.execute(
                        "INSERT INTO events (event_id, hash, from_homebase, homebase_shift_id) VALUES (?, ?, ?, ?)",
                        (
                            event_result["id"],
                            self.get_event_hash(event_result),
                            1,
                            shift["shiftId"],
                        ),
                    )
                    self.primary_calendar_events.append(event_result)
                    self.primary_calendar_event_ids.add(event_result["id"])
                    config.DB.commit()
        self.prune_shifts_table()
        config.DB.commit()

    def prune_events_table(self):
        # Prune Local Events to match remote
        config.DB_CURSOR.execute("SELECT event_id FROM events")
        local_events = {row[0] for row in config.DB_CURSOR.fetchall()}
        events_to_delete = local_events - self.primary_calendar_event_ids
        for event_id in events_to_delete:
            config.DB_CURSOR.execute(
                "DELETE FROM events WHERE event_id = ?", (event_id,)
            )
            print(f"Event deleted: {event_id}")
        config.DB.commit()

    def prune_shifts_table(self):
        # Prune Local Shifts to match remote
        config.DB_CURSOR.execute("SELECT homebase_shift_id FROM shifts")
        local_shifts = {row[0] for row in config.DB_CURSOR.fetchall()}
        shifts_to_delete = local_shifts - self.remote_homebase_shift_ids
        for event_id in shifts_to_delete:
            config.DB_CURSOR.execute(
                "DELETE FROM shifts WHERE homebase_shift_id = ?", (event_id,)
            )
            print(f"Shift deleted: {event_id}")
        config.DB.commit()

    def remove_remote_homebase_events(self):
        connect_database()

        for shift_id in self.remote_homebase_events:
            config.DB_CURSOR.execute(
                "SELECT event_id FROM events WHERE homebase_shift_id = ?",
                (shift_id,),
            )
            event_id = config.DB_CURSOR.fetchone()[0]
            event_result = config.GOOGLE.remove_event(
                self.primary_calendar["id"], event_id
            )

            config.DB_CURSOR.execute(
                "DELETE FROM events WHERE event_id = ?", (event_id,)
            )
            config.DB.commit()

            config.DB_CURSOR.execute(
                "DELETE FROM shifts WHERE homebase_shift_id = ?", (shift_id,)
            )
            config.DB.commit()


def main():
    cli()
    sync = HomebaseCalendarSync()
    sync()

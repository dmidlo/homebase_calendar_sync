import os
import json
import httpx
from bs4 import BeautifulSoup
import pendulum
from pathlib import Path
from dotenv import load_dotenv
from rich import print
import sqlite3
import hashlib

import config
from db.models import setup_database, connect_database
from google_client.auth import Metadata
from google_client.google_client import GoogleClient

DOTENV_BASE_DIR = Path(__file__).parent
load_dotenv(Path(DOTENV_BASE_DIR, ".env"))

HOMEBASE_USERNAME = os.environ["CC_HOMEBASE_USERNAME"]
HOMEBASE_PASSWORD = os.environ["CC_HOMEBASE_PASSWORD"]
EMPLOYEE_FIRSTNAME = os.environ["CC_HOMEBASE_EMPLOYEE_FIRSTNAME"]
EMPLOYEE_LASTNAME = os.environ["CC_HOMEBASE_EMPLOYEE_LASTNAME"]
START_DATE = os.environ["CC_HOMEBASE_START_DATE"]
END_DATE = os.environ["CC_HOMEBASE_END_DATE"]

class HomebaseScheduleScraper:
    def __init__(self, username, password, first_name, last_name, start_date, end_date) -> None:
        self.username = username
        self.password = password
        self.start_date, self.end_date = self.initialize_date_range(start_date, end_date)
        self.login_url = "https://app.joinhomebase.com/accounts/sign-in"
        self.base_schedule_url = "https://app.joinhomebase.com/api/fe/schedule_builder/schedule?"
        self.client = httpx.Client()
        self.login_payload = {
            "authenticity_token": self.get_authenticity_token(),
            "account[login]": username,
            "account[password]": password,
            "account[remember_me]": 0
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
            html_content = BeautifulSoup(response.text, 'html.parser')

            return html_content.find('form', method='post')
        else:
            print(f"Failed to retrieve the page. Status Code: {response.status_code}")

    def get_authenticity_token(self):
        login_form = self.get_login_form()
        if login_form:
            input_element = login_form.find('input', attrs={'name':'authenticity_token', 'type':'hidden'})
            return input_element.get('value')
        else:
            print("No input element with `name='authenticity_token'` found.")

    def login(self):
        response = self.client.post(self.login_url, data=self.login_payload)

        if response.status_code == 200:
            print(f"Homebase Login Successful. Status Code: {response.status_code}")
        else:
            print(f"Homebase Login failed. Status Code: {response.status_code}")

    def get_schedule_route(self):
        return f"{self.base_schedule_url}end_date={self.end_date.to_date_string()}&start_date={self.start_date.to_date_string()}"
    
    def get_calendar_json(self):
        response = self.client.get(self.get_schedule_route())

        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to retrieve the page. Status Code: {response.status_code}")

    def get_employee_id(self):
        for _ in self.calendar_json["included"]:
            if _["type"] == "user" \
            and (str(_["attributes"]["firstName"]).lower() == self.employee_first_name.lower() \
            and str(_["attributes"]["lastName"]).lower() == self.employee_last_name.lower()):
                return _["id"]
            
    def get_employee_jobs(self):
        return [_["id"] for _ in self.calendar_json["included"] if _["type"] == "job" and _["relationships"]["user"]["data"]["id"] == self.employee_id]

    def get_employee_shifts(self):
        return (_ for _ in self.calendar_json["included"] if _["type"] == "shift" and _["relationships"]["owner"]["data"]["id"] in self.employee_jobs)

    def initialize_date_range(self, start_date, end_date):
        if start_date == 'today':
            start = pendulum.now().start_of("day")
        else:
            start = pendulum.parse(start_date).start_of("day")
        if end_date == "today":
            end = pendulum.now().end_of("day")
        else:
            end = pendulum.parse(end_date).end_of("day")
    
        return start, end

    def filter_shifts_by_date(self):
        return (_ for _ in self.employee_shifts if self.start_date <= pendulum.parse(_["attributes"]["startAt"]) <= self.end_date)

    def get_employee_shifts_json(self):
        shifts = []

        for _ in self.employee_shifts_in_range:
            shift = {
                "shiftId": _["id"],
                "firstName": self.employee_first_name,
                "lastName": self.employee_last_name,
                "jobRole": _["attributes"]["roleName"],
                "shiftDate": pendulum.parse(_["attributes"]["startAt"]).to_date_string(),
                "startTime": pendulum.parse(_["attributes"]["startAt"]).to_time_string(),
                "endTime": pendulum.parse(_["attributes"]["endAt"]).to_time_string()
            }

            shifts.append(shift)

        return json.dumps(shifts)
    
class HomebaseCalendarSync:
    def __init__(self) -> None:
        setup_database()
        self.scraper = HomebaseScheduleScraper(
            HOMEBASE_USERNAME,
            HOMEBASE_PASSWORD,
            EMPLOYEE_FIRSTNAME,
            EMPLOYEE_LASTNAME,
            START_DATE,
            END_DATE
        )
        self.primary_calendar = config.GOOGLE.get_primary_calendar()
        self.primary_calendar_events = config.GOOGLE.get_calendar_events(self.primary_calendar["id"])
    
    def __call__(self):
        self.update_events_db_from_remote()
        self.add_homebase_shifts()

    def get_event_hash(self, event: dict) -> str:
        event_str = json.dumps(event, sort_keys=True)
        return hashlib.sha512(event_str.encode("utf-8")).hexdigest()
    
    def update_events_db_from_remote(self):
        connect_database()
        remote_events = set()
        
        # Insert or Update Remote Events
        for event in self.primary_calendar_events:
            event_id = event["id"]
            event_hash = self.get_event_hash(event)
            remote_events.add(event_id)
            from_homebase = 0  # 0/1 - False/True
            homebase_shift_id = None

            homebase_event = event.get("source")
            if homebase_event:
                shift_id_source = homebase_event["title"].split("-")
                
                if len(shift_id_source) > 1 and shift_id_source[0] == "homebaseShiftId":
                    homebase_shift_id = shift_id_source[1]
                    from_homebase = 1

            config.DB_CURSOR.execute('SELECT hash FROM events WHERE event_id = ?', (event_id,))
            row = config.DB_CURSOR.fetchone()

            if row is None:
                config.DB_CURSOR.execute('INSERT INTO events (event_id, hash, from_homebase, homebase_shift_id) VALUES (?, ?, ?, ?)', (event_id, event_hash, from_homebase, homebase_shift_id))
                print(f"New event added: {event_id}")
            elif row[0] != event_hash:
                config.DB_CURSOR.execute('UPDATE events SET hash = ? WHERE event_id = ?', (event_hash, event_id))
                print(f"Event updated: {event_id}")

        # Prune Local Events to match remote
        config.DB_CURSOR.execute('SELECT event_id FROM events')
        local_events = {row[0] for row in config.DB_CURSOR.fetchall()}
        events_to_delete = local_events - remote_events
        for event_id in events_to_delete:
            config.DB_CURSOR.execute('DELETE FROM events WHERE event_id = ?', (event_id,))
            print(f"Event deleted: {event_id}")

        config.DB.commit()
        config.DB.close()

    def get_homebase_events(self) -> set:
        homebase_events = set()

        for _ in self.primary_calendar_events:
            if _.get("source"):
                shift_id_source = _["source"]["title"].split("-")
                
                if len(shift_id_source) > 1 and shift_id_source[0] == "homebaseShiftId":
                    homebase_events.add(shift_id_source[1])
        return homebase_events

    def add_homebase_shifts(self):
        homebase_shifts = json.loads(self.scraper.get_employee_shifts_json())
        connect_database()


        for shift in homebase_shifts:
            config.DB_CURSOR.execute('SELECT hash FROM events WHERE homebase_shift_id = ?', (shift["shiftId"],))
            row = config.DB_CURSOR.fetchone()

            if row is None and shift["shiftId"] not in self.get_homebase_events():
                local_time = pendulum.now()
                start = pendulum.parse(f"{shift["shiftDate"]} {shift["startTime"]}", tz=local_time.timezone_name)
                end = pendulum.parse(f"{shift["shiftDate"]} {shift["endTime"]}", tz=local_time.timezone_name)

                event = {
                    "summary": f"Homebase - {shift["jobRole"]}",
                    "description": f"{shift["firstName"]} {shift["lastName"]}",
                    "start": {
                        "dateTime": start.to_iso8601_string(),
                        "timeZone": local_time.timezone_name
                    },
                    "end": {
                        "dateTime": end.to_iso8601_string(),
                        "timeZone": local_time.timezone_name
                    },
                    "source": {
                        "title": f"homebaseShiftId-{shift["shiftId"]}",
                        "url": "https://app.joinhomebase.com/"
                    },
                }

                config.GOOGLE.create_new_event(self.primary_calendar["id"], event)
                self.update_events_db_from_remote()



def main():
    config.META = Metadata.metadata_singleton_factory()
    config.META.check_for_client_secret_and_import()
    config.GOOGLE = GoogleClient()
    sync = HomebaseCalendarSync()
    sync()

if __name__ == "__main__":
    main()

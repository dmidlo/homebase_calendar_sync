import os
import json
import httpx
from bs4 import BeautifulSoup
import pendulum
from pathlib import Path
from dotenv import load_dotenv
from rich import print

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
                "firstName": self.employee_first_name,
                "lastName": self.employee_last_name,
                "jobRole": _["attributes"]["roleName"],
                "shiftDate": pendulum.parse(_["attributes"]["startAt"]).to_date_string(),
                "startTime": pendulum.parse(_["attributes"]["startAt"]).to_time_string(),
                "endTime": pendulum.parse(_["attributes"]["endAt"]).to_time_string()
            }

            shifts.append(shift)

        return json.dumps(shifts)
    
def main():
    scraper = HomebaseScheduleScraper(
        HOMEBASE_USERNAME,
        HOMEBASE_PASSWORD,
        EMPLOYEE_FIRSTNAME,
        EMPLOYEE_LASTNAME,
        START_DATE,
        END_DATE
    )
    print(scraper.get_employee_shifts_json())

if __name__ == "__main__":
    main()

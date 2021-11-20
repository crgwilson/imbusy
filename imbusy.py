import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Sequence

from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build


@dataclass
class Calendar:
    id: str
    summary: str
    time_zone: str
    access_role: str

    @classmethod
    def from_dict(cls, calendar_dict: Dict) -> "Calendar":
        return cls(
            id=calendar_dict["id"],
            summary=calendar_dict["summary"],
            time_zone=calendar_dict["timeZone"],
            access_role=calendar_dict["accessRole"],
        )


class CalendarApi(object):
    CALENDAR_SCOPE = ["https://www.googleapis.com/auth/calendar"]
    CALENDAR_API = "calendar"
    CALENDAR_API_VERSION = "v3"

    def __init__(self, flow: InstalledAppFlow) -> None:
        self._flow = flow
        self.creds = None
        self.service = None

    @property
    def calendars(self) -> List[Calendar]:
        return self._get_calendars()

    def get_calendar(self, attr_name: str, attr_val: str) -> Calendar:
        for calendar in self._get_calendars():
            found = getattr(calendar, attr_name)
            if found == attr_val:
                return calendar

        raise ValueError("No such calendar")

    def schedule_event(self, calendar_id: str, event: dict) -> None:
        self.service.events().insert(calendarId=calendar_id, body=event).execute()

    @lru_cache(maxsize=1)
    def _get_calendars(self) -> List[Calendar]:
        if not self.service:
            self._authenticate()

        calendars = []
        response = self.service.calendarList().list().execute()
        for r in response["items"]:
            calendars.append(Calendar.from_dict(r))

        return calendars

    def _authenticate(self) -> None:
        # TODO: Store the token we get back somewhere and make the auth flow overall less jank
        self.creds = self._flow.run_local_server(port=0)
        self.service = build(
            self.CALENDAR_API, self.CALENDAR_API_VERSION, credentials=self.creds
        )

    @classmethod
    def from_credentials_file(cls, file_path: str) -> "CalendarApi":
        flow = InstalledAppFlow.from_client_secrets_file(file_path, cls.CALENDAR_SCOPE)
        return cls(flow)


def get_current_timezone() -> str:
    # TODO: There is probably a way to format datetime.tzinfo correctly for this...
    with open("/etc/timezone") as f:
        return f.read().strip()


def create_oncall_event(
    start_time: datetime,
    comment: str,
    duration_in_hours: int = 168,
) -> Dict:
    end_time = start_time + timedelta(hours=duration_in_hours)

    start_str = start_time.isoformat()
    end_str = end_time.isoformat()

    local_tz = get_current_timezone()

    return {
        "summary": f"Oncall shift {comment}: {start_str} - {end_str}",
        "location": "",
        "start": {"dateTime": start_str, "timeZone": local_tz},
        "end": {
            "dateTime": end_str,
            "timeZone": local_tz,
        },
        "recurrence": [],
        "attendees": [],
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 60 * 24 * 14},
                {"method": "email", "minutes": 60 * 24 * 7},
                {"method": "popup", "minutes": 60},
            ],
        },
    }


def str_to_datetime(dt_str: str) -> datetime:
    DT_FORMAT = "%Y-%m-%d:%H:%M"
    return datetime.strptime(dt_str, DT_FORMAT)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="imbusy")
    parser.add_argument(
        "--verbose", action="store_true", default=False, help="Log all the things"
    )
    parser.add_argument(
        "--list-calendars",
        action="store_true",
        dest="list_calendars",
        default=False,
        help="List all available calendars",
    )

    subparsers = parser.add_subparsers(dest="oncall")
    oncall_parser = subparsers.add_parser(
        "oncall",
        help="Schedule an oncall shift",
    )
    oncall_parser.add_argument(
        "-s", "--start", type=str, required=True, help="When does the event start"
    )
    oncall_parser.add_argument(
        "-c",
        "--calendar",
        type=str,
        required=True,
        help="The name (summary) of the target google calendar",
    )
    oncall_parser.add_argument(
        "-C",
        "--comment",
        type=str,
        default="",
        required=False,
        help="Additional comments to add to the created event",
    )

    scheduling_group = oncall_parser.add_mutually_exclusive_group()
    scheduling_group.add_argument(
        "-H",
        "--hours",
        type=int,
        default=168,
        required=False,
        help="How long will the event last",
    )
    args = parser.parse_args(argv)

    api = CalendarApi.from_credentials_file("credentials.json")

    if args.list_calendars:
        for c in api.calendars:
            print(c)
    elif args.oncall:
        start_time = datetime.strptime(args.start, "%Y-%m-%d:%H:%M")
        target_calendar = api.get_calendar(attr_name="summary", attr_val=args.calendar)

        event = create_oncall_event(start_time, args.comment, args.hours)
        api.schedule_event(target_calendar.id, event)
    else:
        parser.print_help()

    return 0

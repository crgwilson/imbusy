from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

import imbusy


@pytest.mark.parametrize(
    "dt_str,expected",
    [
        ("2021-01-02:10:30", datetime(2021, 1, 2, 10, 30)),
        ("2021-01-02:16:00", datetime(2021, 1, 2, 16)),
    ],
)
def test_str_to_datetime(dt_str, expected):
    got = imbusy.str_to_datetime(dt_str)
    assert got == expected


@patch("imbusy.get_current_timezone", MagicMock(return_value="America/New_York"))
def test_create_oncall_event():
    start_time = datetime(2021, 1, 1, 14)

    got = imbusy.create_oncall_event(start_time, "unit test")
    assert got == {
        "summary": "Oncall shift unit test: 2021-01-01T14:00:00 - 2021-01-08T14:00:00",
        "location": "",
        "start": {"dateTime": "2021-01-01T14:00:00", "timeZone": "America/New_York"},
        "end": {
            "dateTime": "2021-01-08T14:00:00",
            "timeZone": "America/New_York",
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

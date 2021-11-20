# imbusy

[![Run tests](https://github.com/crgwilson/imbusy/actions/workflows/tests.yml/badge.svg)](https://github.com/crgwilson/imbusy/actions/workflows/tests.yml)

Schedule events (mainly on-call shifts) onto a shared google calendar so my family
will stop asking me about it :)

## Pre-requisites

This CLI uses Google's calendar API to schedule events, follow their [documentation](https://developers.google.com/calendar/api/guides/auth)
to create the necessary credentials.

## Testing

Tests & linting for this project are done using tox

```console
foo@bar: tox
```

## TODO

- [ ] Cache the auth token received from google
- [ ] De-jankify the whole auth flow

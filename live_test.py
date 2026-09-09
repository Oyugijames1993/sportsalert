"""
Standalone live-polling test — Napoli vs Arsenal, Champions League,
9 September 2026, kickoff 19:00 UTC.

Polls the /fixtures?live=all endpoint every 90 seconds, filters for the
Napoli-Arsenal fixture, and prints score/status/events as they change.
Not yet wired into the Django models — this validates the API data flow
live before we build the full football version of the app.

Run with: python live_test.py
Stop with: Ctrl+C
POLL_SECONDS below is adjustable — lower it once on a paid plan with a
higher rate limit.
"""
import time
import requests
from datetime import datetime

API_KEY = "56d8769ae56d7f1ceb68d6fa8cddea88"
URL = "https://v3.football.api-sports.io/fixtures"
HEADERS = {"x-apisports-key": API_KEY}
POLL_SECONDS = 90

TEAM_NAMES = {"napoli", "arsenal"}


def find_our_fixture(fixtures):
    for f in fixtures:
        home = f["teams"]["home"]["name"].lower()
        away = f["teams"]["away"]["name"].lower()
        if home in TEAM_NAMES and away in TEAM_NAMES:
            return f
    return None


def print_snapshot(f, seen_event_keys):
    status = f["fixture"]["status"]
    home = f["teams"]["home"]["name"]
    away = f["teams"]["away"]["name"]
    goals_h = f["goals"]["home"]
    goals_a = f["goals"]["away"]
    now = datetime.now().strftime("%H:%M:%S")

    print(f"[{now}] {home} {goals_h}-{goals_a} {away} | {status['long']} "
          f"({status['elapsed']}')")

    for ev in f.get("events", []):
        key = (ev["time"]["elapsed"], ev["time"]["extra"], ev["type"],
               ev["team"]["name"], ev["player"]["name"])
        if key not in seen_event_keys:
            seen_event_keys.add(key)
            minute = ev["time"]["elapsed"]
            extra = f"+{ev['time']['extra']}" if ev["time"]["extra"] else ""
            print(f"    ⚽ {minute}{extra}' [{ev['team']['name']}] "
                  f"{ev['type']}: {ev['detail']} — {ev['player']['name']}")


def main():
    print("Polling for Napoli vs Arsenal... (Ctrl+C to stop)")
    seen_event_keys = set()
    request_count = 0

    while True:
        try:
            resp = requests.get(URL, headers=HEADERS, params={"live": "all"}, timeout=10)
            request_count += 1
            data = resp.json()

            if data.get("errors"):
                print(f"API error: {data['errors']}")
            else:
                fixture = find_our_fixture(data.get("response", []))
                if fixture:
                    print_snapshot(fixture, seen_event_keys)
                    if fixture["fixture"]["status"]["short"] in ("FT", "AET", "PEN"):
                        print("Match finished. Stopping.")
                        break
                else:
                    now = datetime.now().strftime("%H:%M:%S")
                    print(f"[{now}] Napoli vs Arsenal not live yet "
                          f"(requests used today: {request_count})")

        except Exception as e:
            print(f"Request failed: {e}")

        time.sleep(POLL_SECONDS)

    print(f"\nTotal requests used this run: {request_count}")


if __name__ == "__main__":
    main()

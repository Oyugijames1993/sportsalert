"""
Polls API-Football for tracked football matches and evaluates each
StatAlertRule (silence / burst) configured on them.

Uses TWO API calls per watch per poll cycle:
  1. /fixtures?id={match_id}       — current match status (to know when to
                                      stop polling a finished match)
  2. /fixtures/statistics?fixture={match_id} — per-team stat totals

This is double the request cost of the basketball monitor_matches.py
command (which used one call per watch). Factor this into your polling
interval / how many matches you track simultaneously on the free tier
(100 requests/day).

If a chosen stat_type isn't covered by the API for a given match/league
(e.g. throw-ins, goal kicks — not part of API-Football's standard list),
the API simply won't return that stat — no error, it's just not tracked
for that match, matching the intended graceful behavior.

Run with: python manage.py poll_football_stats
Typically scheduled on a loop by run_scheduler.py, same as the basketball
monitor_matches command.
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from monitoring.models import Watch, StatAlertRule, StatOccurrence, StatAlert

API_BASE = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": settings.API_SPORTS_KEY}

# Maps our internal stat_type choices to the exact "type" strings
# API-Football uses in its /fixtures/statistics response.
STAT_TYPE_TO_API_LABEL = {
    'shots_on_goal':    'Shots on Goal',
    'shots_off_goal':   'Shots off Goal',
    'total_shots':      'Total Shots',
    'blocked_shots':    'Blocked Shots',
    'shots_insidebox':  'Shots insidebox',
    'shots_outsidebox': 'Shots outsidebox',
    'fouls':            'Fouls',
    'corner_kicks':     'Corner Kicks',
    'offsides':         'Offsides',
    'yellow_cards':     'Yellow Cards',
    'red_cards':        'Red Cards',
    'goalkeeper_saves': 'Goalkeeper Saves',
    'total_passes':     'Total passes',
    'passes_accurate':  'Passes accurate',
    # Not part of API-Football's standard list — included in case a
    # specific competition (e.g. Champions League) happens to provide
    # them. If absent from the response, these are just never tracked.
    'throw_ins':         'Throw-ins',
    'goal_kicks':        'Goal Kicks',
}

FINISHED_STATUSES = {"FT", "AET", "PEN", "PST", "CANC", "ABD", "AWD", "WO"}


class Command(BaseCommand):
    help = "Poll live football matches and evaluate stat alert rules"

    def handle(self, *args, **kwargs):
        now = timezone.now()
        watches = Watch.objects.filter(
            sport='football',
            active=True,
            monitoring_finished=False,
            monitoring_start__lte=now,
        )
        self.stdout.write(f"Found {watches.count()} football watch(es) ready for monitoring")

        for watch in watches:
            try:
                self._poll_watch(watch, now)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error polling watch {watch.id}: {e}"))

        self.stdout.write(self.style.SUCCESS("\nFootball polling complete"))

    def _poll_watch(self, watch, now):
        self.stdout.write(f"\nChecking fixture {watch.match_id} ({watch})")

        # ── 1. Fixture status ──────────────────────────────────────────
        status_resp = requests.get(
            f"{API_BASE}/fixtures",
            headers=HEADERS,
            params={"id": watch.match_id},
            timeout=10,
        ).json()

        fixtures = status_resp.get("response", [])
        if not fixtures:
            self.stdout.write("  No fixture data returned — skipping this cycle.")
            return

        fixture_data = fixtures[0]
        status_short = fixture_data["fixture"]["status"]["short"]
        watch.game_status = status_short
        watch.last_polled = now
        if not watch.monitoring_started:
            watch.monitoring_started = True

        if status_short in FINISHED_STATUSES:
            watch.monitoring_finished = True
            watch.active = False
            watch.save()
            self.stdout.write(self.style.SUCCESS(
                f"  Fixture {watch.match_id} finished ({status_short}). Monitoring stopped."
            ))
            return

        watch.save()
        self.stdout.write(f"  Status: {status_short}")

        # ── 2. Statistics ───────────────────────────────────────────────
        rules = list(watch.stat_alert_rules.filter(active=True))
        if not rules:
            self.stdout.write("  No active stat alert rules on this watch — skipping stats call.")
            return

        stats_resp = requests.get(
            f"{API_BASE}/fixtures/statistics",
            headers=HEADERS,
            params={"fixture": watch.match_id},
            timeout=10,
        ).json()

        stats_response = stats_resp.get("response", [])
        if len(stats_response) < 2:
            self.stdout.write("  No statistics coverage for this fixture yet — skipping.")
            return

        # API-Football's documented convention: home team first, away
        # team second, in fixture order.
        team_blocks = {"home": stats_response[0], "away": stats_response[1]}

        for rule in rules:
            teams_to_check = ["home", "away"] if rule.team_scope == "both" else [rule.team_scope]
            api_label = STAT_TYPE_TO_API_LABEL.get(rule.stat_type)
            if not api_label:
                continue

            for team in teams_to_check:
                value = self._extract_stat_value(team_blocks[team], api_label)
                if value is None:
                    # Not provided for this match/competition — skip silently.
                    continue

                self._record_occurrence_if_increased(watch, rule.stat_type, team, value)

            self._evaluate_rule(watch, rule, now)

    def _extract_stat_value(self, team_block, api_label):
        for stat in team_block.get("statistics", []):
            if stat.get("type") == api_label:
                raw = stat.get("value")
                if raw is None:
                    return None
                # API-Football sometimes returns percentages as strings
                # like "54%" for possession — only handle plain integers
                # here since none of our tracked types are percentages.
                try:
                    return int(raw)
                except (TypeError, ValueError):
                    return None
        return None

    def _record_occurrence_if_increased(self, watch, stat_type, team, value):
        last = (
            StatOccurrence.objects
            .filter(watch=watch, stat_type=stat_type, team=team)
            .order_by('-detected_at')
            .first()
        )
        last_value = last.value_at_time if last else 0
        if value > last_value:
            StatOccurrence.objects.create(
                watch=watch,
                stat_type=stat_type,
                team=team,
                value_at_time=value,
            )
            self.stdout.write(f"    New occurrence: {stat_type} ({team}) {last_value} -> {value}")

    def _evaluate_rule(self, watch, rule, now):
        teams_to_check = ["home", "away"] if rule.team_scope == "both" else [rule.team_scope]

        if rule.mode == "silence":
            for team in teams_to_check:
                last = (
                    StatOccurrence.objects
                    .filter(watch=watch, stat_type=rule.stat_type, team=team)
                    .order_by('-detected_at')
                    .first()
                )
                if not last:
                    continue  # nothing recorded yet — no baseline to measure silence from
                gap_minutes = (now - last.detected_at).total_seconds() / 60
                if gap_minutes < rule.silence_gap_minutes:
                    continue
                # Already fired since this occurrence? Don't repeat.
                already_fired = StatAlert.objects.filter(
                    rule=rule, alert_type='silence', created_at__gte=last.detected_at
                ).exists()
                if already_fired:
                    continue
                message = (
                    f"{watch}: no new {rule.get_stat_type_display()} ({team}) "
                    f"for {int(gap_minutes)} minutes (threshold {rule.silence_gap_minutes}m)."
                )
                StatAlert.objects.create(
                    watch=watch, rule=rule, alert_type='silence', message=message
                )
                self.stdout.write(self.style.WARNING(f"  ALERT (silence): {message}"))

        elif rule.mode == "burst":
            window_start = now - timezone.timedelta(minutes=rule.burst_window_minutes)
            for team in teams_to_check:
                count = StatOccurrence.objects.filter(
                    watch=watch, stat_type=rule.stat_type, team=team,
                    detected_at__gte=window_start,
                ).count()
                if count < rule.burst_count:
                    continue
                already_fired = StatAlert.objects.filter(
                    rule=rule, alert_type='burst', created_at__gte=window_start
                ).exists()
                if already_fired:
                    continue
                message = (
                    f"{watch}: {count} {rule.get_stat_type_display()} ({team}) "
                    f"in the last {rule.burst_window_minutes} minutes (threshold {rule.burst_count})."
                )
                StatAlert.objects.create(
                    watch=watch, rule=rule, alert_type='burst', message=message
                )
                self.stdout.write(self.style.WARNING(f"  ALERT (burst): {message}"))

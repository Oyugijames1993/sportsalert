"""
Polls API-Football for tracked football matches and evaluates:
  - StatAlertRule (silence / burst) — optional, per-stat alert rules
  - StatOddsModel (confidence) — fires when any line's live-projected
    fair win probability crosses the user's chosen confidence threshold

Uses TWO API calls per watch per poll cycle:
  1. /fixtures?id={match_id}       — current match status (to know when to
                                      stop polling a finished match)
  2. /fixtures/statistics?fixture={match_id} — per-team stat totals

If a chosen stat_type isn't covered by the API for a given match/league
(e.g. throw-ins, goal kicks — not part of API-Football's standard list),
the API simply won't return that stat — no error, it's just not tracked
for that match.

Run with: python manage.py poll_football_stats
Typically scheduled on a loop by run_football_scheduler.py.
"""
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from monitoring.models import Watch, StatOccurrence, StatAlert
from monitoring import odds_model

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
    help = "Poll live football matches, track stats, and evaluate alert rules"

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
        watch.elapsed_minutes = fixture_data["fixture"]["status"].get("elapsed")
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
        odds_rows = list(watch.stat_odds_models.all())

        if not rules and not odds_rows:
            self.stdout.write("  No stat alert rules or odds models on this watch — skipping stats call.")
            return

        stat_types_needed = set(r.stat_type for r in rules) | set(o.stat_type for o in odds_rows)

        # total_goals is a special case — it comes from the fixture STATUS
        # call (already fetched above), not the statistics endpoint like
        # every other tracked stat, so it's handled before we even decide
        # whether a statistics call is needed at all.
        if 'total_goals' in stat_types_needed:
            goals = fixture_data.get('goals', {})
            for team in ('home', 'away'):
                value = goals.get(team)
                if value is not None:
                    self._record_occurrence_if_increased(watch, 'total_goals', team, value)

        other_stat_types = stat_types_needed - {'total_goals'}
        if not other_stat_types:
            self.stdout.write("  Only total_goals tracked — statistics call not needed this cycle.")
            for rule in rules:
                self._evaluate_rule(watch, rule, now)
            t = watch.elapsed_minutes or 0
            for row in odds_rows:
                self._evaluate_confidence(watch, row, t)
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

        # Possession is captured whenever a statistics call happens
        # anyway, regardless of whether it's in other_stat_types — it's
        # display-only, not opt-in like the alert/odds-board stats.
        for team in ("home", "away"):
            value = self._extract_possession_value(team_blocks[team])
            if value is not None:
                self._record_possession(watch, team, value)

        for stat_type in other_stat_types:
            api_label = STAT_TYPE_TO_API_LABEL.get(stat_type)
            if not api_label:
                continue
            for team in ("home", "away"):
                value = self._extract_stat_value(team_blocks[team], api_label)
                if value is None:
                    continue  # not provided for this match/competition — skip silently
                self._record_occurrence_if_increased(watch, stat_type, team, value)

        for rule in rules:
            self._evaluate_rule(watch, rule, now)

        t = watch.elapsed_minutes or 0
        for row in odds_rows:
            self._evaluate_confidence(watch, row, t)

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

    def _extract_possession_value(self, team_block):
        for stat in team_block.get("statistics", []):
            if stat.get("type") == "Ball Possession":
                raw = stat.get("value")
                if raw is None:
                    return None
                try:
                    return int(str(raw).replace("%", "").strip())
                except (TypeError, ValueError):
                    return None
        return None

    def _record_possession(self, watch, team, value):
        """
        Unlike _record_occurrence_if_increased, possession can go up or
        down — so this records a new point whenever the value CHANGES at
        all, not just when it increases. Reuses the StatOccurrence table
        (stat_type='possession') purely as a time-series log; it isn't
        used by any silence/burst rule or odds board.
        """
        last = (
            StatOccurrence.objects
            .filter(watch=watch, stat_type='possession', team=team)
            .order_by('-detected_at')
            .first()
        )
        if last is None or last.value_at_time != value:
            StatOccurrence.objects.create(
                watch=watch,
                stat_type='possession',
                team=team,
                value_at_time=value,
            )

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

    def _evaluate_confidence(self, watch, row, t):
        """
        Computes the live odds board for this StatOddsModel row and fires
        a confidence alert the first time any line's fair win probability
        (Over or Under) reaches the user's chosen threshold. Dedup is by
        checking whether an alert already exists mentioning that exact
        line+side for this odds_model row — so each specific line only
        ever fires once, but a newly-safe line as the match progresses
        still fires fresh.
        """
        latest_home = (
            StatOccurrence.objects
            .filter(watch=watch, stat_type=row.stat_type, team='home')
            .order_by('-detected_at').first()
        )
        latest_away = (
            StatOccurrence.objects
            .filter(watch=watch, stat_type=row.stat_type, team='away')
            .order_by('-detected_at').first()
        )
        k = (latest_home.value_at_time if latest_home else 0) + \
            (latest_away.value_at_time if latest_away else 0)

        try:
            r = odds_model.get_dispersion_r(row.stat_type, row.dispersion_r)
            board = odds_model.odds_board(mu_0=row.mu_0, r=r, t=t, k=k, overround=row.overround)
        except (ValueError, ZeroDivisionError):
            return

        for line_row in board['rows']:
            p_over = line_row['p_over_fair']
            p_under = 1 - p_over

            for side, prob in (('Over', p_over), ('Under', p_under)):
                if prob < row.confidence_threshold:
                    continue
                signature = f"{side} {line_row['label'].split()[-1]}"  # e.g. "Over 21"
                already_fired = StatAlert.objects.filter(
                    odds_model=row, alert_type='confidence', message__icontains=signature
                ).exists()
                if already_fired:
                    continue
                message = (
                    f"{watch}: {row.get_stat_type_display()} — {signature} "
                    f"has reached {prob*100:.0f}% confidence (threshold {row.confidence_threshold*100:.0f}%)."
                )
                StatAlert.objects.create(
                    watch=watch, odds_model=row, alert_type='confidence', message=message
                )
                self.stdout.write(self.style.WARNING(f"  ALERT (confidence): {message}"))

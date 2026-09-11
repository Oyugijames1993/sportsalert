from django.db import models
class Watch(models.Model):

    SPORT_CHOICES = (
        ('basketball', 'Basketball'),
        ('football', 'Football'),
    )

    sport = models.CharField(
        max_length=20,
        choices=SPORT_CHOICES
    )

    match_id = models.CharField(
        max_length=100
    )

    home_team = models.CharField(
        max_length=100,
        blank=True
    )

    away_team = models.CharField(
        max_length=100,
        blank=True
    )

    league = models.CharField(
        max_length=100,
        blank=True
    )

    active = models.BooleanField(
        default=True
    )

    monitoring_start = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Time monitoring should begin"
    )

    monitoring_started = models.BooleanField(
        default=False
    )

    monitoring_finished = models.BooleanField(
        default=False
    )

    game_status = models.CharField(
        max_length=20,
        blank=True,
        default=""
    )

    elapsed_minutes = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    last_polled = models.DateTimeField(
        null=True,
        blank=True
    )

    total_game_minutes = models.IntegerField(
        default=40
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"{self.home_team} vs "
            f"{self.away_team}"
        )

class WatchParameter(models.Model):

    PARAMETER_CHOICES = (
        ('total_points', 'Total Points'),
        ('home_points', 'Home Team Points'),
        ('away_points', 'Away Team Points'),
        ('three_points_made', '3PT Made'),
        ('three_points_attempted', '3PT Attempted'),
        ('two_points_made', '2PT Made'),
        ('two_points_attempted', '2PT Attempted'),
    )

    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE,
        related_name="parameters"
    )

    parameter = models.CharField(
        max_length=50,
        choices=PARAMETER_CHOICES
    )

    baseline = models.FloatField()

    threshold = models.FloatField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = (
            "watch",
            "parameter",
        )

    def __str__(self):
        return (
            f"{self.watch} - "
            f"{self.get_parameter_display()}"
        )


class MatchSnapshot(models.Model):

    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE,
        related_name="snapshots"
    )

    game_clock = models.CharField(
        max_length=20,
        blank=True
    )

    elapsed_seconds = models.IntegerField(
        default=0
    )

    minutes_played = models.FloatField(
        default=0
    )

    current_points = models.IntegerField(
        default=0
    )

    actual_scoring_rate = models.FloatField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]

class TeamStatistic(models.Model):

    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE,
        related_name="team_statistics"
    )

    team_id = models.IntegerField(
        null=True,
        blank=True
    )

    team_name = models.CharField(
        max_length=100
    )

    points = models.IntegerField(
        default=0
    )

    # ---------- Raw API Statistics ----------

    field_goal_points = models.IntegerField(
        default=0
    )

    field_goal_made = models.IntegerField(
        default=0
    )

    field_goal_attempted = models.IntegerField(
        default=0
    )

    field_goal_percentage = models.FloatField(
        default=0
    )

    three_pt_made = models.IntegerField(
        default=0
    )

    three_pt_attempted = models.IntegerField(
        default=0
    )

    three_pt_percentage = models.FloatField(
        default=0
    )

    free_throw_made = models.IntegerField(
        default=0
    )

    free_throw_attempted = models.IntegerField(
        default=0
    )

    free_throw_percentage = models.FloatField(
        default=0
    )

    rebounds = models.IntegerField(
        default=0
    )

    assists = models.IntegerField(
        default=0
    )

    steals = models.IntegerField(
        default=0
    )

    blocks = models.IntegerField(
        default=0
    )

    turnovers = models.IntegerField(
        default=0
    )

    # ---------- Derived Analytics ----------

    estimated_possessions = models.FloatField(
        default=0
    )

    points_per_possession = models.FloatField(
        default=0
    )

    offensive_rating = models.FloatField(
        default=0
    )

    pace = models.FloatField(
        default=0
    )

    projected_points = models.FloatField(
        default=0
    )

    # ---------- Snapshot Information ----------

    quarter = models.IntegerField(
        default=0
    )

    game_status = models.CharField(
        max_length=10,
        blank=True
    )

    game_minute = models.FloatField(
        default=0
    )

    game_clock = models.CharField(
        max_length=20,
        blank=True
    )

    elapsed_seconds = models.IntegerField(
        default=0
    )

    bookmaker_total = models.FloatField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]

    @property
    def shooting_percentage(self):

        if self.field_goal_attempted == 0:
            return 0

        return round(
            (
                self.field_goal_made /
                self.field_goal_attempted
            ) * 100,
            2
        )

    @property
    def two_pt_made(self):
        return self.field_goal_made - self.three_pt_made

    @property
    def two_pt_attempted(self):
        return (
                self.field_goal_attempted -
                self.three_pt_attempted
        )

    @property
    def two_pt_percentage(self):

        if self.two_pt_attempted == 0:
            return 0

        return round(
            (
                    self.two_pt_made /
                    self.two_pt_attempted
            ) * 100,
            2
        )

    def __str__(self):

        return (
            f"{self.team_name} "
            f"(Q{self.quarter}) "
            f"{self.points} pts"
        )
class Alert(models.Model):

    ALERT_TYPES = (
        ('UP', 'UP'),
        ('DOWN', 'DOWN'),
    )

    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE,
        related_name="alerts"
    )

    parameter = models.ForeignKey(
        WatchParameter,
        on_delete=models.CASCADE,
        related_name="alerts",
        null=True,
        blank=True
    )

    alert_type = models.CharField(
        max_length=10,
        choices=ALERT_TYPES
    )

    projection = models.FloatField()

    deviation = models.FloatField()

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.message



# ── Football stat-tracking (time-since-last / burst alerting) ────────────────
# A different alerting model from basketball's baseline/threshold deviation
# system above: rather than "is scoring pace ahead/behind projection", this
# tracks discrete countable events (fouls, shots, corners, etc.) and alerts
# on either (a) silence — no new occurrence of a stat for N minutes, or
# (b) burst — M or more occurrences within a rolling N-minute window.

class StatAlertRule(models.Model):

    STAT_TYPE_CHOICES = (
        ('shots_on_goal',    'Shots on Goal'),
        ('shots_off_goal',   'Shots off Goal'),
        ('total_shots',      'Total Shots'),
        ('blocked_shots',    'Blocked Shots'),
        ('shots_insidebox',  'Shots Inside Box'),
        ('shots_outsidebox', 'Shots Outside Box'),
        ('fouls',            'Fouls'),
        ('corner_kicks',     'Corner Kicks'),
        ('offsides',         'Offsides'),
        ('yellow_cards',     'Yellow Cards'),
        ('red_cards',        'Red Cards'),
        ('goalkeeper_saves', 'Goalkeeper Saves'),
        ('total_passes',     'Total Passes'),
        ('passes_accurate',  'Passes Accurate'),
        # Not part of API-Football's standard statistics list — included
        # per request in case a specific competition (e.g. Champions
        # League) happens to provide them. If the API returns no data for
        # these, they're simply never tracked — no error, no alert.
        ('throw_ins',        'Throw-ins'),
        ('goal_kicks',       'Goal Kicks'),
        # Sourced from the fixture STATUS call (goals.home/goals.away),
        # not the statistics endpoint like everything else here — see
        # poll_football_stats.py for the special handling this requires.
        ('total_goals',      'Total Goals'),
    )

    MODE_CHOICES = (
        ('silence', 'Silence — alert if no new occurrence for N minutes'),
        ('burst',   'Burst — alert if N or more occurrences within a window'),
    )

    TEAM_SCOPE_CHOICES = (
        ('both', 'Either team'),
        ('home', 'Home team only'),
        ('away', 'Away team only'),
    )

    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE,
        related_name='stat_alert_rules'
    )

    stat_type = models.CharField(
        max_length=30,
        choices=STAT_TYPE_CHOICES
    )

    team_scope = models.CharField(
        max_length=10,
        choices=TEAM_SCOPE_CHOICES,
        default='both'
    )

    mode = models.CharField(
        max_length=10,
        choices=MODE_CHOICES
    )

    # ── Silence mode ───────────────────────────────────────────────────
    silence_gap_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Alert if no new occurrence of this stat for this many minutes."
    )

    # ── Burst mode ─────────────────────────────────────────────────────
    burst_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of occurrences that triggers a burst alert."
    )
    burst_window_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Rolling time window (minutes) the burst count is measured over."
    )

    # User's own reference target for this stat's final count — not used
    # in any alert logic, just displayed alongside the running actual
    # total so the user can see the deviation at a glance.
    expected_total = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Your own expected/target total for this stat by full-time (reference only)."
    )

    active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('watch', 'stat_type', 'team_scope', 'mode')

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.mode == 'silence' and not self.silence_gap_minutes:
            raise ValidationError('Silence mode requires a gap (minutes) value.')
        if self.mode == 'burst' and not (self.burst_count and self.burst_window_minutes):
            raise ValidationError('Burst mode requires both a count and a window (minutes).')

    def __str__(self):
        if self.mode == 'silence':
            detail = f'silence {self.silence_gap_minutes}m'
        else:
            detail = f'burst {self.burst_count}/{self.burst_window_minutes}m'
        return f'{self.watch} — {self.get_stat_type_display()} ({detail})'


class StatOccurrence(models.Model):
    """
    One row per detected increase in a tracked stat's running total for one
    team. Polling compares the latest value from the API against the last
    known value for (watch, stat_type, team) and logs the delta here —
    this is what silence/burst rules are evaluated against.
    """
    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE,
        related_name='stat_occurrences'
    )

    stat_type = models.CharField(
        max_length=30,
        choices=StatAlertRule.STAT_TYPE_CHOICES
    )

    team = models.CharField(
        max_length=10,
        choices=(('home', 'Home'), ('away', 'Away')),
    )

    value_at_time = models.PositiveIntegerField(
        help_text="Cumulative stat total at the moment this occurrence was detected."
    )

    detected_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['detected_at']

    def __str__(self):
        return f'{self.watch} — {self.get_stat_type_display()} ({self.team}) = {self.value_at_time} @ {self.detected_at}'


class StatAlert(models.Model):

    ALERT_TYPE_CHOICES = (
        ('silence',    'Silence'),
        ('burst',      'Burst'),
        ('confidence', 'Confidence'),
    )

    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE,
        related_name='stat_alerts'
    )

    rule = models.ForeignKey(
        StatAlertRule,
        on_delete=models.CASCADE,
        related_name='fired_alerts',
        null=True,
        blank=True
    )

    # Used for alert_type='confidence' — links back to the odds-model row
    # (mu_0/r/overround) whose live-projected board crossed the threshold.
    odds_model = models.ForeignKey(
        'StatOddsModel',
        on_delete=models.CASCADE,
        related_name='fired_alerts',
        null=True,
        blank=True
    )

    alert_type = models.CharField(
        max_length=10,
        choices=ALERT_TYPE_CHOICES
    )

    message = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.message


class StatOddsModel(models.Model):
    """
    Holds the inputs needed to project a live, bookmaker-style 5-line odds
    board for one (watch, stat_type) pair — see monitoring/odds_model.py
    for the actual math.

    mu_0 is entered by the user per match (the pre-match expected total
    for this stat, read off a real bookmaker's odds ladder for this
    fixture). dispersion_r is NOT entered per match — it's a per-stat-type
    constant, fitted once from a representative odds ladder and reused
    across matches (see DEFAULT_DISPERSION_R in odds_model.py). It's still
    stored here (rather than hardcoded) so it can be overridden or
    refined later without a code change.
    """
    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE,
        related_name='stat_odds_models'
    )

    stat_type = models.CharField(
        max_length=30,
        choices=StatAlertRule.STAT_TYPE_CHOICES
    )

    mu_0 = models.FloatField(
        help_text="Pre-match expected total for this stat, from the bookmaker's own odds ladder for this match."
    )

    dispersion_r = models.FloatField(
        null=True,
        blank=True,
        help_text="Negative binomial dispersion for this stat. Leave blank to use the fitted per-stat default."
    )

    overround = models.FloatField(
        default=1.10,
        help_text="Bookmaker margin to reapply when pricing the live odds board, e.g. 1.10 = 10% overround."
    )

    confidence_threshold = models.FloatField(
        default=0.80,
        help_text="Fire a confidence alert once any line's fair win probability reaches this level, e.g. 0.80 = 80%."
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        unique_together = ('watch', 'stat_type')

    def __str__(self):
        return f'{self.watch} — {self.get_stat_type_display()} (mu_0={self.mu_0})'

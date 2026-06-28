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


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

    current_points = models.FloatField()

    expected_points = models.FloatField()

    live_deviation = models.FloatField()

    projection = models.FloatField()

    deviation = models.FloatField()

    minutes_played = models.FloatField()

    expected_scoring_rate = models.FloatField()

    actual_scoring_rate = models.FloatField()

    scoring_rate_deviation = models.FloatField()

    recent_scoring_rate = models.FloatField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]


class TeamStatistic(models.Model):

    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE
    )

    team_name = models.CharField(
        max_length=100
    )

    points = models.IntegerField(
        default=0
    )

    two_pt_made = models.IntegerField(
        default=0
    )

    two_pt_attempted = models.IntegerField(
        default=0
    )

    three_pt_made = models.IntegerField(
        default=0
    )

    three_pt_attempted = models.IntegerField(
        default=0
    )

    free_throw_made = models.IntegerField(
        default=0
    )

    free_throw_attempted = models.IntegerField(
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


class Alert(models.Model):

    ALERT_TYPES = (
        ('UP', 'UP'),
        ('DOWN', 'DOWN'),
    )

    watch = models.ForeignKey(
        Watch,
        on_delete=models.CASCADE
    )

    parameter = models.ForeignKey(
        WatchParameter,
        on_delete=models.CASCADE,
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


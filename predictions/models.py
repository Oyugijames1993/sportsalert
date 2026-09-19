from django.db import models


class CoachProfile(models.Model):

    coach_id = models.PositiveIntegerField(
        unique=True,
        null=True,
        blank=True
    )

    coach_name = models.CharField(max_length=200)

    # =========================
    # HOME PROFILE
    # =========================

    goals_home = models.FloatField(default=0)
    assists_home = models.FloatField(default=0)
    shots_home = models.FloatField(default=0)
    shots_on_target_home = models.FloatField(default=0)
    shots_inside_box_home = models.FloatField(default=0)
    shots_outside_box_home = models.FloatField(default=0)
    key_passes_home = models.FloatField(default=0)
    dribbles_home = models.FloatField(default=0)
    successful_dribbles_home = models.FloatField(default=0)
    offsides_home = models.FloatField(default=0)
    corners_home = models.FloatField(default=0)

    possession_home = models.FloatField(default=0)
    total_passes_home = models.FloatField(default=0)
    accurate_passes_home = models.FloatField(default=0)
    pass_accuracy_home = models.FloatField(default=0)

    tackles_home = models.FloatField(default=0)
    interceptions_home = models.FloatField(default=0)
    blocks_home = models.FloatField(default=0)
    duels_home = models.FloatField(default=0)
    duels_won_home = models.FloatField(default=0)
    fouls_home = models.FloatField(default=0)
    saves_home = models.FloatField(default=0)

    yellow_home = models.FloatField(default=0)
    red_home = models.FloatField(default=0)

    # =========================
    # AWAY PROFILE
    # =========================

    goals_away = models.FloatField(default=0)
    assists_away = models.FloatField(default=0)
    shots_away = models.FloatField(default=0)
    shots_on_target_away = models.FloatField(default=0)
    shots_inside_box_away = models.FloatField(default=0)
    shots_outside_box_away = models.FloatField(default=0)
    key_passes_away = models.FloatField(default=0)
    dribbles_away = models.FloatField(default=0)
    successful_dribbles_away = models.FloatField(default=0)
    offsides_away = models.FloatField(default=0)
    corners_away = models.FloatField(default=0)

    possession_away = models.FloatField(default=0)
    total_passes_away = models.FloatField(default=0)
    accurate_passes_away = models.FloatField(default=0)
    pass_accuracy_away = models.FloatField(default=0)

    tackles_away = models.FloatField(default=0)
    interceptions_away = models.FloatField(default=0)
    blocks_away = models.FloatField(default=0)
    duels_away = models.FloatField(default=0)
    duels_won_away = models.FloatField(default=0)
    fouls_away = models.FloatField(default=0)
    saves_away = models.FloatField(default=0)

    yellow_away = models.FloatField(default=0)
    red_away = models.FloatField(default=0)

    ppda_home = models.FloatField(default=0)
    ppda_away = models.FloatField(default=0)
    transition_to_shot_seconds_home = models.FloatField(default=0)
    transition_to_shot_seconds_away = models.FloatField(default=0)

    ppda_home = models.FloatField(default=0)
    ppda_away = models.FloatField(default=0)
    transition_to_shot_seconds_home = models.FloatField(default=0)
    transition_to_shot_seconds_away = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.coach_name

from monitoring.models import TeamStatistic


def get_team_snapshots(
    watch,
    team_id
):
    return (
        TeamStatistic.objects
        .filter(
            watch=watch,
            team_id=team_id
        )
        .order_by("created_at")
    )


def get_latest_snapshot(
    watch,
    team_id
):
    return (
        get_team_snapshots(
            watch,
            team_id
        ).last()
    )


def get_first_snapshot(
    watch,
    team_id
):
    return (
        get_team_snapshots(
            watch,
            team_id
        ).first()
    )


def get_snapshot_quarter(
    snapshot
):

    if snapshot.game_clock.startswith("Q1"):
        return 1

    if snapshot.game_clock.startswith("Q2"):
        return 2

    if snapshot.game_clock.startswith("Q3"):
        return 3

    if snapshot.game_clock.startswith("Q4"):
        return 4

    return None


def get_quarter_snapshots(
    watch,
    team_id,
    quarter
):

    snapshots = (
        get_team_snapshots(
            watch,
            team_id
        )
    )

    return [
        snapshot
        for snapshot in snapshots
        if (
            get_snapshot_quarter(
                snapshot
            ) == quarter
        )
    ]


def snapshot_difference(
    current,
    previous=None
):

    if previous is None:

        previous_values = {
            "points": 0,
            "field_goal_points": 0,
            "field_goal_made": 0,
            "field_goal_attempted": 0,
            "three_pt_made": 0,
            "three_pt_attempted": 0,
            "free_throw_made": 0,
            "free_throw_attempted": 0,
            "rebounds": 0,
            "assists": 0,
            "steals": 0,
            "blocks": 0,
            "turnovers": 0,
        }

    else:

        previous_values = {
            "points": previous.points,
            "field_goal_points": previous.field_goal_points,
            "field_goal_made": previous.field_goal_made,
            "field_goal_attempted": previous.field_goal_attempted,
            "three_pt_made": previous.three_pt_made,
            "three_pt_attempted": previous.three_pt_attempted,
            "free_throw_made": previous.free_throw_made,
            "free_throw_attempted": previous.free_throw_attempted,
            "rebounds": previous.rebounds,
            "assists": previous.assists,
            "steals": previous.steals,
            "blocks": previous.blocks,
            "turnovers": previous.turnovers,
        }

    result = {

        "points":
            current.points -
            previous_values["points"],

        "field_goal_points":
            current.field_goal_points -
            previous_values["field_goal_points"],

        "field_goal_made":
            current.field_goal_made -
            previous_values["field_goal_made"],

        "field_goal_attempted":
            current.field_goal_attempted -
            previous_values["field_goal_attempted"],

        "three_pt_made":
            current.three_pt_made -
            previous_values["three_pt_made"],

        "three_pt_attempted":
            current.three_pt_attempted -
            previous_values["three_pt_attempted"],

        "free_throw_made":
            current.free_throw_made -
            previous_values["free_throw_made"],

        "free_throw_attempted":
            current.free_throw_attempted -
            previous_values["free_throw_attempted"],

        "rebounds":
            current.rebounds -
            previous_values["rebounds"],

        "assists":
            current.assists -
            previous_values["assists"],

        "steals":
            current.steals -
            previous_values["steals"],

        "blocks":
            current.blocks -
            previous_values["blocks"],

        "turnovers":
            current.turnovers -
            previous_values["turnovers"],
    }

    if result["field_goal_attempted"] > 0:

        result["field_goal_percentage"] = round(
            (
                result["field_goal_made"] /
                result["field_goal_attempted"]
            ) * 100,
            2
        )

    else:

        result["field_goal_percentage"] = 0

    if result["three_pt_attempted"] > 0:

        result["three_pt_percentage"] = round(
            (
                result["three_pt_made"] /
                result["three_pt_attempted"]
            ) * 100,
            2
        )

    else:

        result["three_pt_percentage"] = 0

    if result["free_throw_attempted"] > 0:

        result["free_throw_percentage"] = round(
            (
                result["free_throw_made"] /
                result["free_throw_attempted"]
            ) * 100,
            2
        )

    else:

        result["free_throw_percentage"] = 0

    return result


def get_quarter_summary(
    watch,
    team_id,
    quarter
):

    snapshots = (
        get_quarter_snapshots(
            watch,
            team_id,
            quarter
        )
    )

    if not snapshots:
        return None

    current = snapshots[-1]

    if quarter == 1:

        return snapshot_difference(
            current
        )

    previous_snapshots = (
        get_quarter_snapshots(
            watch,
            team_id,
            quarter - 1
        )
    )

    if not previous_snapshots:

        return snapshot_difference(
            current
        )

    previous = previous_snapshots[-1]

    return snapshot_difference(
        current,
        previous
    )

def get_team_summary(
    watch,
    team_id
):

    snapshot = get_latest_snapshot(
        watch,
        team_id
    )

    if snapshot is None:
        return None

    return {

        "team": snapshot.team_name,

        "points": snapshot.points,

        "field_goal_points":
            snapshot.field_goal_points,

        "field_goal_made":
            snapshot.field_goal_made,

        "field_goal_attempted":
            snapshot.field_goal_attempted,

        "field_goal_percentage":
            snapshot.field_goal_percentage,

        "three_pt_made":
            snapshot.three_pt_made,

        "three_pt_attempted":
            snapshot.three_pt_attempted,

        "three_pt_percentage":
            snapshot.three_pt_percentage,

        "free_throw_made":
            snapshot.free_throw_made,

        "free_throw_attempted":
            snapshot.free_throw_attempted,

        "free_throw_percentage":
            snapshot.free_throw_percentage,

        "rebounds":
            snapshot.rebounds,

        "assists":
            snapshot.assists,

        "steals":
            snapshot.steals,

        "blocks":
            snapshot.blocks,

        "turnovers":
            snapshot.turnovers,

        "game_minute":
            snapshot.game_minute,

        "game_clock":
            snapshot.game_clock,
    }

def calculate_estimated_possessions(
    summary
):

    return round(

        summary["field_goal_attempted"]

        +

        (
            0.44 *
            summary["free_throw_attempted"]
        )

        +

        summary["turnovers"],

        2

    )

def calculate_points_per_possession(
    summary
):

    possessions = (
        calculate_estimated_possessions(
            summary
        )
    )

    if possessions == 0:
        return 0

    return round(

        summary["points"] /
        possessions,

        3

    )

def calculate_offensive_rating(
    summary
):

    possessions = (
        calculate_estimated_possessions(
            summary
        )
    )

    if possessions == 0:
        return 0

    return round(

        (
            summary["points"] /
            possessions
        ) * 100,

        2

    )

def calculate_pace(
    summary,
    watch
):

    if summary["game_minute"] == 0:
        return 0

    possessions = (
        calculate_estimated_possessions(
            summary
        )
    )

    return round(

        (
            possessions /
            summary["game_minute"]
        )

        *

        watch.total_game_minutes,

        2

    )

def calculate_three_point_rate(
    summary
):

    if summary["field_goal_attempted"] == 0:
        return 0

    return round(

        (
            summary["three_pt_attempted"] /
            summary["field_goal_attempted"]
        ) * 100,

        2
    )

def calculate_free_throw_rate(
    summary
):

    if summary["field_goal_attempted"] == 0:
        return 0

    return round(

        (
            summary["free_throw_attempted"] /
            summary["field_goal_attempted"]
        ) * 100,

        2
    )

def calculate_assist_turnover_ratio(
    summary
):

    if summary["turnovers"] == 0:

        if summary["assists"] == 0:
            return 0

        return summary["assists"]

    return round(

        summary["assists"] /

        summary["turnovers"],

        2
    )

def calculate_shot_distribution(
    summary
):

    two_point_made = (
        summary["field_goal_made"] -
        summary["three_pt_made"]
    )

    two_point_attempted = (
        summary["field_goal_attempted"] -
        summary["three_pt_attempted"]
    )

    two_point_points = (
        two_point_made * 2
    )

    three_point_points = (
        summary["three_pt_made"] * 3
    )

    free_throw_points = (
        summary["free_throw_made"]
    )

    total_points = summary["points"]

    if total_points == 0:

        two_point_share = 0
        three_point_share = 0
        free_throw_share = 0

    else:

        two_point_share = round(
            (
                two_point_points /
                total_points
            ) * 100,
            2
        )

        three_point_share = round(
            (
                three_point_points /
                total_points
            ) * 100,
            2
        )

        free_throw_share = round(
            (
                free_throw_points /
                total_points
            ) * 100,
            2
        )

    return {

        "two_point_made":
            two_point_made,

        "two_point_attempted":
            two_point_attempted,

        "two_point_percentage":
            round(
                (
                    two_point_made /
                    two_point_attempted
                ) * 100,
                2
            )
            if two_point_attempted
            else 0,

        "three_point_made":
            summary["three_pt_made"],

        "three_point_attempted":
            summary["three_pt_attempted"],

        "three_point_percentage":
            summary["three_pt_percentage"],

        "free_throw_made":
            summary["free_throw_made"],

        "free_throw_attempted":
            summary["free_throw_attempted"],

        "free_throw_percentage":
            summary["free_throw_percentage"],

        "two_point_points":
            two_point_points,

        "three_point_points":
            three_point_points,

        "free_throw_points":
            free_throw_points,

        "two_point_scoring_share":
            two_point_share,

        "three_point_scoring_share":
            three_point_share,

        "free_throw_scoring_share":
            free_throw_share,
    }

def project_team_points(
    watch,
    team_id
):

    summary = get_team_summary(
        watch,
        team_id
    )

    if summary is None:
        return None

    minutes = summary["game_minute"]

    if minutes == 0:
        return None

    projection = round(

        (
            summary["points"] /
            minutes
        )

        *

        watch.total_game_minutes,

        2
    )

    return projection



def calculate_scoring_rate(
    watch,
    team_id
):

    summary = get_team_summary(
        watch,
        team_id
    )

    if summary is None:
        return None

    minutes = summary["game_minute"]

    if minutes == 0:

        return {

            "points_per_minute": 0,

            "projected_points": 0,
        }

    points_per_minute = round(

        summary["points"] /

        minutes,

        2
    )

    projected_points = round(

        points_per_minute *

        watch.total_game_minutes,

        2
    )

    return {

        "points_per_minute":
            points_per_minute,

        "projected_points":
            projected_points,
    }

def calculate_recent_shooting(
    watch,
    team_id,
    snapshots=5
):

    team_snapshots = list(

        get_team_snapshots(
            watch,
            team_id
        )

    )

    if len(team_snapshots) < 2:

        return None

    recent_snapshots = team_snapshots[-snapshots:]

    current = recent_snapshots[-1]

    previous = recent_snapshots[0]

    difference = snapshot_difference(
        current,
        previous
    )

    return {

        "field_goal_made":
            difference["field_goal_made"],

        "field_goal_attempted":
            difference["field_goal_attempted"],

        "field_goal_percentage":
            difference["field_goal_percentage"],

        "three_point_made":
            difference["three_pt_made"],

        "three_point_attempted":
            difference["three_pt_attempted"],

        "three_point_percentage":
            difference["three_pt_percentage"],

        "free_throw_made":
            difference["free_throw_made"],

        "free_throw_attempted":
            difference["free_throw_attempted"],

        "free_throw_percentage":
            difference["free_throw_percentage"],
    }

def calculate_team_momentum(
    watch,
    team_id,
    snapshots=5
):

    team_snapshots = list(

        get_team_snapshots(
            watch,
            team_id
        )

    )

    if len(team_snapshots) < snapshots:

        return None

    recent_snapshots = team_snapshots[-snapshots:]

    scoring = []

    previous = None

    for snapshot in recent_snapshots:

        difference = snapshot_difference(
            snapshot,
            previous
        )

        scoring.append(
            difference["points"]
        )

        previous = snapshot

    average = round(

        sum(scoring) /

        len(scoring),

        2
    )

    latest = scoring[-1]

    if latest > average:

        trend = "Increasing"

    elif latest < average:

        trend = "Decreasing"

    else:

        trend = "Stable"

    return {

        "recent_scoring":

            scoring,

        "average_points":

            average,

        "latest_points":

            latest,

        "trend":

            trend
    }

def calculate_efficiency_trend(
    watch,
    team_id,
    snapshots=5
):

    team_snapshots = list(

        get_team_snapshots(
            watch,
            team_id
        )

    )

    if len(team_snapshots) < 2:

        return None

    recent_snapshots = team_snapshots[-snapshots:]

    current = recent_snapshots[-1]

    previous = recent_snapshots[0]

    difference = snapshot_difference(
        current,
        previous
    )

    possessions = round(

        difference["field_goal_attempted"]

        +

        (
            0.44 *
            difference["free_throw_attempted"]
        )

        +

        difference["turnovers"],

        2
    )

    if possessions == 0:

        points_per_possession = 0

        offensive_rating = 0

    else:

        points_per_possession = round(

            difference["points"] /

            possessions,

            3
        )

        offensive_rating = round(

            points_per_possession *

            100,

            2
        )

    return {

        "estimated_possessions":
            possessions,

        "points_per_possession":
            points_per_possession,

        "offensive_rating":
            offensive_rating,
    }

def calculate_team_projection_v2(
    watch,
    team_id
):

    summary = get_team_summary(
        watch,
        team_id
    )

    if summary is None:
        return None

    possessions = (
        calculate_estimated_possessions(
            summary
        )
    )

    if possessions == 0:

        return {

            "projected_points": 0,

            "remaining_minutes":
                watch.total_game_minutes,

            "remaining_possessions": 0,
        }

    current_ppp = round(

        summary["points"] /

        possessions,

        3
    )

    current_pace = calculate_pace(
        summary,
        watch
    )

    remaining_minutes = max(

        watch.total_game_minutes -

        summary["game_minute"],

        0
    )

    remaining_possessions = round(

        (
            current_pace /

            watch.total_game_minutes
        )

        *

        remaining_minutes,

        2
    )

    projected_points = round(

        summary["points"]

        +

        (
            remaining_possessions *

            current_ppp
        ),

        2
    )

    return {

        "current_points":
            summary["points"],

        "current_ppp":
            current_ppp,

        "current_pace":
            current_pace,

        "remaining_minutes":
            remaining_minutes,

        "remaining_possessions":
            remaining_possessions,

        "projected_points":
            projected_points,
    }

def analyse_team(
    watch,
    team_id
):

    summary = get_team_summary(
        watch,
        team_id
    )

    if summary is None:
        return None

    advanced_metrics = {

        "estimated_possessions":
            calculate_estimated_possessions(
                summary
            ),

        "points_per_possession":
            calculate_points_per_possession(
                summary
            ),

        "offensive_rating":
            calculate_offensive_rating(
                summary
            ),

        "pace":
            calculate_pace(
                summary,
                watch
            ),
    }

    team_style = {

        "three_point_rate":
            calculate_three_point_rate(
                summary
            ),

        "free_throw_rate":
            calculate_free_throw_rate(
                summary
            ),

        "assist_turnover_ratio":
            calculate_assist_turnover_ratio(
                summary
            ),
    }

    shot_distribution = (
        calculate_shot_distribution(
            summary
        )
    )

    projection = {

        "projected_points":
            project_team_points(
                watch,
                team_id
            )
    }

    analytics = {

        "scoring_rate":
            calculate_scoring_rate(
                watch,
                team_id
            ),

        "recent_shooting":
            calculate_recent_shooting(
                watch,
                team_id
            ),

        "momentum":
            calculate_team_momentum(
                watch,
                team_id
            ),

        "efficiency_trend":
            calculate_efficiency_trend(
                watch,
                team_id
            ),

        "projection":
            calculate_team_projection_v2(
                watch,
                team_id
            ),
    }

    return {

        "team":

            {

                "id": team_id,

                "name":
                    summary["team"],
            },

        "score":

            {

                "points":
                    summary["points"],

                "projected_points":
                    projection[
                        "projected_points"
                    ],
            },

        "shooting":

            {

                "field_goals":

                    {

                        "points":
                            summary[
                                "field_goal_points"
                            ],

                        "made":
                            summary[
                                "field_goal_made"
                            ],

                        "attempted":
                            summary[
                                "field_goal_attempted"
                            ],

                        "percentage":
                            summary[
                                "field_goal_percentage"
                            ],
                    },

                "three_pointers":

                    {

                        "made":
                            summary[
                                "three_pt_made"
                            ],

                        "attempted":
                            summary[
                                "three_pt_attempted"
                            ],

                        "percentage":
                            summary[
                                "three_pt_percentage"
                            ],
                    },

                "free_throws":

                    {

                        "made":
                            summary[
                                "free_throw_made"
                            ],

                        "attempted":
                            summary[
                                "free_throw_attempted"
                            ],

                        "percentage":
                            summary[
                                "free_throw_percentage"
                            ],
                    },
            },

        "ball_control":

            {

                "assists":
                    summary["assists"],

                "turnovers":
                    summary["turnovers"],

                "assist_turnover_ratio":
                    team_style[
                        "assist_turnover_ratio"
                    ],
            },

        "defense":

            {

                "rebounds":
                    summary["rebounds"],

                "steals":
                    summary["steals"],

                "blocks":
                    summary["blocks"],
            },

        "advanced_metrics":

            advanced_metrics,

        "team_style":

            {

                "three_point_rate":
                    team_style[
                        "three_point_rate"
                    ],

                "free_throw_rate":
                    team_style[
                        "free_throw_rate"
                    ],
            },

        "shot_distribution":

            shot_distribution,

        "analytics":

            analytics,
    }

def analyse_match(
    watch
):

    team_ids = list(

        watch.team_statistics

        .values_list(
            "team_id",
            flat=True
        )

        .distinct()

    )

    if len(team_ids) != 2:
        return None

    home = analyse_team(
        watch,
        team_ids[0]
    )

    away = analyse_team(
        watch,
        team_ids[1]
    )

    home_projected = (
        home["score"]["projected_points"]
    )

    away_projected = (
        away["score"]["projected_points"]
    )

    projected_total = round(
        home_projected +
        away_projected,
        2
    )

    projected_margin = round(
        abs(
            home_projected -
            away_projected
        ),
        2
    )

    if home_projected > away_projected:

        projected_winner = (
            home["team"]["name"]
        )

    elif away_projected > home_projected:

        projected_winner = (
            away["team"]["name"]
        )

    else:

        projected_winner = "Tie"

    return {

        "home": home,

        "away": away,

        "summary": {

            "current_total":

                home["score"]["points"]

                +

                away["score"]["points"],

            "projected_total":
                projected_total,

            "projected_margin":
                projected_margin,

            "projected_winner":
                projected_winner,
        }
    }

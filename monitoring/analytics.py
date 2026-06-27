from .models import (
    Alert,
    MatchSnapshot
)
from .services import save_team_statistics


def expected_score_at_time(
        baseline,
        elapsed_seconds,
        total_game_seconds):

    if total_game_seconds <= 0:
        return 0

    return (
        baseline *
        elapsed_seconds /
        total_game_seconds
    )


def save_snapshot(
        watch,
        parameter,
        current_points,
        expected_score,
        deviation,
        elapsed_seconds,
        game_clock):

    total_game_seconds = (
        watch.total_game_minutes * 60
    )

    expected_rate = (
        parameter.baseline /
        total_game_seconds
        if total_game_seconds > 0
        else 0
    )

    actual_rate = (
        current_points /
        elapsed_seconds
        if elapsed_seconds > 0
        else 0
    )

    MatchSnapshot.objects.create(

        watch=watch,

        game_clock=game_clock,

        elapsed_seconds=elapsed_seconds,

        current_points=current_points,

        expected_points=expected_score,

        live_deviation=deviation,

        # Legacy fields retained for compatibility
        projection=current_points,

        deviation=deviation,

        minutes_played=(
            elapsed_seconds / 60
        ),

        expected_scoring_rate=expected_rate,

        actual_scoring_rate=actual_rate,

        scoring_rate_deviation=(
            actual_rate -
            expected_rate
        ),

        recent_scoring_rate=actual_rate
    )


def create_alert(
        watch,
        parameter,
        expected_score,
        current_points,
        deviation):

    direction = (
        "UP"
        if deviation > 0
        else "DOWN"
    )

    message = (
        f"{parameter.get_parameter_display()} "
        f"moved {direction} by "
        f"{abs(deviation):.2f} points "
        f"(Expected={expected_score:.2f}, "
        f"Actual={current_points:.2f}, "
        f"Deviation={deviation:.2f})"
    )

    Alert.objects.create(
        watch=watch,
        parameter=parameter,
        alert_type=direction,

        # Legacy field retained
        projection=current_points,

        deviation=deviation,

        message=message
    )


def should_create_alert(
        watch,
        deviation):

    last_alert = (
        Alert.objects
        .filter(watch=watch)
        .order_by("-created_at")
        .first()
    )

    if not last_alert:
        return True

    if abs(
        deviation -
        last_alert.deviation
    ) >= 5:
        return True

    return False


def check_watch(
        watch,
        current_points,
        minutes_played,
        elapsed_seconds,
        game_clock,
        quarter,
        game_status):

    parameter = (
        watch.parameters.first()
    )

    if not parameter:
        return False

    total_game_seconds = (
        watch.total_game_minutes * 60
    )

    expected_score = (
        expected_score_at_time(
            parameter.baseline,
            elapsed_seconds,
            total_game_seconds
        )
    )

    deviation = (
        current_points -
        expected_score
    )

    # Save analytics snapshot
    save_snapshot(
        watch,
        parameter,
        current_points,
        expected_score,
        deviation,
        elapsed_seconds,
        game_clock
    )

    # Save team statistics snapshot
    save_team_statistics(
        watch=watch,
        game_id=watch.match_id,
        minutes_played=minutes_played,
        game_clock=game_clock,
        elapsed_seconds=elapsed_seconds,
        bookmaker_total=parameter.baseline,
        quarter=quarter,
        game_status=game_status,
    )

    print("\n====================")
    print(
        f"Expected Score: "
        f"{expected_score:.2f}"
    )
    print(
        f"Actual Score: "
        f"{current_points:.2f}"
    )
    print(
        f"Deviation: "
        f"{deviation:.2f}"
    )
    print("====================\n")

    if abs(deviation) >= (
        parameter.threshold
    ):

        if should_create_alert(
                watch,
                deviation):

            create_alert(
                watch,
                parameter,
                expected_score,
                current_points,
                deviation
            )

            return True

    return False
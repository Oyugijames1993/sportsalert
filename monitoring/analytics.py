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
        current_points,
        elapsed_seconds,
        game_clock):

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

        minutes_played=(
            elapsed_seconds / 60
        ),

        actual_scoring_rate=actual_rate,
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

    # Save match snapshot
    save_snapshot(
        watch=watch,
        current_points=current_points,
        elapsed_seconds=elapsed_seconds,
        game_clock=game_clock,
    )

    # Save team statistics
    save_team_statistics(
        watch=watch,
        game_id=watch.match_id,
        minutes_played=minutes_played,
        game_clock=game_clock,
        elapsed_seconds=elapsed_seconds,
        bookmaker_total=None,
        quarter=quarter,
        game_status=game_status,
    )

    print("\n====================")
    print(f"Current Points: {current_points}")
    print(f"Minutes Played: {minutes_played}")
    print(f"Game Clock: {game_clock}")
    print(f"Elapsed Seconds: {elapsed_seconds}")
    print(f"Quarter: {quarter}")
    print(f"Status: {game_status}")
    print("====================\n")

    # Alerts will be generated later from the analytics engine.
    return False
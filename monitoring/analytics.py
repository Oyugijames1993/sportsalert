from .models import (
    Alert,
    MatchSnapshot
)


def projected_total(
        current_points,
        minutes_played,
        baseline,
        total_minutes=40):

    if minutes_played <= 0:
        return baseline

    return (
        current_points /
        minutes_played
    ) * total_minutes


def calculate_deviation(
        baseline,
        projection):

    return projection - baseline


def expected_points_at_time(
        baseline,
        minutes_played,
        total_minutes):

    return (
        baseline *
        minutes_played /
        total_minutes
    )


def expected_scoring_rate(
        baseline,
        total_minutes):

    return (
        baseline /
        total_minutes
    )


def actual_scoring_rate(
        current_points,
        minutes_played):

    if minutes_played <= 0:
        return 0

    return (
        current_points /
        minutes_played
    )


def calculate_recent_scoring_rate(
        watch,
        current_points,
        minutes_played):

    snapshots = list(
        MatchSnapshot.objects
        .filter(watch=watch)
        .order_by("-created_at")[:10]
    )

    if not snapshots:
        return None

    target_window = 5

    reference_snapshot = None

    for snapshot in snapshots:

        if (
            minutes_played -
            snapshot.minutes_played
        ) >= target_window:

            reference_snapshot = snapshot
            break

    if reference_snapshot is None:

        reference_snapshot = (
            snapshots[-1]
        )

    points_diff = (
        current_points -
        reference_snapshot.current_points
    )

    minutes_diff = (
        minutes_played -
        reference_snapshot.minutes_played
    )

    if minutes_diff <= 0:
        return None

    return (
        points_diff /
        minutes_diff
    )


def projected_total_from_recent_rate(
        watch,
        current_points,
        minutes_played,
        baseline,
        total_minutes):

    expected_rate = (
        expected_scoring_rate(
            baseline,
            total_minutes
        )
    )

    recent_rate = (
        calculate_recent_scoring_rate(
            watch,
            current_points,
            minutes_played
        )
    )

    if recent_rate is None:
        recent_rate = expected_rate

    progress = (
        minutes_played /
        total_minutes
    )

    recent_weight = min(
        progress,
        0.8
    )

    expected_weight = (
        1 -
        recent_weight
    )

    blended_rate = (
        expected_weight *
        expected_rate
        +
        recent_weight *
        recent_rate
    )

    remaining_minutes = max(
        total_minutes -
        minutes_played,
        0
    )

    projection = (
        current_points +
        blended_rate *
        remaining_minutes
    )

    return projection


def save_snapshot(
        watch,
        parameter,
        current_points,
        projection,
        deviation,
        minutes_played,
        elapsed_seconds,
        game_clock):

    expected_points = (
        expected_points_at_time(
            parameter.baseline,
            minutes_played,
            watch.total_game_minutes
        )
    )

    live_deviation = (
        current_points -
        expected_points
    )

    expected_rate = (
        expected_scoring_rate(
            parameter.baseline,
            watch.total_game_minutes
        )
    )

    actual_rate = (
        actual_scoring_rate(
            current_points,
            minutes_played
        )
    )

    rate_deviation = (
        actual_rate -
        expected_rate
    )

    recent_rate = (
        calculate_recent_scoring_rate(
            watch,
            current_points,
            minutes_played
        )
    )

    MatchSnapshot.objects.create(

        watch=watch,

        game_clock=
            game_clock,

        elapsed_seconds=
            elapsed_seconds,

        current_points=
            current_points,

        expected_points=
            expected_points,

        live_deviation=
            live_deviation,

        projection=
            projection,

        deviation=
            deviation,

        minutes_played=
            minutes_played,

        expected_scoring_rate=
            expected_rate,

        actual_scoring_rate=
            actual_rate,

        scoring_rate_deviation=
            rate_deviation,

        recent_scoring_rate=
            recent_rate
    )


def create_alert(
        watch,
        parameter,
        projection,
        deviation):

    direction = (
        "UP"
        if deviation > 0
        else "DOWN"
    )

    message = (
        f"{parameter.get_parameter_display()} moved "
        f"{direction} by "
        f"{abs(deviation):.2f} points "
        f"(Baseline={parameter.baseline}, "
        f"Projection={projection:.2f})"
    )

    Alert.objects.create(
        watch=watch,
        parameter=parameter,
        alert_type=direction,
        projection=projection,
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
        game_clock):

    parameter = (
        watch.parameters.first()
    )

    if not parameter:
        return False

    projection = (
        projected_total_from_recent_rate(
            watch,
            current_points,
            minutes_played,
            parameter.baseline,
            watch.total_game_minutes
        )
    )

    deviation = calculate_deviation(
        parameter.baseline,
        projection
    )

    save_snapshot(
        watch,
        parameter,
        current_points,
        projection,
        deviation,
        minutes_played,
        elapsed_seconds,
        game_clock
    )

    if abs(deviation) >= (
        parameter.threshold
    ):

        if should_create_alert(
                watch,
                deviation):

            create_alert(
                watch,
                parameter,
                projection,
                deviation
            )

            return True

    return False
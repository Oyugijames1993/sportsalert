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
        total_minutes=40):

    return (
        baseline *
        minutes_played /
        total_minutes
    )


def expected_scoring_rate(
        baseline,
        total_minutes=40):

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

    last_snapshot = (
        MatchSnapshot.objects
        .filter(watch=watch)
        .order_by("-created_at")
        .first()
    )

    if not last_snapshot:
        return None

    points_diff = (
        current_points -
        last_snapshot.current_points
    )

    minutes_diff = (
        minutes_played -
        last_snapshot.minutes_played
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
        total_minutes=40):

    recent_rate = (
        calculate_recent_scoring_rate(
            watch,
            current_points,
            minutes_played
        )
    )

    if recent_rate is None:
        return baseline

    recent_projection = (
        recent_rate *
        total_minutes
    )

    weight = min(
        minutes_played /
        total_minutes,
        1
    )

    projection = (
        weight *
        recent_projection
        +
        (1 - weight) *
        baseline
    )

    return projection


def save_snapshot(
        watch,
        parameter,
        current_points,
        projection,
        deviation,
        minutes_played):

    expected_points = (
        expected_points_at_time(
            parameter.baseline,
            minutes_played
        )
    )

    live_deviation = (
        current_points -
        expected_points
    )

    expected_rate = (
        expected_scoring_rate(
            parameter.baseline
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

        current_points=current_points,

        expected_points=expected_points,

        live_deviation=live_deviation,

        projection=projection,

        deviation=deviation,

        minutes_played=minutes_played,

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
        minutes_played):

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
            parameter.baseline
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
        minutes_played
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
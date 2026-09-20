import numpy as np


COUNT_FIELDS = {
    "goals": ("goals_home", "goals_away"),
    "shots": ("shots_home", "shots_away"),
    "shots_on_target": ("shots_on_target_home", "shots_on_target_away"),
    "shots_inside_box": ("shots_inside_box_home", "shots_inside_box_away"),
    "shots_outside_box": ("shots_outside_box_home", "shots_outside_box_away"),
    "corners": ("corners_home", "corners_away"),
    "offsides": ("offsides_home", "offsides_away"),
    "tackles": ("tackles_home", "tackles_away"),
    "interceptions": ("interceptions_home", "interceptions_away"),
    "blocks": ("blocks_home", "blocks_away"),
    "duels": ("duels_home", "duels_away"),
    "duels_won": ("duels_won_home", "duels_won_away"),
    "fouls": ("fouls_home", "fouls_away"),
    "saves": ("saves_home", "saves_away"),
    "yellow_cards": ("yellow_home", "yellow_away"),
    "red_cards": ("red_home", "red_away"),
}


PERCENTAGE_FIELDS = {
    "possession": ("possession_home", "possession_away"),
    "pass_accuracy": ("pass_accuracy_home", "pass_accuracy_away"),
}


PASS_FIELDS = {
    "total_passes": ("total_passes_home", "total_passes_away"),
    "accurate_passes": ("accurate_passes_home", "accurate_passes_away"),
}


def _safe_value(profile, field):
    value = getattr(profile, field, None)

    if value is None:
        return None

    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(value):
        return None

    return max(0.0, value)


def _simulate_count(rng, mean, simulations):
    """
    Generate count-type statistics.

    We use a negative-binomial-style Gamma-Poisson mixture rather than
    a fixed Poisson distribution so the simulated results have realistic
    variation around the historical mean.
    """
    if mean is None:
        return None

    mean = max(0.0, float(mean))

    if mean == 0:
        return np.zeros(simulations, dtype=int)

    # Moderate dispersion.
    dispersion = max(1.0, mean * 2.0)

    gamma_shape = dispersion
    gamma_scale = mean / gamma_shape

    rates = rng.gamma(
        shape=gamma_shape,
        scale=gamma_scale,
        size=simulations,
    )

    return rng.poisson(rates)


def _simulate_percentage(rng, mean, simulations):
    """
    Simulate a percentage around the profile mean.
    """
    if mean is None:
        return None

    mean = float(np.clip(mean, 0.0, 100.0))

    if mean == 0:
        return np.zeros(simulations)

    if mean == 100:
        return np.full(simulations, 100.0)

    # Gives a reasonable amount of match-to-match variation.
    concentration = 30.0

    alpha = (mean / 100.0) * concentration
    beta = (1.0 - mean / 100.0) * concentration

    return rng.beta(alpha, beta, simulations) * 100.0


def _simulate_normal(rng, mean, simulations):
    """
    Simulate continuous passing statistics.
    """
    if mean is None:
        return None

    mean = max(0.0, float(mean))

    # Approximate 10% coefficient of variation.
    std = max(1.0, mean * 0.10)

    values = rng.normal(mean, std, simulations)

    return np.maximum(values, 0.0)


def _average(values):
    if values is None:
        return None

    return float(np.mean(values))


def _probability(values, condition):
    if values is None:
        return None

    return float(np.mean(condition(values)))


def _round_probability(value):
    if value is None:
        return None

    return round(value * 100, 2)


def simulate_match(home_profile, away_profile, simulations=100_000, random_seed=42):
    rng = np.random.default_rng(random_seed)

    result = {
        "simulations": simulations,
        "home_coach": home_profile.coach_name,
        "away_coach": away_profile.coach_name,
    }

    simulated = {}

    # ---------------------------------------------------------
    # COUNT STATISTICS
    # ---------------------------------------------------------

    for name, (home_field, away_field) in COUNT_FIELDS.items():
        home_mean = _safe_value(home_profile, home_field)
        away_mean = _safe_value(away_profile, away_field)

        home_values = _simulate_count(rng, home_mean, simulations)
        away_values = _simulate_count(rng, away_mean, simulations)

        simulated[f"home_{name}"] = home_values
        simulated[f"away_{name}"] = away_values

        result[f"home_{name}"] = _average(home_values)
        result[f"away_{name}"] = _average(away_values)

        if home_values is not None and away_values is not None:
            result[f"total_{name}"] = _average(
                home_values + away_values
            )

    # ---------------------------------------------------------
    # THROW-INS
    # ---------------------------------------------------------

    home_won = _safe_value(home_profile, "throw_ins_won_home")
    home_conceded = _safe_value(home_profile, "throw_ins_conceded_home")
    away_won = _safe_value(away_profile, "throw_ins_won_away")
    away_conceded = _safe_value(away_profile, "throw_ins_conceded_away")

    if home_won is not None and away_conceded is not None:
        home_throw_mean = (home_won + away_conceded) / 2.0
        home_throw_values = _simulate_count(rng, home_throw_mean, simulations)
        simulated["home_throw_ins"] = home_throw_values
        result["home_expected_throw_ins"] = _average(home_throw_values)
    else:
        home_throw_values = None

    if away_won is not None and home_conceded is not None:
        away_throw_mean = (away_won + home_conceded) / 2.0
        away_throw_values = _simulate_count(rng, away_throw_mean, simulations)
        simulated["away_throw_ins"] = away_throw_values
        result["away_expected_throw_ins"] = _average(away_throw_values)
    else:
        away_throw_values = None

    if home_throw_values is not None and away_throw_values is not None:
        total_throw_values = home_throw_values + away_throw_values
        simulated["total_throw_ins"] = total_throw_values
        result["total_expected_throw_ins"] = _average(total_throw_values)

    # ---------------------------------------------------------
    # PASSING STATISTICS
    # ---------------------------------------------------------

    for name, (home_field, away_field) in PASS_FIELDS.items():
        home_mean = _safe_value(home_profile, home_field)
        away_mean = _safe_value(away_profile, away_field)

        home_values = _simulate_normal(rng, home_mean, simulations)
        away_values = _simulate_normal(rng, away_mean, simulations)

        simulated[f"home_{name}"] = home_values
        simulated[f"away_{name}"] = away_values

        result[f"home_{name}"] = _average(home_values)
        result[f"away_{name}"] = _average(away_values)

        if home_values is not None and away_values is not None:
            result[f"total_{name}"] = _average(
                home_values + away_values
            )

    # ---------------------------------------------------------
    # POSSESSION
    # ---------------------------------------------------------

    home_possession_mean = _safe_value(
        home_profile,
        "possession_home",
    )

    away_possession_mean = _safe_value(
        away_profile,
        "possession_away",
    )

    if (
        home_possession_mean is not None
        and away_possession_mean is not None
    ):
        # Combine the two coach profiles and keep the two sides
        # summing to exactly 100%.
        combined = (
            home_possession_mean
            + away_possession_mean
        )

        if combined > 0:
            home_share = (
                home_possession_mean / combined
            ) * 100
        else:
            home_share = 50.0

        home_values = _simulate_percentage(
            rng,
            home_share,
            simulations,
        )

        away_values = 100.0 - home_values

        simulated["home_possession"] = home_values
        simulated["away_possession"] = away_values

        result["home_possession"] = _average(home_values)
        result["away_possession"] = _average(away_values)

    # ---------------------------------------------------------
    # BALL RETENTION — SECONDS OF POSSESSION PER PASS
    # ---------------------------------------------------------

    home_passes = simulated.get("home_total_passes")
    away_passes = simulated.get("away_total_passes")
    home_possession = simulated.get("home_possession")
    away_possession = simulated.get("away_possession")

    if home_passes is not None and home_possession is not None:
        home_seconds_per_pass = np.divide(
            home_possession * 54.0,
            home_passes,
            out=np.zeros_like(home_passes, dtype=float),
            where=home_passes > 0,
        )
        simulated["home_seconds_per_pass"] = home_seconds_per_pass
        result["home_seconds_per_pass"] = _average(home_seconds_per_pass)

    if away_passes is not None and away_possession is not None:
        away_seconds_per_pass = np.divide(
            away_possession * 54.0,
            away_passes,
            out=np.zeros_like(away_passes, dtype=float),
            where=away_passes > 0,
        )
        simulated["away_seconds_per_pass"] = away_seconds_per_pass
        result["away_seconds_per_pass"] = _average(away_seconds_per_pass)

    # ---------------------------------------------------------
    # PASS ACCURACY
    # ---------------------------------------------------------

    for name, (home_field, away_field) in {
        "pass_accuracy": PERCENTAGE_FIELDS["pass_accuracy"],
    }.items():

        home_mean = _safe_value(home_profile, home_field)
        away_mean = _safe_value(away_profile, away_field)

        home_values = _simulate_percentage(
            rng,
            home_mean,
            simulations,
        )

        away_values = _simulate_percentage(
            rng,
            away_mean,
            simulations,
        )

        simulated[f"home_{name}"] = home_values
        simulated[f"away_{name}"] = away_values

        result[f"home_{name}"] = _average(home_values)
        result[f"away_{name}"] = _average(away_values)

    # ---------------------------------------------------------
    # DERIVED STATISTICS
    # ---------------------------------------------------------

    if (
        simulated.get("home_shots") is not None
        and simulated.get("home_shots_on_target") is not None
    ):
        home_shots = simulated["home_shots"]
        home_sot = simulated["home_shots_on_target"]

        result["home_shot_accuracy"] = _average(
            np.divide(
                home_sot,
                home_shots,
                out=np.zeros_like(home_sot, dtype=float),
                where=home_shots > 0,
            ) * 100
        )

    if (
        simulated.get("away_shots") is not None
        and simulated.get("away_shots_on_target") is not None
    ):
        away_shots = simulated["away_shots"]
        away_sot = simulated["away_shots_on_target"]

        result["away_shot_accuracy"] = _average(
            np.divide(
                away_sot,
                away_shots,
                out=np.zeros_like(away_sot, dtype=float),
                where=away_shots > 0,
            ) * 100
        )

    # ---------------------------------------------------------
    # GOAL-BASED OUTPUTS
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # COACH STYLE MATCHUP
    #
    # Lower PPDA = stronger pressing.
    # Lower transition-to-shot time = faster transition attack.
    #
    # We compare the two coaches directly. If the values are
    # unavailable (0), that component is ignored.
    # ---------------------------------------------------------

    home_style_factor = 1.0
    away_style_factor = 1.0

    home_ppda = _safe_value(home_profile, "ppda_home")
    away_ppda = _safe_value(away_profile, "ppda_away")

    home_transition = _safe_value(
        home_profile,
        "transition_to_shot_seconds_home",
    )
    away_transition = _safe_value(
        away_profile,
        "transition_to_shot_seconds_away",
    )

    # Pressing matchup
    if home_ppda and away_ppda and home_ppda > 0 and away_ppda > 0:
        ppda_factor = (away_ppda / home_ppda) ** 0.15

        home_style_factor *= ppda_factor
        away_style_factor /= ppda_factor

    # Transition-to-shot matchup
    if (
        home_transition
        and away_transition
        and home_transition > 0
        and away_transition > 0
    ):
        transition_factor = (
            away_transition / home_transition
        ) ** 0.10

        home_style_factor *= transition_factor
        away_style_factor /= transition_factor

    # Keep the style factors visible in the simulation result.
    result["home_style_factor"] = home_style_factor
    result["away_style_factor"] = away_style_factor

    result["home_ppda"] = home_ppda
    result["away_ppda"] = away_ppda
    result["home_transition_to_shot"] = home_transition
    result["away_transition_to_shot"] = away_transition

    # Re-simulate goals using the existing statistical method,
    # but with the coach-style matchup applied.
    home_goal_mean = _safe_value(
        home_profile,
        "goals_home",
    )

    away_goal_mean = _safe_value(
        away_profile,
        "goals_away",
    )

    if home_goal_mean is not None:
        home_goal_mean *= home_style_factor

    if away_goal_mean is not None:
        away_goal_mean *= away_style_factor

    home_goals = _simulate_count(
        rng,
        home_goal_mean,
        simulations,
    )

    away_goals = _simulate_count(
        rng,
        away_goal_mean,
        simulations,
    )

    simulated["home_goals"] = home_goals
    simulated["away_goals"] = away_goals

    result["home_expected_goals"] = _average(home_goals)
    result["away_expected_goals"] = _average(away_goals)

    total_goals = home_goals + away_goals

    result["total_expected_goals"] = _average(total_goals)

    result["home_win"] = _probability(
        home_goals,
        lambda x: x > away_goals,
    )

    result["draw"] = _probability(
        home_goals,
        lambda x: x == away_goals,
    )

    result["away_win"] = _probability(
        home_goals,
        lambda x: x < away_goals,
    )

    result["btts"] = _probability(
        home_goals,
        lambda x: (x > 0) & (away_goals > 0),
    )

    result["over_1_5"] = _probability(
        total_goals,
        lambda x: x > 1,
    )

    result["over_2_5"] = _probability(
        total_goals,
        lambda x: x > 2,
    )

    result["over_3_5"] = _probability(
        total_goals,
        lambda x: x > 3,
    )

    result["under_2_5"] = 1 - result["over_2_5"]

    # ---------------------------------------------------------
    # COMMON SCORELINES
    # ---------------------------------------------------------

    scorelines = {}

    for home_goals_value, away_goals_value in zip(
        home_goals,
        away_goals,
    ):
        score = (
            int(home_goals_value),
            int(away_goals_value),
        )

        scorelines[score] = (
            scorelines.get(score, 0) + 1
        )

    sorted_scorelines = sorted(
        scorelines.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    result["common_scorelines"] = []

    for (home_score, away_score), count in sorted_scorelines[:10]:
        result["common_scorelines"].append(
            {
                "score": f"{home_score}-{away_score}",
                "probability": count / simulations,
            }
        )

    # ---------------------------------------------------------
    # OVER/UNDER PROBABILITIES
    # ---------------------------------------------------------

    thresholds = {
        "corners": [7.5, 8.5, 9.5, 10.5, 11.5],
        "fouls": [19.5, 21.5, 23.5, 25.5, 27.5],
        "yellow_cards": [2.5, 3.5, 4.5, 5.5],
        "shots": [20.5, 22.5, 24.5, 26.5, 28.5],
        "shots_on_target": [6.5, 7.5, 8.5, 9.5],
        "offsides": [1.5, 2.5, 3.5, 4.5],
        "throw_ins": [20.5, 22.5, 24.5, 26.5, 28.5, 30.5, 32.5, 34.5, 36.5],
    }

    result["markets"] = {}

    for statistic, lines in thresholds.items():
        values = simulated.get(
            f"home_{statistic}"
        )

        away_values = simulated.get(
            f"away_{statistic}"
        )

        if values is None or away_values is None:
            continue

        total_values = values + away_values

        result["markets"][statistic] = {}

        for line in lines:
            result["markets"][statistic][str(line)] = {
                "over": _probability(
                    total_values,
                    lambda x, line=line: x > line,
                ),
                "under": _probability(
                    total_values,
                    lambda x, line=line: x < line,
                ),
            }

    return result

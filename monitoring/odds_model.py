"""
Live, bookmaker-style odds projection for tracked football stats.

Model: total count of a stat in a match ~ Negative Binomial(mu, r).
  - mu (mean) is user-supplied per match, read off a real bookmaker's
    pre-match odds ladder (StatOddsModel.mu_0).
  - r (dispersion) is a per-stat-type constant, fitted once from a
    representative odds ladder (de-vigged, half-number lines only, since
    whole-number lines carry a push/tie outcome that a simple two-way
    Negative Binomial fit can't represent).

Live updating uses a Gamma-Poisson conjugate model: the match's
underlying per-minute event rate is treated as Gamma(shape=r, rate=beta)
distributed, with beta chosen so the prior mean over the full T-minute
match equals mu_0:

    beta = r * T / mu_0

Having observed k events by elapsed minute t, the posterior rate is
Gamma(r+k, beta+t), giving a live projected match-total:

    mu_live(t, k) = k + (r + k) / (beta + t) * (T - t)

At t=0 this equals mu_0 exactly; at t=T it equals k exactly (nothing left
to project). This produces exactly the "regression to the mean early,
trust observed pace late" behavior real bookmaker in-play lines show.
"""
from scipy import stats

# Per-stat dispersion constants, fitted from real bookmaker odds ladders
# (Champions League matches, Sept 2026) — de-vigged, half-lines only.
# These are reused across matches; only mu_0 varies per fixture.
DEFAULT_DISPERSION_R = {
    'fouls':         40.17,
    'corner_kicks':  21.22,
    'goal_kicks':    30.71,
    'shots_on_goal': 35.60,   # fit against "Shots On Target" ladder
    'throw_ins':     54.55,
    'total_goals':   24.58,
    'yellow_cards':  13.64,
}

DEFAULT_MATCH_MINUTES = 90


def get_dispersion_r(stat_type, override=None):
    """Resolve the dispersion parameter to use: an explicit override if
    given (e.g. from StatOddsModel.dispersion_r), else the fitted
    per-stat default. Raises if neither is available."""
    if override is not None:
        return override
    if stat_type in DEFAULT_DISPERSION_R:
        return DEFAULT_DISPERSION_R[stat_type]
    raise ValueError(f"No dispersion_r available for stat_type={stat_type!r}")


def live_mean(mu_0, r, t, k, T=DEFAULT_MATCH_MINUTES):
    """The Bayesian-updated projected match-total for this stat, given
    elapsed minutes t and observed count k so far."""
    if mu_0 <= 0 or r <= 0:
        raise ValueError("mu_0 and r must both be positive")
    beta = r * T / mu_0
    return k + (r + k) / (beta + t) * (T - t)


def _fair_p_over(line, mu, r):
    """P(X > line) under NegBinom(mu, r). line is always X.5, so the
    threshold for 'over' is simply floor(line) + 1."""
    p = r / (r + mu)
    k_threshold = int(line) + 1  # floor(line)+1, since line is always X.5
    return 1 - stats.nbinom.cdf(k_threshold - 1, r, p)


def odds_board(mu_0, r, t, k, overround=1.10, T=DEFAULT_MATCH_MINUTES):
    """
    Returns the live projected mean plus 5 lines (center-2 .. center+2,
    where 'center' is the live mean rounded to the nearest whole number)
    with bookmaker-style Over/Under odds — fair probability with the
    overround re-applied symmetrically, matching how real books price a
    ladder (not de-vigged fair odds).
    """
    mu_live = live_mean(mu_0, r, t, k, T)
    center = round(mu_live)

    rows = []
    for offset in range(-2, 3):
        whole = center + offset
        line = whole - 0.5  # "Over 21" -> line 20.5
        if line < 0:
            continue

        p_over_fair = _fair_p_over(line, mu_live, r)
        p_under_fair = 1 - p_over_fair

        # Re-apply the bookmaker's margin symmetrically, same convention
        # used when we de-vigged the real ladders (both sides scaled up
        # by the same overround factor).
        p_over_book = p_over_fair * overround
        p_under_book = p_under_fair * overround

        rows.append({
            'line': line,
            'label': f'Over {whole}',
            'p_over_fair': round(p_over_fair, 4),
            'odds_over': round(1 / p_over_book, 2) if p_over_book > 0 else None,
            'odds_under': round(1 / p_under_book, 2) if p_under_book > 0 else None,
        })

    return {
        'mu_live': round(mu_live, 2),
        'center': center,
        'rows': rows,
    }

def variation_status(mu_0, r, mu_live, overround, pre_match_odds, odds_margin, variation_threshold):
    """
    Evaluates the two-condition Pace Up/Down check shared by the live
    watch-detail display and the polling command's alert firing:

      1) |mu_live - mu_0| >= variation_threshold
      2) the fair odd for the line nearest mu_live, under the *live*
         mu_live/r, stays within odds_margin of pre_match_odds

    Returns a dict describing the current state regardless of whether
    both conditions are met, so callers can display "how close" as well
    as fire on a clean pass.
    """
    variation = mu_live - mu_0
    meets_variation = abs(variation) >= variation_threshold
    direction = 'UP' if variation > 0 else 'DOWN'
    label = 'Pace is up' if variation > 0 else 'Pace is low'

    line = round(mu_live) - 0.5
    live_odds = None
    meets_odds = False
    try:
        p_over = _fair_p_over(line, mu_live, r)
        p_side = p_over if variation > 0 else (1 - p_over)
        if p_side > 0:
            live_odds = round((1 / p_side) * overround, 2)
            meets_odds = abs(live_odds - pre_match_odds) <= odds_margin
    except (ValueError, ZeroDivisionError):
        pass

    return {
        'variation': round(variation, 2),
        'direction': direction,
        'label': label,
        'meets_variation': meets_variation,
        'live_odds': live_odds,
        'meets_odds': meets_odds,
        'fires': meets_variation and meets_odds,
    }

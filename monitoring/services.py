import requests

from django.conf import settings
from datetime import date
from monitoring.models import Watch



def get_total_game_minutes(game):

    league_name = (
        game["league"]["name"]
        .lower()
    )

    if "nba" in league_name:
        return 48

    return 40


def calculate_elapsed_seconds(game):

    minutes_played = (
        calculate_minutes_played(
            game
        )
    )

    if minutes_played is None:
        return 0

    return (
        minutes_played * 60
    )
def calculate_minutes_played(game):

    status = game["status"]["short"]

    timer = game["status"]["timer"]

    total_game_minutes = (
        get_total_game_minutes(game)
    )

    quarter_length = (
        total_game_minutes / 4
    )

    if status == "HT":
        return quarter_length * 2

    if status == "FT":
        return total_game_minutes

    if not timer:
        return None

    if ":" not in str(timer):
        return None

    minutes_remaining, seconds_remaining = (
        map(
            int,
            timer.split(":")
        )
    )

    remaining = (
        minutes_remaining +
        (
            seconds_remaining / 60
        )
    )

    elapsed_in_quarter = (
        quarter_length -
        remaining
    )

    quarter_map = {
        "Q1": 0,
        "Q2": 1,
        "Q3": 2,
        "Q4": 3,
    }

    if status not in quarter_map:
        return None

    completed_quarters = (
        quarter_map[status]
        * quarter_length
    )

    return (
        completed_quarters +
        elapsed_in_quarter
    )
def get_match_data(match_id):

    url = (
        f"https://v1.basketball.api-sports.io/games"
        f"?id={match_id}"
    )

    headers = {
        "x-apisports-key":
            settings.API_SPORTS_KEY
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if data["results"] == 0:

        raise Exception(
            f"No game found with ID "
            f"{match_id}"
        )

    game = data["response"][0]

    print("\n====================")

    print(
        "STATUS:",
        game["status"]
    )

    print(
        "HOME:",
        game["scores"]["home"]["total"]
    )

    print(
        "AWAY:",
        game["scores"]["away"]["total"]
    )

    print("====================")

    home_score = (
        game["scores"]["home"]["total"]
        or 0
    )

    away_score = (
        game["scores"]["away"]["total"]
        or 0
    )

    current_points = (
        home_score +
        away_score
    )

    minutes_played = (
        calculate_minutes_played(
            game
        )
    )

    if minutes_played is None:
        minutes_played = 0

    total_game_minutes = (
        get_total_game_minutes(
            game
        )
    )

    status_short = (
        game["status"]["short"]
    )

    timer = (
        game["status"]["timer"]
    )

    if timer:

        game_clock = (
            f"{status_short} "
            f"{timer}"
        )

    else:

        game_clock = (
            status_short
        )

    elapsed_seconds = (
        calculate_elapsed_seconds(
            game
        )
    )

    print(
        "GAME CLOCK:",
        game_clock
    )

    print(
        "MINUTES PLAYED:",
        minutes_played
    )

    print(
        "ELAPSED SECONDS:",
        elapsed_seconds
    )

    return {

        "current_points":
            current_points,

        "minutes_played":
            minutes_played,

        "elapsed_seconds":
            elapsed_seconds,

        "game_clock":
            game_clock,

        "status":
            status_short,

        "total_game_minutes":
            total_game_minutes

    }
def get_games_by_date(game_date):

    url = (
        f"https://v1.basketball.api-sports.io/games"
        f"?date={game_date}"
    )

    headers = {
        "x-apisports-key":
            settings.API_SPORTS_KEY
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


def is_live_game(game):

    return game["status"]["short"] in [
        "Q1",
        "Q2",
        "Q3",
        "Q4",
        "HT"
    ]


def get_live_games_by_date(game_date):

    data = get_games_by_date(
        game_date
    )

    return [
        game
        for game in data["response"]
        if is_live_game(game)
    ]


def get_today_live_games():

    today = date.today().strftime(
        "%Y-%m-%d"
    )

    return get_live_games_by_date(
        today
    )


def create_watch_from_game(
    game,
    baseline,
    threshold
):

    return Watch.objects.create(

        sport="basketball",

        match_id=str(game["id"]),

        home_team=
            game["teams"]["home"]["name"],

        away_team=
            game["teams"]["away"]["name"],

        league=
            game["league"]["name"],

        parameter="total_points",

        baseline=baseline,

        threshold=threshold,

        active=True
    )


def get_today_games():

    today = date.today().strftime(
        "%Y-%m-%d"
    )

    data = get_games_by_date(
        today
    )

    return data["response"]


def get_scheduled_games():

    games = get_today_games()

    return [
        game
        for game in games
        if game["status"]["short"] == "NS"
    ]
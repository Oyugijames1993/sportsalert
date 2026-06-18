import requests

from django.conf import settings
from datetime import date
from monitoring.models import Watch


def calculate_minutes_played(game):

    status = game["status"]["short"]

    timer = game["status"]["timer"]

    # Half Time
    if status == "HT":
        return 20

    # Full Time
    if status == "FT":
        return 40

    # Unknown timer state
    if timer is None:
        return None

    timer = float(timer)

    if status == "Q1":
        return timer

    elif status == "Q2":
        return 10 + timer

    elif status == "Q3":
        return 20 + timer

    elif status == "Q4":
        return 30 + timer

    return None

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

    # Game not started yet
    if minutes_played is None:
        minutes_played = 0

    return {

        "current_points":
            current_points,

        "minutes_played":
            minutes_played,

        "status":
            game["status"]["short"]

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
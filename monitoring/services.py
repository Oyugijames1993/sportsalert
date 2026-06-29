import requests

from django.conf import settings
from datetime import date
from monitoring.models import Watch
from monitoring.models import TeamStatistic



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

def get_current_quarter(game):

    status = game["status"]["short"]

    mapping = {

        "Q1": 1,
        "Q2": 2,
        "Q3": 3,
        "Q4": 4,
        "OT": 5,

    }

    return mapping.get(
        status,
        0
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

    # API returns plain minute numbers
    if ":" not in str(timer):

        elapsed_in_quarter = float(timer)

        return (
            completed_quarters +
            elapsed_in_quarter
        )

    # Fallback for MM:SS format
    minutes_remaining, seconds_remaining = (
        map(
            int,
            timer.split(":")
        )
    )

    remaining = (
        minutes_remaining +
        (seconds_remaining / 60)
    )

    elapsed_in_quarter = (
        quarter_length -
        remaining
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

    quarter = (
        get_current_quarter(
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

    print(
        "QUARTER:",
        quarter
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

        "quarter":
            quarter,

        "total_game_minutes":
            total_game_minutes

    }



def get_team_statistics(game_id):

    url = (
        "https://v1.basketball.api-sports.io/"
        "games/statistics/teams"
    )

    headers = {
        "x-apisports-key":
            settings.API_SPORTS_KEY
    }

    response = requests.get(
        url,
        headers=headers,
        params={"id": game_id},
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    if data["results"] == 0:

        print(
            f"No team statistics available "
            f"for game {game_id}."
        )

        return None

    return data

def save_team_statistics(
    watch,
    game_id,
    minutes_played=0,
    game_clock="",
    elapsed_seconds=0,
    bookmaker_total=None,
    quarter=0,
    game_status=""
):
    print(f"\nSaving team statistics for game {game_id}")

    data = get_team_statistics(game_id)

    if data is None:
        print("No statistics returned from API.")
        return

    total_game_minutes = watch.total_game_minutes

    for index, team in enumerate(data["response"]):

        # =====================================
        # DEBUG
        # =====================================

        print("\n==========================================")
        print("TEAM:", team["team"]["name"])
        print("FIELD GOALS:", team["field_goals"])
        print("THREE POINTERS:", team["threepoint_goals"])
        print("FREE THROWS:", team["freethrows_goals"])
        print("==========================================")

        try:

            fg_attempts = (
                team["field_goals"].get("attempts") or 0
            )

            fg_made = (
                team["field_goals"].get("total") or 0
            )

            fg_percentage = float(
                team["field_goals"].get("percentage") or 0
            )

            three_attempts = (
                team["threepoint_goals"].get("attempts") or 0
            )

            three_made = (
                team["threepoint_goals"].get("total") or 0
            )

            three_percentage = float(
                team["threepoint_goals"].get("percentage") or 0
            )

            ft_attempts = (
                team["freethrows_goals"].get("attempts") or 0
            )

            ft_made = (
                team["freethrows_goals"].get("total") or 0
            )

            ft_percentage = float(
                team["freethrows_goals"].get("percentage") or 0
            )

            # =====================================
            # DEBUG
            # =====================================

            print("\nParsed values")
            print(f"FGM: {fg_made}")
            print(f"FGA: {fg_attempts}")
            print(f"3PM: {three_made}")
            print(f"3PA: {three_attempts}")
            print(f"FTM: {ft_made}")
            print(f"FTA: {ft_attempts}")

            if fg_attempts < three_attempts:
                print("ERROR: FGA is less than 3PA")

            if fg_made < three_made:
                print("ERROR: FGM is less than 3PM")

            two_pt_made = fg_made - three_made
            two_pt_attempts = fg_attempts - three_attempts

            print(f"Derived 2PM: {two_pt_made}")
            print(f"Derived 2PA: {two_pt_attempts}")

            field_goal_points = (
                (two_pt_made * 2)
                + (three_made * 3)
            )

            points = (
                field_goal_points +
                ft_made
            )

            rebounds = (
                team["rebounds"].get("total") or 0
            )

            assists = team.get("assists") or 0
            steals = team.get("steals") or 0
            blocks = team.get("blocks") or 0
            turnovers = team.get("turnovers") or 0

            possessions = round(
                fg_attempts +
                (0.44 * ft_attempts) +
                turnovers,
                2
            )

            if possessions > 0:
                ppp = round(points / possessions, 3)
                offensive_rating = round(ppp * 100, 2)
            else:
                ppp = 0
                offensive_rating = 0

            if minutes_played > 0:

                pace = round(
                    (possessions / minutes_played)
                    * total_game_minutes,
                    2
                )

                projected_points = round(
                    (points / minutes_played)
                    * total_game_minutes,
                    2
                )

            else:

                pace = 0
                projected_points = 0

            team_name = (
                watch.home_team
                if index == 0
                else watch.away_team
            )

            latest = (
                TeamStatistic.objects
                .filter(
                    watch=watch,
                    team_id=team["team"]["id"]
                )
                .order_by("-created_at")
                .first()
            )

            if latest and (
                latest.points == points and
                latest.field_goal_made == fg_made and
                latest.field_goal_attempted == fg_attempts and
                latest.three_pt_made == three_made and
                latest.three_pt_attempted == three_attempts and
                latest.free_throw_made == ft_made and
                latest.free_throw_attempted == ft_attempts and
                latest.rebounds == rebounds and
                latest.assists == assists and
                latest.steals == steals and
                latest.blocks == blocks and
                latest.turnovers == turnovers
            ):
                print(f"Skipping {team_name} (no changes).")
                continue

            stat = TeamStatistic.objects.create(
                watch=watch,
                team_id=team["team"]["id"],
                team_name=team_name,
                points=points,
                field_goal_points=field_goal_points,
                field_goal_made=fg_made,
                field_goal_attempted=fg_attempts,
                field_goal_percentage=fg_percentage,
                three_pt_made=three_made,
                three_pt_attempted=three_attempts,
                three_pt_percentage=three_percentage,
                free_throw_made=ft_made,
                free_throw_attempted=ft_attempts,
                free_throw_percentage=ft_percentage,
                rebounds=rebounds,
                assists=assists,
                steals=steals,
                blocks=blocks,
                turnovers=turnovers,
                estimated_possessions=possessions,
                points_per_possession=ppp,
                offensive_rating=offensive_rating,
                pace=pace,
                projected_points=projected_points,
                quarter=quarter,
                game_status=game_status,
                game_minute=minutes_played,
                game_clock=game_clock,
                elapsed_seconds=elapsed_seconds,
                bookmaker_total=bookmaker_total,
            )

            print(
                f"Saved snapshot for {team_name} (ID={stat.id})"
            )

        except Exception as e:

            print(
                f"Error saving "
                f"{team.get('team', {}).get('name', 'Unknown')}: {e}"
            )
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


def create_watch_from_game(game):

    return Watch.objects.create(

        sport="basketball",

        match_id=str(game["id"]),

        home_team=
            game["teams"]["home"]["name"],

        away_team=
            game["teams"]["away"]["name"],

        league=
            game["league"]["name"],

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

def get_team_statistics_for_watch(watch):

    match_data = get_match_data(
        watch.match_id
    )

    save_team_statistics(
        watch=watch,
        game_id=watch.match_id,
        minutes_played=
            match_data[
                "minutes_played"
            ]
    )

    return TeamStatistic.objects.filter(
        watch=watch
    ).order_by("-created_at")[:2]
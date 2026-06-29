from django.core.management.base import BaseCommand

from monitoring.services import (
    get_today_games,
    get_team_statistics,
)


class Command(BaseCommand):

    help = (
        "Find today's games that provide team statistics"
    )

    def handle(self, *args, **options):

        games = get_today_games()

        self.stdout.write(
            f"Checking {len(games)} games...\n"
        )

        for game in games:

            game_id = game["id"]

            try:

                stats = get_team_statistics(
                    game_id
                )

                if stats and stats["results"] > 0:

                    start_time = (
                        game["date"]
                    )

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{game_id} | "
                            f"{game['teams']['home']['name']} "
                            f"vs "
                            f"{game['teams']['away']['name']} | "
                            f"Start: {start_time} | "
                            f"Status: {game['status']['short']}"
                        )
                    )

            except Exception as e:

                self.stdout.write(
                    self.style.ERROR(
                        f"{game_id}: {e}"
                    )
                )
from django.core.management.base import BaseCommand

from monitoring.services import (
    get_scheduled_games,
    create_watch_from_game
)


class Command(BaseCommand):

    help = "Create a watch for a game"

    def add_arguments(
            self,
            parser):

        parser.add_argument(
            "--game-id",
            type=int,
            required=True
        )

        parser.add_argument(
            "--baseline",
            type=float,
            required=True
        )

        parser.add_argument(
            "--threshold",
            type=float,
            required=True
        )

    def handle(
            self,
            *args,
            **options):

        game_id = options[
            "game_id"
        ]

        baseline = options[
            "baseline"
        ]

        threshold = options[
            "threshold"
        ]

        games = (
            get_scheduled_games()
        )

        game = next(
            (
                g
                for g in games
                if g["id"] == game_id
            ),
            None
        )

        if not game:

            self.stdout.write(
                self.style.ERROR(
                    "Game not found"
                )
            )

            return

        watch = (
            create_watch_from_game(
                game,
                baseline,
                threshold
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Watch created: "
                f"{watch.home_team} vs "
                f"{watch.away_team}"
            )
        )


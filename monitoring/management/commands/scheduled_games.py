from django.core.management.base import BaseCommand

from monitoring.services import (
    get_scheduled_games
)


class Command(BaseCommand):

    help = (
        "Display scheduled games"
    )

    def handle(
            self,
            *args,
            **options):

        games = (
            get_scheduled_games()
        )

        if not games:

            self.stdout.write(
                self.style.WARNING(
                    "No scheduled games found"
                )
            )

            return

        for game in games:

            self.stdout.write(
                f'{game["id"]} | '
                f'{game["teams"]["home"]["name"]} '
                f'vs '
                f'{game["teams"]["away"]["name"]} | '
                f'{game["league"]["name"]}'
            )
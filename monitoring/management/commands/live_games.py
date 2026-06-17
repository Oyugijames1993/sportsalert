from django.core.management.base import BaseCommand

from monitoring.services import (
    get_today_live_games
)


class Command(BaseCommand):

    help = (
        "Show live games"
    )

    def handle(
        self,
        *args,
        **kwargs
    ):

        games = (
            get_today_live_games()
        )

        for game in games:

            self.stdout.write(
                f"{game['id']} | "
                f"{game['teams']['home']['name']} "
                f"vs "
                f"{game['teams']['away']['name']} | "
                f"{game['status']['short']}"
            )
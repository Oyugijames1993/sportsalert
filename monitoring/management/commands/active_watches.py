from django.core.management.base import BaseCommand

from monitoring.models import Watch


class Command(BaseCommand):

    help = "Display active watches"

    def handle(
            self,
            *args,
            **options):

        watches = Watch.objects.filter(
            active=True
        )

        if not watches.exists():

            self.stdout.write(
                self.style.WARNING(
                    "No active watches"
                )
            )

            return

        for watch in watches:

            self.stdout.write(
                f"{watch.id} | "
                f"{watch.home_team} vs "
                f"{watch.away_team} | "
                f"Baseline={watch.baseline} | "
                f"Threshold={watch.threshold}"
            )
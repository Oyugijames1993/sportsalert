from django.core.management.base import BaseCommand

from monitoring.models import Watch
from monitoring.analytics import check_watch
from monitoring.services import get_match_data


class Command(BaseCommand):

    help = "Monitor active matches"

    def handle(self, *args, **kwargs):

        watches = Watch.objects.filter(
            active=True
        )

        self.stdout.write(
            f"Found {watches.count()} active watches"
        )

        for watch in watches:

            try:

                self.stdout.write(
                    f"\nChecking game "
                    f"{watch.match_id}"
                )

                data = get_match_data(
                    watch.match_id
                )

                self.stdout.write(
                    f"Current Points: "
                    f"{data['current_points']}"
                )

                self.stdout.write(
                    f"Minutes Played: "
                    f"{data['minutes_played']}"
                )

                triggered = check_watch(
                    watch,
                    data["current_points"],
                    data["minutes_played"]
                )

                if triggered:

                    self.stdout.write(
                        self.style.SUCCESS(
                            "Alert Created"
                        )
                    )

                else:

                    self.stdout.write(
                        "No Alert"
                    )

            except Exception as e:

                self.stdout.write(
                    self.style.ERROR(
                        f"Error: {e}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                "\nMonitoring complete"
            )
        )
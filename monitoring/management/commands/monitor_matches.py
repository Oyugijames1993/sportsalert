from django.core.management.base import BaseCommand
from django.utils import timezone

from monitoring.models import Watch
from monitoring.analytics import check_watch
from monitoring.services import get_match_data


class Command(BaseCommand):

    help = "Monitor active matches"

    def handle(self, *args, **kwargs):

        now = timezone.now()

        watches = Watch.objects.filter(
            active=True,
            monitoring_finished=False,
            monitoring_start__lte=now
        )

        self.stdout.write(
            f"Found {watches.count()} watch(es) ready for monitoring"
        )

        for watch in watches:

            try:

                self.stdout.write(
                    f"\nChecking game {watch.match_id}"
                )

                data = get_match_data(
                    watch.match_id
                )

                status = data.get(
                    "status",
                    ""
                )

                watch.game_status = status

                watch.last_polled = now

                watch.total_game_minutes = (
                    data["total_game_minutes"]
                )

                if not watch.monitoring_started:

                    watch.monitoring_started = True

                # Stop monitoring if game finished
                if status == "FT":

                    watch.monitoring_finished = True

                    watch.active = False

                    watch.save()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Game {watch.match_id} finished. Monitoring stopped."
                        )
                    )

                    continue

                watch.save()

                self.stdout.write(
                    f"Status: {status}"
                )

                self.stdout.write(
                    f"Current Points: "
                    f"{data['current_points']}"
                )

                self.stdout.write(
                    f"Minutes Played: "
                    f"{data['minutes_played']}"
                )

                self.stdout.write(
                    f"Game Clock: "
                    f"{data['game_clock']}"
                )

                self.stdout.write(
                    f"Elapsed Seconds: "
                    f"{data['elapsed_seconds']}"
                )

                self.stdout.write(
                    f"Total Game Minutes: "
                    f"{data['total_game_minutes']}"
                )

                triggered = check_watch(
                    watch,
                    data["current_points"],
                    data["minutes_played"],
                    data["elapsed_seconds"],
                    data["game_clock"]
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
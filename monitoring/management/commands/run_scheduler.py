import time

from django.core.management import BaseCommand, call_command
from django.utils import timezone

from monitoring.models import Watch
from monitoring.services import get_match_data


LIVE_STATUSES = {
    "Q1",
    "Q2",
    "HT",
    "Q3",
    "Q4",
    "OT",
}


class Command(BaseCommand):
    help = "Runs monitor_matches for live games only"

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.SUCCESS(
                "Scheduler started..."
            )
        )

        while True:

            try:

                now = timezone.now()

                watches = Watch.objects.filter(
                    active=True,
                    monitoring_finished=False,
                    monitoring_start__lte=now
                )

                live_found = False

                for watch in watches:

                    try:

                        data = get_match_data(
                            watch.match_id
                        )

                        status = data.get(
                            "status",
                            ""
                        )

                        if status in LIVE_STATUSES:

                            if not watch.monitoring_started:

                                watch.monitoring_started = True

                                watch.save(
                                    update_fields=[
                                        "monitoring_started"
                                    ]
                                )

                                self.stdout.write(
                                    self.style.SUCCESS(
                                        f"Game {watch.match_id} started"
                                    )
                                )

                            live_found = True

                        else:

                            self.stdout.write(
                                f"Game {watch.match_id} not started "
                                f"(status={status})"
                            )

                    except Exception as e:

                        self.stdout.write(
                            self.style.ERROR(
                                f"Error checking game "
                                f"{watch.match_id}: {e}"
                            )
                        )

                if live_found:

                    self.stdout.write(
                        self.style.SUCCESS(
                            "Running monitor_matches..."
                        )
                    )

                    call_command(
                        "monitor_matches"
                    )

                else:

                    self.stdout.write(
                        "No live games found"
                    )

            except Exception as e:

                self.stdout.write(
                    self.style.ERROR(
                        f"Scheduler error: {e}"
                    )
                )

            # Poll every 60 seconds
            time.sleep(60)
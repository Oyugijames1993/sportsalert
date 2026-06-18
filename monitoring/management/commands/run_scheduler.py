import time

from django.core.management import BaseCommand, call_command
from django.utils import timezone

from monitoring.models import Watch


class Command(BaseCommand):
    help = "Runs monitor_matches for active watches"

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

                if watches.exists():

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"{watches.count()} active watch(es) found"
                        )
                    )

                    call_command("monitor_matches")

                else:

                    self.stdout.write(
                        "No watches ready for monitoring"
                    )

            except Exception as e:

                self.stdout.write(
                    self.style.ERROR(
                        f"Scheduler error: {e}"
                    )
                )

            # wait 2 minutes
            time.sleep(120)
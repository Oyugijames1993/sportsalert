"""
Simple loop that runs poll_football_stats every POLL_SECONDS. Unlike
run_scheduler.py (basketball), this doesn't do a separate "is anything
live" pre-check call — poll_football_stats already filters to watches
whose monitoring_start has passed and checks each fixture's own status,
so when nothing's live it just reports "0 watches" and makes zero API
calls that cycle.

POLL_SECONDS is adjustable — lower it once on a paid plan with a higher
rate limit; 90s keeps a single tracked match comfortably within the free
tier's 100 requests/day (each poll costs 2 requests: status + statistics).

Run with: python manage.py run_football_scheduler
Stop with: Ctrl+C
"""
import time
from django.core.management import BaseCommand, call_command

POLL_SECONDS = 90


class Command(BaseCommand):
    help = "Runs poll_football_stats on a loop every POLL_SECONDS"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS(
            f"Football scheduler started — polling every {POLL_SECONDS}s. Ctrl+C to stop."
        ))
        while True:
            try:
                call_command("poll_football_stats")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Scheduler error: {e}"))
            time.sleep(POLL_SECONDS)

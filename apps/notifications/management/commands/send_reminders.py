"""Напоминания о предстоящих воркшопах.

Запускается по cron (см. README). Celery сознательно не используем —
для напоминаний достаточно периодического прогона команды.

    */15 * * * *  python manage.py send_reminders

Идемпотентна: отправленное напоминание помечается в Enrollment.reminded_at,
поэтому повторный запуск не продублирует уведомление.
"""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone

from apps.enrollments.models import Enrollment
from apps.notifications.models import Notification
from apps.notifications.services import settings_for


class Command(BaseCommand):
    help = "Рассылает напоминания о воркшопах, которые скоро начнутся"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Только показать, кому ушло бы напоминание",
        )

    def handle(self, *args, **options):
        now = timezone.now()
        dry_run = options["dry_run"]

        candidates = (
            Enrollment.objects.filter(status="confirmed", reminded_at__isnull=True)
            .filter(workshop__status="published")
            .select_related("workshop", "workshop__mentor", "participant")
        )

        sent = 0
        skipped = 0

        for enrollment in candidates:
            workshop = enrollment.workshop
            starts_at = workshop.starts_at

            if starts_at <= now:
                # Встреча уже началась — напоминать поздно.
                continue

            prefs = settings_for(enrollment.participant)
            if not prefs.reminders:
                skipped += 1
                continue

            if starts_at - now > timedelta(hours=prefs.reminder_hours):
                # Ещё рано для этого пользователя.
                continue

            if dry_run:
                self.stdout.write(
                    f"→ {enrollment.participant.email}: «{workshop.title}» "
                    f"за {prefs.reminder_hours} ч"
                )
                sent += 1
                continue

            Notification.objects.create(
                recipient=enrollment.participant,
                title=f"Скоро воркшоп «{workshop.title}»",
                body=f"{workshop.full_date_label} · {workshop.place}. "
                f"Ментор: {workshop.mentor.full_name}.",
                workshop=workshop,
            )
            enrollment.reminded_at = now
            enrollment.save(update_fields=["reminded_at"])
            sent += 1

        verb = "Показано" if dry_run else "Отправлено"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} напоминаний: {sent}. Пропущено (отключены): {skipped}."
            )
        )

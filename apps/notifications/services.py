from .models import Notification, NotificationSettings

STATUS = "status"
REMINDER = "reminder"
RECOMMENDATION = "recommendation"

_FLAG_BY_KIND = {
    STATUS: "status_changes",
    REMINDER: "reminders",
    RECOMMENDATION: "recommendations",
}


def settings_for(user):
    obj, _ = NotificationSettings.objects.get_or_create(user=user)
    return obj


def notify(user, title, body, workshop=None, kind=STATUS):
    """Создаёт уведомление, если пользователь его не отключил."""
    prefs = settings_for(user)
    flag = _FLAG_BY_KIND.get(kind)
    if flag and not getattr(prefs, flag):
        return None
    return Notification.objects.create(
        recipient=user, title=title, body=body, workshop=workshop
    )


def notify_mentor_about_enrollment(enrollment, title):
    workshop = enrollment.workshop
    if workshop.mentor_id == enrollment.participant_id:
        return None
    return notify(
        workshop.mentor,
        "Изменение записи на воркшоп",
        f"{enrollment.participant.full_name} · {workshop.title} · {title}",
        workshop=workshop,
    )

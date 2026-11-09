def shell(request):
    """Данные для шапки: навигация и счётчик непрочитанных уведомлений."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {"nav_items": _nav_for(None), "unread_count": 0}

    from apps.notifications.models import Notification

    return {
        "nav_items": _nav_for(user),
        "unread_count": Notification.objects.filter(
            recipient=user, is_read=False
        ).count(),
    }


def _nav_for(user):
    items = [
        {"label": "Воркшопы", "url_name": "workshops:catalog", "key": "catalog"},
        {"label": "Менторы", "url_name": "accounts:mentors", "key": "mentors"},
    ]
    if user is None:
        return items
    items.append(
        {"label": "Моё обучение", "url_name": "enrollments:learning", "key": "learning"}
    )
    if user.is_mentor:
        items.append(
            {"label": "Мои воркшопы", "url_name": "workshops:studio", "key": "studio"}
        )
    return items

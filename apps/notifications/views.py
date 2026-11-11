from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def notification_list(request):
    """Лента уведомлений. Данные приходят из /api/notifications/."""
    return render(request, "pages/notifications.html", {"active_nav": "notifications"})

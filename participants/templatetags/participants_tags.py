from django import template
from django.utils import timezone
from datetime import timedelta

register = template.Library()

TIME_LIMIT = timedelta(minutes=10)

@register.filter
def time_remaining(joined_at_iso):
    """
    Given a joined_at ISO string from the session, returns the remaining
    session time as a 'M:SS' string. Used to server-render the timer
    display so there's no flash of '10:00' on page load.
    """
    if not joined_at_iso:
        return "10:00"

    try:
        joined_at = timezone.datetime.fromisoformat(joined_at_iso)
        if timezone.is_naive(joined_at):
            joined_at = timezone.make_aware(joined_at)

        remaining = (joined_at + TIME_LIMIT) - timezone.now()
        total_seconds = max(0, int(remaining.total_seconds()))
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
    except (ValueError, TypeError):
        return "10:00"
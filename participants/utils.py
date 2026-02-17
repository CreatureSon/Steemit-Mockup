from django.utils import timezone
from datetime import timedelta

TIME_LIMIT = timedelta(minutes=10)

def is_time_expired(request):
    joined_at = request.session.get("joined_at")

    if not joined_at:
        return False

    joined_at = timezone.datetime.fromisoformat(joined_at)

    if timezone.is_naive(joined_at):
        joined_at = timezone.make_aware(joined_at)

    return timezone.now() > joined_at + TIME_LIMIT
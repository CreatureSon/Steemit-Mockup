from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def simple_time(value):
    """
    Convert datetime to simple relative time format:
    - "Just now" (< 1 minute)
    - "X minutes ago" (< 1 hour)
    - "X hours ago" (< 1 day)
    - "Yesterday" (1 day ago)
    - "X days ago" (< 1 week)
    - "1 week ago" (< 2 weeks)
    - "X weeks ago" (< 1 month)
    - "1 month ago" (< 2 months)
    - "X months ago" (< 1 year)
    - "1 year ago" or "X years ago"
    """
    if not value:
        return ""
    
    now = timezone.now()
    diff = now - value
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Just now"
    elif seconds < 3600:  # Less than 1 hour
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:  # Less than 1 day
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif seconds < 172800:  # Less than 2 days
        return "Yesterday"
    elif seconds < 604800:  # Less than 1 week
        days = int(seconds / 86400)
        return f"{days} days ago"
    elif seconds < 1209600:  # Less than 2 weeks
        return "1 week ago"
    elif seconds < 2592000:  # Less than 30 days
        weeks = int(seconds / 604800)
        return f"{weeks} weeks ago"
    elif seconds < 5184000:  # Less than 60 days
        return "1 month ago"
    elif seconds < 31536000:  # Less than 1 year
        months = int(seconds / 2592000)
        return f"{months} months ago"
    elif seconds < 63072000:  # Less than 2 years
        return "1 year ago"
    else:
        years = int(seconds / 31536000)
        return f"{years} years ago"
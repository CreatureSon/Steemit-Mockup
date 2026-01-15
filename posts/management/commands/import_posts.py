import json
import bleach
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from posts.models import Post
from django.utils.dateparse import parse_datetime

ALLOWED_TAGS = [
    'p', 'br', 'hr', 'em', 'strong', 'a', 'img', 'center'
]

ALLOWED_ATTRS = {
    'a': ['href', 'title', 'rel'],
    'img': ['src', 'alt']
}

class Command(BaseCommand):
    help = "Import posts from JSON file"

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to JSON file to import')

    def handle(self, *args, **options):
        json_file = options['json_file']
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for post_data in data:

            raw_text = post_data.get('text', '')
            clean_text = bleach.clean(
                raw_text,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRS,
                strip=True
            )

            post, created = Post.objects.update_or_create(
                author=post_data['author'],
                permlink=post_data['permlink'],
                defaults={
                    'user': None, #NOT A REAL USER
                    'title': post_data.get('title', ''),
                    'text': clean_text,
                    'votes': post_data.get('votes', 0),
                    'payout': post_data.get('payout', "$0.00"),
                    'image_url': post_data.get('image', ''),
                    'date': parse_datetime(post_data.get('created'))
                }
            )
                
            post.save()
            self.stdout.write(self.style.SUCCESS(f'Imported post: {post.title}'))

# All posts visible to a participant
#Post.objects.filter(
#   Q(user=request.user) | Q(user__isnull=True)
#)

# Only Steem Posts
#Post.objects.filter(user__isnull=True)

# Only Local Posts
#Post.objects.filter(user__isnull=False)
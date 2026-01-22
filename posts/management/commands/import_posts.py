import json
import bleach
import markdown
import re
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime
from posts.models import Post
from django.utils.dateparse import parse_datetime

ALLOWED_TAGS = [
    'p', 'br', 'hr', 'em', 'strong', 'sup',
    'a', 'img', 'b', 'i', 'u', 's', 'span', 'div',
    'ul', 'ol', 'li', 'blockquote', 'center',
    'h1','h2','h3','h4','h5','h6',
    'pre','code'
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

            raw_text = raw_text.replace('\u200e', '').replace('\u200b', '')
            raw_text = re.sub(r'(^|\n)\s+(!\[)', r'\1\2', raw_text)

            html_text = markdown.markdown(
                raw_text, 
                extensions=['extra', 'md_in_html']
            )

            body = bleach.clean(
                html_text,
                tags=ALLOWED_TAGS,
                attributes=ALLOWED_ATTRS,
                strip=True
            )

            soup = BeautifulSoup(html_text, 'html.parser')
            for img in soup.find_all('img'):
                img.decompose()

            body_preview = soup.get_text(separator=' ', strip=True)

            post, created = Post.objects.update_or_create(
                author=post_data['author'],
                permlink=post_data['permlink'],
                defaults={
                    'user': None, #NOT A REAL USER
                    'title': post_data.get('title', ''),
                    'text': body,
                    'body_preview': body_preview,
                    'votes': post_data.get('votes', 0),
                    'payout': post_data.get('payout', "$0.00"),
                    'image_url': post_data.get('image', ''),
                    'date': parse_datetime(post_data.get('created'))
                }
            )
                
            print("RAW TEXT:", repr(raw_text[:100]))
            print("HTML TEXT:", html_text[:200])
            print("BODY:", body[:200])
            print("BODY PREVIEW:", body_preview[:200])

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
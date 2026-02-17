import json
import re
from bs4 import BeautifulSoup
import markdown
from django.core.management.base import BaseCommand
from django.utils import timezone
from posts.models import Comment, Post

class Command(BaseCommand):
    help = 'Import posts from posts.json into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'json_file',
            type=str,
            help='Path to the posts.json file'
        )

    # Fix Markdown tables: add leading/trailing pipes to rows missing them
    # Only process lines that are part of a table (near a separator row |---|)
    def fix_markdown_tables(self, text):
        lines = text.split('\n')
        result = []
        
        # First pass: identify all separator rows
        separator_indices = set()
        for i, line in enumerate(lines):
            if re.match(r'^\s*\|[\s\-|]+\|\s*$', line):
                separator_indices.add(i)

        for i, line in enumerate(lines):
            # Skip if line doesn't contain |
            if '|' not in line:
                result.append(line)
                continue
            
            # Check if this line is part of a table
            # (has a separator nearby or has | in multiple consecutive lines)
            is_table_row = False

            # Check if there's a separator within 10 lines
            for sep_idx in separator_indices:
                if abs(i - sep_idx) <= 10:
                    is_table_row = True
                    break
            
            # If part of table and missing pipes, add them
            if is_table_row:
                stripped = line.strip()
                if not stripped.startswith('|'):
                    line = '|' + line
                if not stripped.endswith('|'):
                    line = line + '|'
                    
            result.append(line)

        return '\n'.join(result)

    def process_markdown_body(self, text):
        '''Process markdown body with all the transformations'''
        body = text
        body = re.sub(r'\n +(<[a-zA-Z][^>]*>)', r'\n\1', body)
        body = re.sub(r'<([^>]+?)(\w+)\s*=\s*(["\'])', r'<\1\2=\3', body)

        # Convert Standalone Image URLs to Markdown
        body = re.sub(
            r'(?<![!\(\"<])^(https?://[^\s]+\.(?:jpg|jpeg|png|gif|webp|bmp))(?![)\">])',
            r'![\1](\1)',
            body,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # Convert Standalone Videos to Markdown
        body = re.sub(
            r'(?<![!\(\"<])^(https?://(?:www\.)?(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/|vimeo\.com/|dai\.ly/)[^\s]+)(?![)\">])',
            r'[Video](\1)',
            body,
            flags=re.MULTILINE | re.IGNORECASE
        )

        # Convert Standalone Links to Markdown
        body = re.sub(
            r'(?<![!\(\"<])^(https?://[^\s]+)(?![)\">])',
            r'[Link](\1)',
            body,
            flags=re.MULTILINE | re.IGNORECASE
        )

        body = self.fix_markdown_tables(body)

        def should_add_markdown_block(match):
            # Get the current line (everything after the last newline before the tag)
            start_of_line = match.string.rfind('\n', 0, match.start()) + 1
            current_line = match.string[start_of_line:match.start()]
            
            # Check if line contains Markdown syntax: |, #, *, -, `, [, !
            tag_content = match.group(1)
            if re.search(r'[\|#*\-`\[!]', current_line):
                return f'<div{tag_content} markdown="1">'  # Use markdown="1" for inline
            
            return f'<div{tag_content} markdown="block">'  # Use markdown="block" for standalone
        body = re.sub(r'<div([^>]*)>', should_add_markdown_block, body)

        def should_add_markdown_block_center(match):
            start_of_line = match.string.rfind('\n', 0, match.start()) + 1
            current_line = match.string[start_of_line:match.start()]
            
            if re.search(r'[\|#*\-`\[!]', current_line):
                return '<center markdown="1">'  # Use markdown="1" for inline
            
            return '<center markdown="block">'  # Use markdown="block" for standalone
        body = re.sub(r'<center>', should_add_markdown_block_center, body)

        body = re.sub(r'(<(?:div|center)[^>]*markdown="block"[^>]*>)\s*', r'\1\n', body)

        return body

    def create_body_preview(self, text):
        """Create a preview from markdown text"""
        md = markdown.Markdown(extensions=['extra'])
        html_content = md.convert(text)

        soup = BeautifulSoup(html_content, 'html.parser')
        for img in soup.find_all('img'):
            img.decompose()
        body_preview = soup.get_text(separator=' ', strip=True)

        # Strip Markdown formatting
        body_preview = re.sub(
            r'\|[^\n]+\||\|-+\||!\[[^\]]*\]\([^\)]+\)|\[([^\]]+)\]\([^\)]+\)|\*\*([^\*]+)\*\*|\*([^\*]+)\*|#{1,6}\s+|\s+',
            lambda m: (m.group(1) or m.group(2) or ' '),
            body_preview
        ).strip()

        # Remove any images that got left over
        body_preview = re.sub(r'\S+\.(jpg|jpeg|png|gif|webp|bmp)', '', body_preview, flags=re.IGNORECASE)

        # Get first 100 words
        words = body_preview.split()[:100]
        return ' '.join(words)

    def import_comments(self, post, comments_data, parent=None):
        """Recursively import comments and nested replies"""
        comment_count = 0
        
        for comment_data in comments_data:
            try:
                date = timezone.datetime.fromisoformat(comment_data['created'].replace('Z', '+00:00'))
                
                # Process comment body
                processed_body = self.process_markdown_body(comment_data['body'])
                
                # Create or update comment
                comment, created = Comment.objects.update_or_create(
                    author=comment_data['author'],
                    permlink=comment_data['permlink'],
                    defaults={
                        'post': post,
                        'parent': parent,
                        'author_image': comment_data.get('author_image') or 'https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y&s=128',
                        'author_reputation': comment_data.get('author_reputation', 25),
                        'body': processed_body,
                        'date': date,
                        'votes': comment_data.get('votes', 0),
                        'payout': comment_data.get('payout', '0.000 SBD')
                    }
                )

                if created:
                    comment_count += 1
                    self.stdout.write(f'  Created comment by {comment.author}')
                
                # Recursively import nested replies
                if 'replies' in comment_data and comment_data['replies']:
                    nested_count = self.import_comments(post, comment_data['replies'], comment)
                    comment_count += nested_count

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'  Skipped comment by {comment_data.get("author", "unknown")}: {str(e)}'
                    )
                )

        return comment_count

    def handle(self, *args, **options):
        json_file = options['json_file']
        
        # Load JSON file
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                posts_data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {json_file}'))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Invalid JSON: {e}'))
            return
        
        # Import posts
        created_count = 0
        updated_count = 0
        skipped_count = 0
        total_comments = 0
        
        for post_data in posts_data:
            try:
                # Parse the date
                date = timezone.datetime.fromisoformat(post_data['created'].replace('Z', '+00:00'))
                
                body = self.process_markdown_body(post_data['text'])
                body_preview = self.create_body_preview(post_data['text'])

                # Create or update post
                post, created = Post.objects.update_or_create(
                    author=post_data['author'],
                    permlink=post_data['permlink'],
                    defaults={
                        'author_image': post_data.get('author_image') or 'https://www.gravatar.com/avatar/00000000000000000000000000000000?d=mp&f=y&s=128',
                        'author_reputation': post_data.get('author_reputation', 25),
                        'category': post_data['category'],
                        'category_name': post_data['category_name'],
                        'title': post_data['title'],
                        'body': body,
                        'body_preview': body_preview,
                        'image_url': post_data.get('image', ''),
                        'date': date,
                        'votes': post_data.get('votes', 0),
                        'payout': post_data.get('payout', '0.000 SBD')
                    }
                )

                if created:
                    created_count += 1
                    self.stdout.write(f'Created: {post.title}')
                else:
                    updated_count += 1
                    self.stdout.write(f'Updated: {post.title}')

                # Import Comments if they exist
                if 'comments' in post_data and post_data['comments']:
                    comment_count = self.import_comments(post, post_data['comments'])
                    total_comments += comment_count
                    self.stdout.write(f'  Imported {comment_count} comments for "{post.title}"')
     
            except Exception as e:
                skipped_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipped post by {post_data.get("author", "unknown")}: {str(e)}'
                    )
                )
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n=== Import Summary ==='))
        self.stdout.write(self.style.SUCCESS(f'Posts Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Posts Updated: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'Comments Imported: {total_comments}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count}'))
        self.stdout.write(self.style.SUCCESS(f'Total Posts: {created_count + updated_count}'))
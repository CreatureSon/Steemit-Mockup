from django_unicorn.components import UnicornView
from django.contrib.contenttypes.models import ContentType
from posts.models import Post, Vote, Comment

class FeedResponsesView(UnicornView):
    post: Post = None
    post_id: int = 0
    payout: str = ""
    downvoted: bool = False
    upvoted: bool = False
    voted: bool = False
    resteemed: bool = False
    show_resteem_box: bool = False
    show_own_post_error: bool = False
    show_comment_box: bool = False
    total_votes: int = 0
    total_comments: int = 0
    is_own_post: bool = False

    def mount(self):
        #arg = self.component_args[0]
        self.post_id = self.component_kwargs["post_id"]
        self.post = Post.objects.get(id=self.post_id)

        user = self.request.user
        if user is not None and user.is_authenticated:
            post_content_type = ContentType.objects.get_for_model(Post)
            voted = Vote.objects.filter(
                user=user, 
                content_type=post_content_type, 
                object_id=self.post.id
            ).first()

            if voted:
                self.upvoted = voted.value == Vote.UPVOTE
                self.downvoted = voted.value == Vote.DOWNVOTE

            self.is_own_post = (self.post.user == user)
            self.resteemed = Post.objects.filter(
                resteemed_by=user, 
                original_post=self.post
            ).exists()

        self.name = self.post.author
        self.payout = self.post.payout
        self.voted = self.upvoted or self.downvoted
        self.total_votes = self.calc_votes()
        self.total_comments = self.calc_comments(user)
        #assert self.name == "jimmy"

    def upvote(self):
        self.toggle_vote(Vote.UPVOTE)

    def downvote(self):
        self.toggle_vote(Vote.DOWNVOTE)

    def toggle_vote(self, vote_type):
        user = self.request.user
        if not user.is_authenticated:
            return
        
        post_content_type = ContentType.objects.get_for_model(Post)
        voted = Vote.objects.filter(
            user=user, 
            content_type=post_content_type, 
            object_id=self.post.id
        ).first()

        if voted and voted.value == vote_type:
            voted.delete()
            self.update_ui_state(None)
        elif voted:
            voted.value = vote_type
            voted.save()
            self.update_ui_state(vote_type)
        else:
            Vote.objects.create(
                user=user, 
                content_object=self.post, 
                value=vote_type)
            self.update_ui_state(vote_type)

        self.total_votes = self.calc_votes()

    def update_ui_state(self, vote_value):
        self.upvoted = vote_value == Vote.UPVOTE
        self.downvoted = vote_value == Vote.DOWNVOTE  

    def calc_votes(self):
        post_content_type = ContentType.objects.get_for_model(Post)
        user_voted = 1 if Vote.objects.filter(
            user=self.request.user, 
            content_type=post_content_type, 
            object_id=self.post.id
        ).exists() else 0
        return self.post.votes + user_voted
    
    def calc_comments(self, user):
        npc_count = Comment.objects.filter(post=self.post, user=None).count()
        if user is not None and user.is_authenticated:
            participant_count = Comment.objects.filter(post=self.post, user=user).count()
            return npc_count + participant_count
        else:
            return npc_count

    def toggle_resteem(self):
        if self.resteemed:
            return
        if self.is_own_post:
            self.show_own_post_error = True
            self.show_resteem_box = False
        else:
            self.show_own_post_error = False
            self.show_resteem_box = not self.show_resteem_box

    def close_resteem_error(self):
        self.show_own_post_error = False

    def resteemed_post(self):
        user = self.request.user
        if not user.is_authenticated or self.is_own_post or self.resteemed:
            return
        
        Post.objects.create(
            user=user,
            author=self.post.author,
            permlink=None,
            author_image=self.post.author_image,
            title=self.post.title,
            body=self.post.body,
            body_preview=self.post.body_preview,
            image_url=self.post.image_url,
            category=self.post.category,
            category_name=self.post.category_name,
            votes=self.post.votes,
            payout=self.post.payout,
            resteemed_by=user,
            original_post=self.post
        )

        self.show_resteem_box = False
        self.resteemed = True

    def toggle_comment(self):
        self.show_comment_box = not self.show_comment_box
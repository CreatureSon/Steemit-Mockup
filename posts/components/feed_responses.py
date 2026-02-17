from django_unicorn.components import UnicornView
from django.contrib.contenttypes.models import ContentType
from posts.models import Post, Vote, Comment

class FeedResponsesView(UnicornView):
    post: Post
    payout: str
    downvoted: bool = False
    upvoted: bool = False
    voted: bool = False
    resteemed: bool = False
    show_resteem_box: bool = False
    show_comment_box: bool = False
    total_votes: int = 0
    total_comments: int = 0

    def mount(self):
        #arg = self.component_args[0]
        post_id = self.component_kwargs["post_id"]
        self.post = Post.objects.get(id=post_id)

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
        if not self.resteemed:
            self.show_resteem_box = not self.show_resteem_box

    def resteemed_post(self):
        self.show_resteem_box = False
        self.resteemed = True

    def toggle_comment(self):
        self.show_comment_box = not self.show_comment_box
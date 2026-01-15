from django_unicorn.components import UnicornView
from posts.models import Post, Vote

class PostResponsesView(UnicornView):
    post: Post
    payout: str
    downvoted: bool = False
    upvoted: bool = False
    voted: bool = False
    resteemed: bool = False
    show_resteem_box: bool = False
    show_comment_box: bool = False
    total_votes: int = 0

    def mount(self):
        #arg = self.component_args[0]
        
        post_id = self.component_kwargs["post_id"]
        self.post = Post.objects.get(id=post_id)

        user = self.request.user
        if user is not None and user.is_authenticated:
            voted = Vote.objects.filter(user=user, post=self.post).first()

            if voted:
                self.upvoted = voted.value == Vote.UPVOTE
                self.downvoted = voted.value == Vote.DOWNVOTE

        self.name = self.post.author
        self.payout = self.post.payout
        self.voted = self.upvoted or self.downvoted
        self.total_votes = self.calc_votes()

        #assert self.name == "jimmy"

    def upvote(self):
        self.toggle_vote(Vote.UPVOTE)

    def downvote(self):
        self.toggle_vote(Vote.DOWNVOTE)

    def toggle_vote(self, vote_type):
        user = self.request.user
        if not user.is_authenticated:
            return
        
        voted = Vote.objects.filter(user=user, post=self.post).first()
        
        if voted and voted.value == vote_type:
            voted.delete()
            self.update_ui_state(None)
        elif voted:
            voted.value = vote_type
            voted.save()
            self.update_ui_state(vote_type)
        else:
            Vote.objects.create(user=user, post=self.post, value=vote_type)
            self.update_ui_state(vote_type)

        self.total_votes = self.calc_votes()

    def update_ui_state(self, vote_value):
        self.upvoted = vote_value == Vote.UPVOTE
        self.downvoted = vote_value == Vote.DOWNVOTE  

    def calc_votes(self):
        user_voted = 1 if Vote.objects.filter(user=self.request.user, post=self.post).exists() else 0
        return self.post.votes + user_voted

    def toggle_resteem(self):
        if not self.resteemed:
            self.show_resteem_box = not self.show_resteem_box

    def resteemed_post(self):
        self.show_resteem_box = False
        self.resteemed = True

    def toggle_comment(self):
        self.show_comment_box = not self.show_comment_box
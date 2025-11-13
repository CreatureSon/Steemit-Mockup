from django_unicorn.components import UnicornView
from posts.models import Post

class PostResponsesView(UnicornView):
    post: Post
    tokens: str
    downvoted: bool = False
    upvoted: bool = False
    voted: bool = False
    resteemed: bool = False
    show_resteem_box: bool = False
    show_comment_box: bool = False

    def mount(self):
        #arg = self.component_args[0]
        
        post_id = self.component_kwargs["post_id"]

        self.post = Post.objects.get(id=post_id)
        self.name = self.post.user.username
        self.tokens = self.post.tokens
        self.voted = self.upvoted or self.downvoted

        #assert self.name == "jimmy"

    def upvote(self):
        self.toggle_vote('up')

    def downvote(self):
        self.toggle_vote('down')

    def toggle_vote(self, vote_type):
        if vote_type == 'up':
            self.upvoted = not self.upvoted
            if self.upvoted:
                self.downvoted = False
        elif vote_type == 'down':
            self.downvoted = not self.downvoted
            if self.downvoted:
                self.upvoted = False

        # Update overall vote status
        previous_voted = self.voted
        self.voted = self.upvoted or self.downvoted

        if self.voted and not previous_voted:
            self.post.votes += 1
        elif not self.voted:
            self.post.votes -= 1
        self.post.save()    

    def toggle_resteem(self):
        if not self.resteemed:
            self.show_resteem_box = not self.show_resteem_box

    def resteemed_post(self):
        self.show_resteem_box = False
        self.resteemed = True

    def toggle_comment(self):
        self.show_comment_box = not self.show_comment_box
from django_unicorn.components import UnicornView
from django.contrib.contenttypes.models import ContentType
from posts.models import Comment, Post, Vote

class CommentResponsesView(UnicornView):
    comment: Comment
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
        
        comment_id = self.component_kwargs["comment_id"]
        self.comment = Comment.objects.get(id=comment_id)

        user = self.request.user
        if user is not None and user.is_authenticated:

            comment_content_type = ContentType.objects.get_for_model(Comment)
            post = self.comment.post
            voted = Vote.objects.filter(
                content_type=comment_content_type,
                object_id=self.comment.id,
                user=user
            ).first()

            if voted:
                self.upvoted = voted.value == Vote.UPVOTE
                self.downvoted = voted.value == Vote.DOWNVOTE

        self.post = post
        self.name = self.comment.author
        self.payout = self.comment.payout
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
        
        comment_content_type = ContentType.objects.get_for_model(Comment)
        voted = Vote.objects.filter(
            user=user, 
            content_type=comment_content_type, 
            object_id=self.comment.id
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
                content_object=self.comment, 
                value=vote_type
            )
            self.update_ui_state(vote_type)

        self.total_votes = self.calc_votes()

    def update_ui_state(self, vote_value):
        self.upvoted = vote_value == Vote.UPVOTE
        self.downvoted = vote_value == Vote.DOWNVOTE  

    def calc_votes(self):
        comment_content_type = ContentType.objects.get_for_model(Comment)
        user_voted = 1 if Vote.objects.filter(
            user=self.request.user, 
            content_type=comment_content_type, 
            object_id=self.comment.id
        ).exists() else 0
        return self.comment.votes + user_voted

    def toggle_comment(self):
        self.show_comment_box = not self.show_comment_box
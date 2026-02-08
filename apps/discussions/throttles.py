from rest_framework.throttling import UserRateThrottle


class PostCreateThrottle(UserRateThrottle):
    scope = "post_create"


class CommentCreateThrottle(UserRateThrottle):
    scope = "comment_create"

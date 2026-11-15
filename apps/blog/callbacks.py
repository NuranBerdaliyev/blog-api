import json

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.http import HttpRequest

from apps.blog.models import Category, Comment, Post
from settings.conf import BLOG_ENV_ID

User = get_user_model()

TOP_CATEGORIES_LIMIT = 5
TOP_AUTHORS_LIMIT = 5
PERCENT_MULTIPLIER = 100
CHART_BAR_COLOR = "#5eb349"
LOCAL_ENV_ID = "local"


def environment_callback(request: HttpRequest) -> tuple[str, str]:
    if BLOG_ENV_ID == LOCAL_ENV_ID:
        return "Local", "warning"
    return "Production", "danger"


def drafts_badge_callback(request: HttpRequest) -> str:
    count = Post.objects.filter(status=Post.StatusChoices.DRAFT).count()
    return str(count) if count > 0 else ""


def dashboard_callback(request: HttpRequest, context: dict) -> dict:
    post_stats = Post.objects.aggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=Post.StatusChoices.PUBLISHED)),
        drafts=Count("id", filter=Q(status=Post.StatusChoices.DRAFT)),
    )
    total_posts = post_stats["total"]

    categories = Category.objects.annotate(post_count=Count("posts")).order_by("-post_count")[:TOP_CATEGORIES_LIMIT]
    top_authors = User.objects.annotate(post_count=Count("posts")).order_by("-post_count")[:TOP_AUTHORS_LIMIT]

    if total_posts > 0:
        published_percentage = int(post_stats["published"] * PERCENT_MULTIPLIER / total_posts)
        draft_percentage = int(post_stats["drafts"] * PERCENT_MULTIPLIER / total_posts)
    else:
        published_percentage = 0
        draft_percentage = 0

    context.update({
        "total_users": User.objects.count(),
        "published_posts": post_stats["published"],
        "draft_posts": post_stats["drafts"],
        "total_comments": Comment.objects.count(),
        "published_percentage": published_percentage,
        "draft_percentage": draft_percentage,
        "published_label": f"{published_percentage}%",
        "draft_label": f"{draft_percentage}%",
        "category_chart": json.dumps({
            "labels": [category.name for category in categories],
            "datasets": [{
                "label": "Posts count",
                "data": [category.post_count for category in categories],
                "backgroundColor": CHART_BAR_COLOR,
            }],
        }),
        "top_authors_table": {
            "headers": ["Author Email", "Full Name", "Posts Count"],
            "rows": [
                [author.email, f"{author.first_name} {author.last_name}", author.post_count]
                for author in top_authors
            ],
        },
    })
    return context
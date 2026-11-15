from datetime import date, timedelta
from typing import Any, Callable

from django.db.models import (
    Avg,
    Case,
    Count,
    Exists,
    F,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.utils import timezone
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag

PUBLISHED = Post.StatusChoices.PUBLISHED
DRAFT = Post.StatusChoices.DRAFT

PAGE_SIZE = 10
NEWEST_POSTS_LIMIT = 10
TOP_AUTHORS_LIMIT = 5
FEED_LIMIT = 50
TAGS_FEED_LIMIT = 20
EDIT_THRESHOLD = timedelta(hours=1)
UNCATEGORIZED = "Uncategorized"
AVERAGE_DIGITS = 2
HOT_COMMENTS_MIN = 10
NORMAL_COMMENTS_MIN = 3
POPULARITY_HOT = "hot"
POPULARITY_NORMAL = "normal"
POPULARITY_QUIET = "quiet"

def categories_by_name() -> QuerySet[Category]:
    '''All categorites sorted by name A to Z.'''
    return Category.objects.order_by("name")

def published_posts() -> QuerySet[Post]:
    '''Published posts, newest first.'''
    return Post.objects.filter(status=PUBLISHED).order_by("-created_at")

def newest_published_posts() -> QuerySet[Post]:
    '''The newest published posts.'''
    return published_posts()[:NEWEST_POSTS_LIMIT]

def post_by_slug(slug: str) -> Post | None:
    '''The post with this slug or None.'''
    return Post.objects.filter(slug=slug).first()

def active_users_count() -> int:
    '''Number of active non-staff users.'''
    return User.objects.filter(is_active=True, is_staff=False).count()

def has_drafts() -> bool:
    '''True if at least one draft exists'''
    return Post.objects.filter(status=DRAFT).exists()

def published_posts_page(page: int) -> QuerySet[Post]:
    '''One page of published posts, newest first'''
    offset = (page - 1) * PAGE_SIZE
    return published_posts()[offset:offset + PAGE_SIZE]

def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    '''Posts whose title contains the word, case-insensitive.'''
    return Post.objects.filter(title__icontains=word)

def users_with_email_domain(domain: str) -> QuerySet[User]:
    '''Users whose email ends with the domain.'''
    return User.objects.filter(email__iendswith=f"@{domain}")

def posts_without_category() -> QuerySet[Post]:
    '''Posts without a category'''
    return Post.objects.filter(category__isnull=True)

def categories_by_slugs(slugs: list[str]) -> QuerySet[Category]:
    '''Categories whose slug is in the list'''
    return Category.objects.filter(slug__in=slugs)

def posts_in_month(year: int, month: int) -> QuerySet[Post]:
    '''Posts created in the given month of the given year.'''
    return Post.objects.filter(created_at__year=year, created_at__month=month)

def posts_last_days(days: int) -> QuerySet[Post]:
    '''Posts created in the last days.'''
    return Post.objects.filter(created_at__gte=timezone.now() - timedelta(days=days))

def posts_between(start: date, end: date) -> QuerySet[Post]:
    '''Posts created from start day to end day inclusive.'''
    return Post.objects.filter(created_at__date__range=(start, end))

def author_published_posts(email: str) -> QuerySet[Post]:
    '''Published posts of the author with this email.'''
    return Post.objects.filter(author__email__iexact=email, status=PUBLISHED)

def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    '''Posts that have the tag'''
    return Post.objects.filter(tags__slug=tag_slug)

def comments_in_category(category_slug: str) -> QuerySet[Comment]:
    '''Comments on posts of the category'''
    return Comment.objects.filter(post__category__slug=category_slug)

def users_with_published_posts() -> QuerySet[User]:
    '''Users with at least one published post, each once.'''
    return User.objects.filter(posts__status=PUBLISHED).distinct()

def posts_without_tags() -> QuerySet[Post]:
    '''Posts without tags.'''
    return Post.objects.filter(tags__isnull=True)

def users_without_comments() -> QuerySet[User]:
    '''Users who never wrote a comment'''
    return User.objects.filter(comments__isnull=True)

def posts_with_both_tags(first_slug: str, second_slug: str) -> QuerySet[Post]:
    '''Posts that have both tags.'''
    return Post.objects.filter(tags__slug=first_slug).filter(tags__slug=second_slug)

def search_posts(text: str) -> QuerySet[Post]:
    '''Posts with the text in title or body, case-insesitive.'''
    return Post.objects.filter(Q(title__icontains=text) | Q(body__icontains=text))

def published_posts_missing_info() -> QuerySet[Post]:
    '''Published posts without category or tags.'''
    return Post.objects.filter(
        Q(category__isnull=True) | Q(tags__isnull=True),
        status=PUBLISHED,
    ).distinct()

def edited_posts() -> QuerySet[Post]:
    '''Posts edited later than the threshold after creation.'''
    return Post.objects.filter(updated_at__gt=F("created_at") + EDIT_THRESHOLD)

def comments_by_post_author() -> QuerySet[Comment]:
    '''Comments written by the post author under their own post.'''
    return Comment.objects.filter(author=F("post__author"))

def comments_before_post() -> QuerySet[Comment]:
    '''Comments created before their post'''
    return Comment.objects.filter(created_at__lt=F("post__created_at"))

def published_authors_emails() -> list[str]:
    '''Unique sorted emails of authors with published posts.'''
    return list(
        Post.objects.filter(status=PUBLISHED)
        .values_list("author__email", flat=True)
        .distinct()
        .order_by("author__email")
    )

def published_posts_overview() -> list[dict[str, Any]]:
    '''Title, author email and category name of published posts.'''
    return list(
        Post.objects.filter(status=PUBLISHED).values(
            "title",
            author_email=F("author__email"),
            category_name=Coalesce("category__name", Value(UNCATEGORIZED)),
        )
    )

def posts_stats() -> dict[str, Any]:
    '''Post counts and first and last post dates'''
    return Post.objects.aaggregate(
        total=Count("id"),
        published=Count("id", filter=Q(status=PUBLISHED)),
        drafts = Count("id", filter=Q(status=DRAFT)),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at"),
    )

def average_comments_per_post() -> float:
    '''Average number of comments on a published post.'''
    result = (
        Post.objects.filter(status=PUBLISHED)
        .annotate(comment_total=Count("comments"))
        .aggregate(average=Avg("comment_total", default=0.0))
    )
    return round(result["average"], AVERAGE_DIGITS)

def categories_with_post_count() -> QuerySet[Category]:
    '''Categories with post_count, most posts first.'''
    return Category.objects.annotate(post_count=Count("posts")).order_by("-post_count", "name")

def categories_with_published_count() -> QuerySet[Category]:
    '''Categories with published_count.'''
    return Category.objects.annotate(
        published_count=Count("posts", filter=Q(posts__status=PUBLISHED))
    )

def top_authors() -> QuerySet[User]:
    """Top users by number of published posts."""
    return User.objects.annotate(
        published_count=Count("posts", filter=Q(posts__status=PUBLISHED))
    ).order_by("-published_count")[:TOP_AUTHORS_LIMIT]


def popular_tags(min_posts: int) -> QuerySet[Tag]:
    """Tags used in at least min_posts posts."""
    return Tag.objects.annotate(post_count=Count("posts")).filter(post_count__gte=min_posts)


def posts_per_status() -> list[dict[str, Any]]:
    """Number of posts for each status."""
    return list(
        Post.objects.values("status").annotate(count=Count("id")).order_by("status")
    )


def users_activity() -> QuerySet[User]:
    """Users with post_count and comment_count."""
    return User.objects.annotate(
        post_count=Count("posts", distinct=True),
        comment_count=Count("comments", distinct=True),
    )


def search_users_by_full_name(text: str) -> QuerySet[User]:
    """Users whose full name contains the text."""
    return User.objects.annotate(
        full_name=Concat("first_name", Value(" "), "last_name")
    ).filter(full_name__icontains=text)


def published_posts_per_month() -> list[dict[str, Any]]:
    """Number of published posts in each month, oldest first."""
    return list(
        Post.objects.filter(status=PUBLISHED)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )


def posts_with_popularity() -> QuerySet[Post]:
    """Posts with comment_count and popularity."""
    return Post.objects.annotate(comment_count=Count("comments")).annotate(
        popularity=Case(
            When(comment_count__gte=HOT_COMMENTS_MIN, then=Value(POPULARITY_HOT)),
            When(comment_count__gte=NORMAL_COMMENTS_MIN, then=Value(POPULARITY_NORMAL)),
            default=Value(POPULARITY_QUIET),
        )
    )


def get_or_create_tag(name: str) -> tuple[Tag, bool]:
    """Get or create the tag by the slug of its name."""
    return Tag.objects.get_or_create(slug=slugify(name), defaults={"name": name})


def publish_old_drafts(days: int) -> int:
    """Publish drafts older than days."""
    now = timezone.now()
    return Post.objects.filter(
        status=DRAFT,
        created_at__lt=now - timedelta(days=days),
    ).update(status=PUBLISHED, updated_at=now)


def tag_category_posts(category_slug: str, tag_slug: str) -> int:
    """Add the tag to every post of the category."""
    tag = Tag.objects.get(slug=tag_slug)
    posts = list(Post.objects.filter(category__slug=category_slug))
    tag.posts.add(*posts)
    return len(posts)


def merge_categories(source_slug: str, target_slug: str) -> int:
    """Move posts from source category to target and delete source."""
    source = Category.objects.get(slug=source_slug)
    target = Category.objects.get(slug=target_slug)
    moved = Post.objects.filter(category=source).update(category=target)
    source.delete()
    return moved


def delete_inactive_users_comments() -> int:
    """Delete comments written by inactive users."""
    deleted, _ = Comment.objects.filter(author__is_active=False).delete()
    return deleted


def published_feed() -> list[str]:
    """Lines for the newest published posts."""
    posts = published_posts().select_related("author", "category")[:FEED_LIMIT]
    return [
        f"{post.title} | {post.author.email} | "
        f"{post.category.name if post.category else UNCATEGORIZED}"
        for post in posts
    ]


def newest_posts_with_tags() -> list[str]:
    """Lines with tags for the newest posts."""
    posts = Post.objects.prefetch_related("tags").order_by("-created_at")[:TAGS_FEED_LIMIT]
    return [
        f"{post.title}: {', '.join(tag.name for tag in post.tags.all())}"
        for post in posts
    ]


def categories_with_published_posts() -> dict[str, list[str]]:
    """Titles of published posts for every category."""
    categories = Category.objects.prefetch_related(
        Prefetch(
            "posts",
            queryset=Post.objects.filter(status=PUBLISHED).order_by("-created_at"),
            to_attr="published_posts_list",
        )
    )
    return {
        category.name: [post.title for post in category.published_posts_list]
        for category in categories
    }


def posts_with_last_comment() -> QuerySet[Post]:
    """Published posts with the text of the newest comment."""
    newest_comment = (
        Comment.objects.filter(post=OuterRef("pk"))
        .order_by("-created_at", "-id")
        .values("body")[:1]
    )
    return published_posts().annotate(last_comment=Subquery(newest_comment))


def posts_with_staff_comments() -> QuerySet[Post]:
    """Posts with at least one comment from a staff user."""
    return Post.objects.filter(
        Exists(Comment.objects.filter(post=OuterRef("pk"), author__is_staff=True))
    )


def users_with_draft_as_latest_post() -> QuerySet[User]:
    """Users whose newest post is a draft."""
    latest_status = (
        Post.objects.filter(author=OuterRef("pk"))
        .order_by("-created_at", "-id")
        .values("status")[:1]
    )
    return User.objects.annotate(latest_post_status=Subquery(latest_status)).filter(
        latest_post_status=DRAFT
    )


QUERIES: dict[int, Callable[..., Any]] = {
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,
    27: published_authors_emails,
    28: published_posts_overview,
    29: posts_stats,
    30: average_comments_per_post,
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post,
}
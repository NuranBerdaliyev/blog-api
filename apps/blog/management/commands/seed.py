import random
import time
from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from apps.blog.models import Category, Comment, Post, Tag

User = get_user_model()
fake = Faker()

SEED_PASSWORD = "password123"
DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500

INACTIVE_USER_RATIO = 0.15
STAFF_USER_RATIO = 0.10
PUBLISHED_POST_RATIO = 0.70
NO_CATEGORY_RATIO = 0.10

MIN_TITLE_WORDS = 3
MAX_TITLE_WORDS = 7
MIN_PARAGRAPHS = 3
MAX_PARAGRAPHS = 6
MIN_TAGS_PER_POST = 0
MAX_TAGS_PER_POST = 5
MIN_COMMENT_SENTENCES = 1
MAX_COMMENT_SENTENCES = 3
EMAIL_SUFFIX_MIN = 1
EMAIL_SUFFIX_MAX = 9999
DEFAULT_SLUG = "post"
FIRST_SLUG_SUFFIX = 2

SUMMARY_LABEL_WIDTH = 11
SUMMARY_COUNT_WIDTH = 4
ELAPSED_DIGITS = 2

CATEGORIES_LIST = ["Python", "Django", "DevOps", "Frontend", "Backend", "AI / ML", "Design", "Management"]
TAGS_LIST = [
    "DRF", "SQL", "Docker", "Git", "Celery", "Redis", "FastAPI", "React",
    "Vue", "CI-CD", "Testing", "Asyncio", "ORM", "Linux", "Security",
    "GraphQL", "Microservices", "Nginx", "Agile", "REST",
]


class Command(BaseCommand):
    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--users", type=int, default=DEFAULT_USERS, help="Number of users to create")
        parser.add_argument("--posts", type=int, default=DEFAULT_POSTS, help="Number of posts to create")
        parser.add_argument("--comments", type=int, default=DEFAULT_COMMENTS, help="Number of comments to create")
        parser.add_argument("--clear", action="store_true", help="Delete existing data before seeding")

    def handle(self, *args: Any, **options: Any) -> None:
        users_count: int = options["users"]
        posts_count: int = options["posts"]
        comments_count: int = options["comments"]
        clear: bool = options["clear"]

        if users_count < 0 or posts_count < 0 or comments_count < 0:
            raise CommandError("Numbers of entities cannot be negative.")

        if clear:
            remaining_users = User.objects.filter(is_superuser=True).count()
            remaining_published = 0
        else:
            remaining_users = User.objects.count()
            remaining_published = Post.objects.filter(status=Post.StatusChoices.PUBLISHED).count()

        if (posts_count > 0 or comments_count > 0) and remaining_users + users_count == 0:
            raise CommandError("Cannot create posts or comments because there are no users in the database.")
        if comments_count > 0 and posts_count == 0 and remaining_published == 0:
            raise CommandError("Cannot create comments because there are no published posts.")

        start_time = time.time()

        with transaction.atomic():
            if clear:
                self.stdout.write(self.style.WARNING("Clearing database..."))
                Comment.objects.all().delete()
                Post.objects.all().delete()
                Tag.objects.all().delete()
                Category.objects.all().delete()
                User.objects.filter(is_superuser=False).delete()
                self.stdout.write(self.style.SUCCESS("Database cleared successfully!"))

            users_created = self._create_users(users_count)
            categories_created = self._create_categories()
            tags_created = self._create_tags()
            posts_created = self._create_posts(posts_count, comments_count > 0, remaining_published > 0)
            comments_created = self._create_comments(comments_count)

        elapsed_time = round(time.time() - start_time, ELAPSED_DIGITS)

        self._write_summary("Users", users_created)
        self._write_summary("Categories", categories_created)
        self._write_summary("Tags", tags_created)
        self._write_summary("Posts", posts_created)
        self._write_summary("Comments", comments_created)
        self.stdout.write(self.style.SUCCESS(f"Done in {elapsed_time} seconds"))

    def _write_summary(self, label: str, count: int) -> None:
        self.stdout.write(f"{label + ':':<{SUMMARY_LABEL_WIDTH}}{count:>{SUMMARY_COUNT_WIDTH}} created")

    def _create_users(self, count: int) -> int:
        if count == 0:
            return 0

        used_emails = set(User.objects.values_list("email", flat=True))
        hashed_password = make_password(SEED_PASSWORD)
        users_to_create = []

        for _ in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()
            base_local = f"{slugify(first_name)}_{slugify(last_name)}"
            domain = fake.free_email_domain()
            email = f"{base_local}@{domain}"
            while email in used_emails:
                suffix = random.randint(EMAIL_SUFFIX_MIN, EMAIL_SUFFIX_MAX)
                email = f"{base_local}{suffix}@{domain}"
            used_emails.add(email)

            users_to_create.append(User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=hashed_password,
                is_active=random.random() >= INACTIVE_USER_RATIO,
                is_staff=random.random() < STAFF_USER_RATIO,
            ))

        return len(User.objects.bulk_create(users_to_create))

    def _create_categories(self) -> int:
        existing_slugs = set(Category.objects.values_list("slug", flat=True))
        categories_to_create = [
            Category(name=name, slug=slugify(name))
            for name in CATEGORIES_LIST
            if slugify(name) not in existing_slugs
        ]
        return len(Category.objects.bulk_create(categories_to_create))

    def _create_tags(self) -> int:
        existing_slugs = set(Tag.objects.values_list("slug", flat=True))
        tags_to_create = [
            Tag(name=name, slug=slugify(name))
            for name in TAGS_LIST
            if slugify(name) not in existing_slugs
        ]
        return len(Tag.objects.bulk_create(tags_to_create))

    def _create_posts(self, count: int, need_published: bool, has_published: bool) -> int:
        if count == 0:
            return 0

        user_ids = list(User.objects.values_list("id", flat=True))
        category_ids = list(Category.objects.values_list("id", flat=True))
        tag_ids = list(Tag.objects.values_list("id", flat=True))
        used_slugs = set(Post.objects.values_list("slug", flat=True))

        posts_to_create = []
        for _ in range(count):
            title = fake.sentence(nb_words=random.randint(MIN_TITLE_WORDS, MAX_TITLE_WORDS)).rstrip(".")
            base_slug = slugify(title) or DEFAULT_SLUG
            slug = base_slug
            suffix = FIRST_SLUG_SUFFIX
            while slug in used_slugs:
                slug = f"{base_slug}-{suffix}"
                suffix += 1
            used_slugs.add(slug)

            is_published = random.random() < PUBLISHED_POST_RATIO
            category_id = None if random.random() < NO_CATEGORY_RATIO else random.choice(category_ids)

            posts_to_create.append(Post(
                author_id=random.choice(user_ids),
                title=title,
                slug=slug,
                body="\n\n".join(fake.paragraphs(nb=random.randint(MIN_PARAGRAPHS, MAX_PARAGRAPHS))),
                category_id=category_id,
                status=Post.StatusChoices.PUBLISHED if is_published else Post.StatusChoices.DRAFT,
            ))

        if need_published and not has_published:
            if not any(post.status == Post.StatusChoices.PUBLISHED for post in posts_to_create):
                posts_to_create[0].status = Post.StatusChoices.PUBLISHED

        created_posts = Post.objects.bulk_create(posts_to_create)

        post_tag_model = Post.tags.through
        relations = []
        for post in created_posts:
            tags_amount = min(random.randint(MIN_TAGS_PER_POST, MAX_TAGS_PER_POST), len(tag_ids))
            for tag_id in random.sample(tag_ids, k=tags_amount):
                relations.append(post_tag_model(post_id=post.id, tag_id=tag_id))
        if relations:
            post_tag_model.objects.bulk_create(relations)

        return len(created_posts)

    def _create_comments(self, count: int) -> int:
        if count == 0:
            return 0

        published_ids = list(
            Post.objects.filter(status=Post.StatusChoices.PUBLISHED).values_list("id", flat=True)
        )
        if not published_ids:
            raise CommandError("Cannot create comments because there are no published posts.")

        user_ids = list(User.objects.values_list("id", flat=True))
        comments_to_create = [
            Comment(
                post_id=random.choice(published_ids),
                author_id=random.choice(user_ids),
                body=" ".join(fake.sentences(nb=random.randint(MIN_COMMENT_SENTENCES, MAX_COMMENT_SENTENCES))),
            )
            for _ in range(count)
        ]
        return len(Comment.objects.bulk_create(comments_to_create))
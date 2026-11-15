from datetime import timedelta
from typing import Any, Callable

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection
from django.db.models import Count, Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.management.commands.seed import CATEGORIES_LIST, TAGS_LIST
from apps.blog.models import Post
from apps.blog.queries import QUERIES

PREVIEW_ROWS = 5
MUTATING_QUERIES = frozenset(range(40, 45))
FIRST_PAGE = 1
SAMPLE_DAYS = 30
SAMPLE_RANGE_DAYS = 90
SAMPLE_MIN_POSTS = 5
SAMPLE_CATEGORIES_COUNT = 2
FULL_NAME_PREFIX = 3
PAIR_TAGS = 2
NEW_TAG_NAME = "Django ORM"

def build_arguments() -> dict[int, dict[str, Any]]:
    now = timezone.now()
    post = (
        Post.objects.select_related("author")
        .filter(status=Post.StatusChoices.PUBLISHED)
        .order_by("-created_at")
        .first()
    )
    user = User.objects.order_by("id").first()
    tagged = Post.objects.annotate(tag_total=Count("tags")).filter(tag_total__gte=PAIR_TAGS).first()
    category_slugs = [slugify(name) for name in CATEGORIES_LIST]
    tag_slugs = [slugify(name) for name in TAGS_LIST]
    pair = list(tagged.tags.values_list("slug", flat=True)[:PAIR_TAGS]) if tagged else []

    if len(pair) < PAIR_TAGS:
        pair = tag_slugs[:PAIR_TAGS]

    slug = post.slug if post else ""
    email = post.author.email if post else ""
    word = post.title.split()[0] if post else ""
    year = post.created_at.year if post else now.year
    month = post.created_at.month if post else now.month
    domain = user.email.split("@")[1] if user else ""
    first_name = user.first_name if user else ""
    last_name = user.last_name if user else ""

    return {
        4: {"slug": slug},
        7: {"page": FIRST_PAGE},
        8: {"word": word},
        9: {"domain": domain},
        11: {"slugs": category_slugs[:SAMPLE_CATEGORIES_COUNT]},
        12: {"year": year, "month": month},
        13: {"days": SAMPLE_DAYS},
        14: {
            "start": (now - timedelta(days=SAMPLE_RANGE_DAYS)).date(),
            "end": now.date()
        },
        15: {"email": email},
        16: {"tag_slug": tag_slugs[0]},
        17: {"category_slug": category_slugs[0]},
        21: {"first_slug": pair[0], "second_slug": pair[1]},
        22: {"text": word},
        34: {"min_posts": SAMPLE_MIN_POSTS},
        37: {"text": f"{first_name} {last_name[:FULL_NAME_PREFIX]}"},
        40: {"name": NEW_TAG_NAME},
        41: {"days": SAMPLE_DAYS},
        42: {"category_slug": category_slugs[0], "tag_slug": tag_slugs[0]},
        43: {"source_slug": category_slugs[-1], "target_slug": category_slugs[-2]},
    }

class Command(BaseCommand):
    help = "Run ORM queries and show results with the number of SQL queries."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--number", type=int, default=None, help="Run only this query")
        parser.add_argument("--sql", action="store_true", help="Print SQL of the queries")

    def handle(self, *args: Any, **options: Any) -> None:
        number: int | None = options["number"]
        show_sql: bool = options["sql"]

        if number is None:
            numbers = [item for item in sorted(QUERIES) if item not in MUTATING_QUERIES]
        elif number in QUERIES:
            numbers = [number]
        else:
            raise CommandError(f"Query #{number} does not exist.")

        arguments = build_arguments()
        for item in numbers:
            self._run(item, QUERIES[item], arguments.get(item, {}), show_sql)

    def _run(
        self,
        number: int,
        function: Callable[..., Any],
        arguments: dict[str, Any],
        show_sql: bool,
    ) -> None:
        with CaptureQueriesContext(connection) as context:
            result = function(**arguments)
            queryset = result if isinstance(result, QuerySet) else None
            value = list(result) if queryset is not None else result

        count = len(context.captured_queries)
        noun = "query" if count == 1 else "queries"
        self.stdout.write(f"#{number} {function.__name__} — {count} SQL {noun}")

        if show_sql:
            for captured in context.captured_queries:
                self.stdout.write(captured["sql"])

        annotation_names = list(queryset.query.annotations) if queryset is not None else []
        self._write_result(value, annotation_names)

    def _write_result(self, value: Any, annotation_names: list[str]) -> None:
        if isinstance(value, dict):
            rows: list[Any] = [f"{key}: {item}" for key, item in value.items()]
        elif isinstance(value, list):
            rows = value
        else:
            self.stdout.write(f"  {value}")
            return

        for row in rows[:PREVIEW_ROWS]:
            self.stdout.write(f"  {self._format_row(row, annotation_names)}")
        self.stdout.write(f"  ({len(rows)} rows)")

    def _format_row(self, row: Any, annotation_names: list[str]) -> str:
        if isinstance(row, Model) and annotation_names:
            values = {name: getattr(row, name) for name in annotation_names}
            return f"{row} {values}"
        return str(row)
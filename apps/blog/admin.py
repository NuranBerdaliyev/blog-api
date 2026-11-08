from django.contrib import admin
from django.db import models
from django.db.models import Count, Prefetch, QuerySet
from django.http import HttpRequest, HttpResponseRedirect
from django.urls import reverse
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

from apps.blog.models import Category, Comment, Post, Tag

COMMENT_TRUNCATE_LENGTH = 50
COMMENTS_PER_PAGE = 10
SECTION_HEIGHT = 300


class PostTableSection(TableSection):
    verbose_name = "Posts"
    height = SECTION_HEIGHT
    related_name = "posts"
    fields = ["title", "status", "created_at"]


class CommentTableSection(TableSection):
    verbose_name = "Comments"
    height = SECTION_HEIGHT
    related_name = "comments"
    fields = ["author", "body", "created_at"]


class CommentInline(TabularInline):
    model = Comment
    tab = True
    extra = 0
    per_page = COMMENTS_PER_PAGE
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ("name", "slug", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    list_sections = [PostTableSection]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return (
            super()
            .get_queryset(request)
            .prefetch_related("posts")
            .annotate(posts_cnt=Count("posts"))
        )

    @display(description="Number of posts", ordering="posts_cnt")
    def post_count(self, obj: Category) -> int:
        return obj.posts_cnt


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "slug", "post_count")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).annotate(posts_cnt=Count("posts"))

    @display(description="Number of posts", ordering="posts_cnt")
    def post_count(self, obj: Tag) -> int:
        return obj.posts_cnt


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("post_title", "author_email", "short_body", "created_at")
    search_fields = ("body", "author__email", "post__title")
    list_filter_submit = True
    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    autocomplete_fields = ("post", "author")
    list_select_related = ("post", "author")

    @display(description="Post")
    def post_title(self, obj: Comment) -> str:
        return obj.post.title

    @display(description="Author")
    def author_email(self, obj: Comment) -> str:
        return obj.author.email

    @display(description="Comment")
    def short_body(self, obj: Comment) -> str:
        if len(obj.body) > COMMENT_TRUNCATE_LENGTH:
            return f"{obj.body[:COMMENT_TRUNCATE_LENGTH]}..."
        return obj.body


@admin.register(Post)
class PostAdmin(ModelAdmin):
    formfield_overrides = {
        models.TextField: {"widget": WysiwygWidget},
    }
    warn_unsaved_form = True
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author", "category", "tags")
    list_select_related = ("author", "category")
    readonly_fields = ("created_at", "updated_at")
    list_sections = [CommentTableSection]

    inlines = [CommentInline]

    list_display = (
        "header_column", "status_label", "category",
        "tags_dropdown", "comments_count", "created_at",
    )
    list_filter_submit = True
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("title", "body", "author__email")

    fieldsets = (
        ("Content", {"classes": ("tab",), "fields": ("title", "slug", "body")}),
        ("Classification", {"classes": ("tab",), "fields": ("category", "tags", "status")}),
        ("Meta", {"classes": ("tab",), "fields": ("author", "created_at", "updated_at")}),
    )

    actions = ["make_published", "make_draft"]
    actions_row = ["toggle_status_row"]
    actions_detail = ["open_comments_detail"]
    actions_list = ["publish_all_drafts_list"]
    actions_submit_line = ["save_and_publish_action"]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return (
            super()
            .get_queryset(request)
            .prefetch_related(
                "tags",
                Prefetch("comments", queryset=Comment.objects.select_related("author")),
            )
            .annotate(comm_cnt=Count("comments"))
        )

    @display(description="Title and Author", header=True)
    def header_column(self, obj: Post) -> tuple[str, str]:
        return obj.title, obj.author.email

    @display(description="Status", label={"published": "success", "draft": "warning"})
    def status_label(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj: Post) -> dict:
        tags = obj.tags.all()
        return {
            "title": f"Tags ({len(tags)})",
            "items": [{"title": tag.name} for tag in tags],
        }

    @display(description="Comments", ordering="comm_cnt")
    def comments_count(self, obj: Post) -> int:
        return obj.comm_cnt

    @action(description="Publish selected posts")
    def make_published(self, request: HttpRequest, queryset: QuerySet) -> None:
        queryset.update(status=Post.StatusChoices.PUBLISHED)

    @action(description="Move selected posts to drafts")
    def make_draft(self, request: HttpRequest, queryset: QuerySet) -> None:
        queryset.update(status=Post.StatusChoices.DRAFT)

    @action(description="Toggle Status")
    def toggle_status_row(self, request: HttpRequest, object_id: int) -> HttpResponseRedirect:
        post = Post.objects.filter(pk=object_id).first()
        if post:
            post.status = (
                Post.StatusChoices.DRAFT
                if post.status == Post.StatusChoices.PUBLISHED
                else Post.StatusChoices.PUBLISHED
            )
            post.save(update_fields=["status", "updated_at"])
        return HttpResponseRedirect(
            request.META.get("HTTP_REFERER") or reverse("admin:blog_post_changelist")
        )

    @action(description="Open this post's comments")
    def open_comments_detail(self, request: HttpRequest, object_id: int) -> HttpResponseRedirect:
        return HttpResponseRedirect(f"{reverse('admin:blog_comment_changelist')}?post__id__exact={object_id}")

    @action(description="Publish all drafts")
    def publish_all_drafts_list(self, request: HttpRequest) -> HttpResponseRedirect:
        Post.objects.filter(status=Post.StatusChoices.DRAFT).update(status=Post.StatusChoices.PUBLISHED)
        return HttpResponseRedirect(reverse("admin:blog_post_changelist"))

    @action(description="Save & publish")
    def save_and_publish_action(self, request: HttpRequest, obj: Post) -> None:
        obj.status = Post.StatusChoices.PUBLISHED
        obj.save(update_fields=["status", "updated_at"])
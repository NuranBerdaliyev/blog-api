from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from apps.auths.models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("last_login",)

    list_display = ("user_header", "is_active_label", "is_staff_label", "posts_count")
    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )

    fieldsets = (
        ("Personal info", {"classes": ("tab",), "fields": ("first_name", "last_name", "email", "password")}),
        ("Permissions", {"classes": ("tab",), "fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"classes": ("tab",), "fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "first_name", "last_name", "password1", "password2"),
        }),
    )

    actions = ["activate_users", "deactivate_users"]

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        return super().get_queryset(request).annotate(p_cnt=Count("posts"))

    @display(description="User Info", header=True)
    def user_header(self, obj: User) -> tuple[str, str, str]:
        initials = f"{obj.first_name[:1]}{obj.last_name[:1]}".upper() or "U"
        return f"{obj.first_name} {obj.last_name}", obj.email, initials

    @display(description="Active", label={"active": "success", "inactive": "danger"})
    def is_active_label(self, obj: User) -> tuple[str, str]:
        return ("active", "Active") if obj.is_active else ("inactive", "Inactive")

    @display(description="Staff", label={"staff": "info", "regular": "warning"})
    def is_staff_label(self, obj: User) -> tuple[str, str]:
        return ("staff", "Staff") if obj.is_staff else ("regular", "Regular")

    @display(description="Posts Created", ordering="p_cnt")
    def posts_count(self, obj: User) -> int:
        return obj.p_cnt

    @action(description="Activate selected users")
    def activate_users(self, request: HttpRequest, queryset: QuerySet) -> None:
        queryset.update(is_active=True)

    @action(description="Deactivate selected users")
    def deactivate_users(self, request: HttpRequest, queryset: QuerySet) -> None:
        queryset.update(is_active=False)
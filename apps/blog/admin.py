from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.blog.models import Category, Tag, Post, Comment

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Post)
class PostAdmin(ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'body')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)

@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ('author', 'post', 'created_at')
    search_fields = ('body', 'author__email', 'post__title')
    list_filter = ('created_at',)
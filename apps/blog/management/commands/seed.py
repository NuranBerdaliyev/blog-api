import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from faker import Faker
from apps.blog.models import Category, Tag, Post, Comment

User = get_user_model()
fake = Faker(['ru_RU'])

class Command(BaseCommand):
    help = "Fill the database by fake data for testing"

    def add_arguments(self, parser):
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Delete the old data before filling database (except superusers)'
        )

    def handle(self, *args, **options):
        if options['clean']:
            self.stdout.write(self.style.WARNING("Removing database..."))
            Comment.objects.all().delete()
            Post.objects.all().delete()
            Tag.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("Old data is removed successfully!"))

        self.stdout.write("The data generation beginning...")

        users = []
        for _ in range(10):
            profile = fake.simple_profile()
            first_name = fake.first_name()
            last_name = fake.last_name()
            email = fake.unique.email()

            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password="password123"
            )
            users.append(user)
        self.stdout.write(f"Users created: {len(users)}")

        categories_names = ["Tech", "Travel", "Kitchen", "Sport", "Art", "Education"]
        categories = []
        for name in categories_names:
            slug = slugify(name, allow_unicode=True)
            if Category.objects.filter(slug=slug).exists():
                slug = f"{slug}-{random.randint(1, 100)}"
            category = Category.objects.create(name=name, slug=slug)
            categories.append(category)
        self.stdout.write(f"Categories created: {len(categories)}")

        tags_names = ["Python", "Django", "RestAPI", "Logic", "Life", "Advices", "Trends", "New"]
        tags = []
        for name in tags_names:
            slug = slugify(name, allow_unicode=True)
            if Tag.objects.filter(slug=slug).exists():
                slug = f"{slug}-{random.randint(1, 100)}"
            tag = Tag.objects.create(name=name, slug=slug)
            tags.append(tag)
        self.stdout.write(f"Tags created: {len(tags)}")

        posts=[]
        for _ in range(30):
            title = fake.sentence(nb_words=random.randint(3, 7)).rstrip('.')
            slug = slugify(title, allow_unicode=True)
            if Post.objects.filter(slug=slug).exists():
                slug = f"{slug}-{random.randint(1, 1000)}"

            post = Post.objects.create(
                author=random.choice(users),
                title=title,
                slug=slug,
                body="\n\n".join(fake.paragraphs(nb=random.randint(3, 6))),
                category=random.choice(categories),
                status=random.choice(Post.StatusChoices.values)
            )

            random_tags = random.sample(tags, k=random.randint(1, 4))
            post.tags.set(random_tags)
            posts.append(post)
        self.stdout.write(f"Posts created: {len(posts)}")

        comments_count = 0
        for post in posts:
            for _ in range(random.randint(0, 5)):
                Comment.objects.create(
                    post=post,
                    author=random.choice(users),
                    body=fake.text(max_nb_chars=200)
                )
                comments_count += 1
        self.stdout.write(f"Comments created: {comments_count}")

        self.stdout.write(self.style.SUCCESS("Database is filled successfully!"))

    


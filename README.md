# Django Blog API & Advanced Admin Panel

A modern web application built with Django 5.x, featuring a comprehensive blog platform with a highly optimized custom development data seeder and a customized, responsive administration panel powered by the **Django Unfold** theme (Tailwind CSS).

---

## 🛠 Tech Stack

* **Backend:** Python 3.11+, Django 5.x
* **Database:** PostgreSQL / SQLite3
* **Interface & Theme:** Django Unfold, Tailwind CSS
* **Data Generation:** Faker
* **Environment Management:** Python-dotenv / Django-decouple

---

## 🚀 Local Deployment

Follow these exact steps to set up and run the project locally:

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd <project-folder-name>
```

### 2. Configure the Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # For Linux/macOS
# or
venv\Scripts\activate     # For Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements/dev.txt
```

### 4. Setup Environment Variables
Create a `.env` file in the root directory of the project using the following template:
```env
BLOG_SECRET_KEY=your-super-secret-django-key
BLOG_ENV_ID=local
```

### 5. Apply Database Migrations
```bash
python manage.py migrate
```

### 6. Run the Data Seeder (Seed Command)
To populate the database with optimized mock data for development, execute the custom management command:
```bash
python manage.py seed --users 50 --posts 300 --comments 1500
```

**Available Command-Line Arguments:**
* `--users` (Default: `20`): Number of users to create.
* `--posts` (Default: `100`): Number of posts to create.
* `--comments` (Default: `500`): Number of comments to create.
* `--clear`: Optional flag. When passed, it deletes existing comments, posts, tags, categories, and all users **except superusers** before seeding.

### 7. Create Superuser & Start Server
```bash
python manage.py createsuperuser
python manage.py runserver
```
Once started, the administration panel will be available at: `http://127.0.0`

---

## ⚡ Seed Command Architecture & Optimization (`seed.py`)

The custom data generation command is engineered for maximum performance, minimizing database overhead and preventing crashes on consecutive runs:
* **Batch Insertions (`bulk_create`):** All records for users, categories, tags, posts, and comments are inserted into the database using single batch operations, reducing thousands of SQL queries down to a handful.
* **No N+1 M2M Insertion:** Rather than resolving Many-to-Many relationships inside a loop, tags are bound by performing a bulk insertion on the intermediate join table (`Post.tags.through`), satisfying strict performance requirements.
* **Proportional Generation Logic:** Adheres strictly to predefined distribution requirements: approximately 70% of posts are generated as `published`, 30% as `draft`, and around 10% are created without a category assigned.
* **In-Memory Cache Filtering (`set`):** Uniqueness checks for emails and slugs are handled entirely via Python `set` structures in RAM, eliminating redundant database query hits.
* **Single-Pass Password Hashing:** User passwords are encrypted exactly once using `make_password(SEED_PASSWORD)` before execution, avoiding massive performance bottlenecks.
* **Rigorous Validation:** Throws explicit `CommandError` instances if negative inputs are provided or if dependent relationships are missing (e.g., generating posts when there are no users).

Console output layout summary example:
```text
Users:       50 created
Categories:   8 created
Tags:        20 created
Posts:      300 created
Comments:  1500 created
Done in 2.41 seconds
```

---

## 🎨 Django Unfold Admin Panel Customization

The Django admin site has been heavily customized to provide a beautiful, responsive user interface:

* **Global UI Layouts:**
  * Configured a custom Tailwind CSS color palette (Emerald shades replacing default styles).
  * Interactive navigation sidebar featuring application grouping and specific Material Icons.
  * Real-time environment badge (`Local` / `Production`) rendered via callback mappings.
  * Global search overlay triggered with `Cmd+K` / `Ctrl+K` hotkeys.
  * Quick tabs layout filter views (**All / Published / Drafts**) directly over the post changelist.
* **Model Level Architecture Enhancements:**
  * **Users:** Form views are split into distinct functional tabs (*Personal info*, *Permissions*, *Important dates*). Includes built-in custom creation fieldsets and radio actions for instant bulk activation status updating.
  * **Posts:** Configured an embedded WYSIWYG text editor widget. Includes tabular comments inline configurations (10 comments per page limits), prepopulated title-to-slug mapping, and detailed row level toggle quick actions.
  * **Categories & Tags:** Database queries are optimized with `.annotate(Count(...))` to query post totals safely without N+1 query loops. Configured accordion-style `list_sections` row dropdowns for category structures.
  * **Comments:** Outfitted with `RangeDateTimeFilter` parameters and relational autocomplete inputs.
* **Admin Home Dashboard:** Features metric counter cards, analytical progress ratios, interactive bar charts for top categories, and optimized tabular tracking lists highlighting top-performing system authors.

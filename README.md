# Voter Management System

A Django-based voter management system with authentication, dashboard, and comprehensive voter data management functionality.

## Features

- **User Authentication**
  - Login with username/password
  - User registration (requires admin approval)
  - Logout functionality
  - Session management

- **Voter Management**
  - Full voter database with search and filtering
  - Hierarchical category system (Upazila → Union → Voter Area)
  - Excel file import for bulk voter data
  - Advanced search with autocomplete
  - Voter detail views with full information
  - Gender-based filtering
  - Pagination for large datasets

- **Dashboard**
  - Clean, modern UI using Bootstrap 5
  - Voter statistics (total, male, female counts)
  - Top categories by voter count
  - Quick action buttons
  - System status overview

- **Security**
  - CSRF protection
  - Password validation
  - Secure session handling
  - Login required for all voter pages
  - Rate limiting on API endpoints

## Project Structure

```
voter_project/
├── voter_project/          # Django project configuration
│   ├── settings.py         # Project settings
│   ├── urls.py            # URL routing
│   └── wsgi.py            # WSGI configuration
├── apps/
│   ├── core/              # Core application (auth, main dashboard)
│   │   ├── views.py       # Dashboard and auth views
│   │   ├── urls.py        # URL patterns
│   │   └── context_processors.py  # Global template context
│   └── voters/            # Voter management application
│       ├── models.py      # Voter, Category, ExcelColumnSchema models
│       ├── views.py       # Voter list, detail, category views
│       ├── urls.py        # Voter URL patterns
│       ├── admin.py       # Admin configuration
│       └── management/    # Management commands
│           └── commands/
│               ├── import_voters.py      # Excel import command
│               └── update_search_text.py # Search index update
├── templates/             # HTML templates
│   ├── base.html         # Base layout
│   ├── core/             # Core app templates
│   ├── voters/           # Voter app templates
│   │   ├── base_voters.html
│   │   ├── dashboard.html
│   │   ├── voter_list.html
│   │   ├── voter_detail.html
│   │   ├── category_list.html
│   │   └── category_detail.html
│   └── partials/         # Reusable components
├── static/               # Static files (CSS, JS, images)
├── logs/                 # Application logs
├── manage.py            # Django management script
├── requirements.txt     # Python dependencies
└── .env.example        # Environment variables template
```

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Setup Steps

1. **Clone or navigate to the project directory**
   ```bash
   cd D:\personal\voter_application\voter_project
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create environment file**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` file and update settings as needed (SECRET_KEY, DEBUG, etc.)

6. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser (admin account)**
   ```bash
   python manage.py createsuperuser
   ```
   Follow the prompts to create your admin account.

8. **Collect static files (for production)**
   ```bash
   python manage.py collectstatic
   ```

9. **Run the development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the application**
    - Main site: http://127.0.0.1:8000/
    - Admin panel: http://127.0.0.1:8000/admin/

## Usage

### First Time Setup

1. Start the development server
2. Navigate to http://127.0.0.1:8000/
3. You'll be redirected to the login page
4. Click "Sign up now" to register a new account
5. After registration, login to the admin panel (http://127.0.0.1:8000/admin/) with your superuser account
6. Activate the newly registered user account
7. Login with the activated account

### User Registration Flow

- New users register through the registration page
- Accounts are created as **inactive** by default
- Admin must activate accounts through the admin panel
- Only active users can login

### Admin Panel

Access the Django admin panel at `/admin/` to:
- Activate/deactivate user accounts
- Manage user permissions
- View and manage all users

## Configuration

### Environment Variables

Key environment variables in `.env`:

- `SECRET_KEY`: Django secret key (change in production!)
- `DEBUG`: Debug mode (True/False)
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `APP_NAME`: Application name displayed in UI
- `DATABASE_URL`: Database connection string (optional)

### Database Options

**SQLite (Default)**
- No configuration needed
- Database file: `db.sqlite3`

**PostgreSQL**
```env
DB_ENGINE=postgresql
DB_NAME=voter_project
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
```

**MySQL**
```env
DB_ENGINE=mysql
DB_NAME=voter_project
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

## Development

### Adding New Features

This project is designed to be extended with voter-related features:

1. **Models**: Add voter models in `apps/core/models.py`
2. **Views**: Add views in `apps/core/views.py`
3. **URLs**: Register URLs in `apps/core/urls.py`
4. **Templates**: Create templates in `templates/core/`
5. **Sidebar**: Update `templates/partials/sidebar.html` to add menu items

### Running Migrations

After modifying models:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Technology Stack

- **Backend**: Django 4.2+
- **Frontend**: Bootstrap 5, HTML5, CSS3, JavaScript
- **Icons**: Line Awesome, Remix Icons
- **Database**: SQLite (default), PostgreSQL, MySQL supported
- **Static Files**: Whitenoise for production serving

## Security Best Practices

- Change `SECRET_KEY` in production
- Set `DEBUG=False` in production
- Configure `ALLOWED_HOSTS` properly
- Use HTTPS in production
- Keep dependencies updated
- Regular security audits

## Logging

Application logs are stored in the `logs/` directory:
- `app.log`: General application logs
- `error.log`: Error logs
- `security.log`: Security-related events

## Docker Deployment

### Quick Start with Docker

1. **Copy environment file**
   ```bash
   copy .env.example .env
   ```

2. **Start services**
   ```bash
   docker-compose up -d
   ```

3. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. **Create superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access the application**
   - Main site: http://localhost:8090/
   - Admin panel: http://localhost:8090/admin/

### Docker Services

| Service | Description | Port |
|---------|-------------|------|
| `db` | PostgreSQL 15 database | 5432 |
| `web` | Django application | 8090 |

### Docker Commands

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild after changes
docker-compose up -d --build

# Import voter data
docker-compose exec web python manage.py import_voters --base-path "/app/election_votar_data"
```

## Production Deployment

### Environment Configuration

For production, set these environment variables:

```env
DEBUG=False
SECRET_KEY=your-secure-random-secret-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:password@host:5432/dbname
```

### Database Configuration

| Environment | Database | Configuration |
|-------------|----------|---------------|
| Development | SQLite | Default, no config needed |
| Production | PostgreSQL | Set `DATABASE_URL` or `DB_ENGINE=postgresql` |

### Static Files (WhiteNoise)

Static files are served using WhiteNoise in production:

```bash
python manage.py collectstatic --noinput
```

WhiteNoise is pre-configured in `settings.py` with compression enabled.

### Production Checklist

- [ ] Set `DEBUG=False`
- [ ] Generate secure `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up PostgreSQL database
- [ ] Run `collectstatic`
- [ ] Configure HTTPS/SSL
- [ ] Set up reverse proxy (nginx recommended)
- [ ] Configure logging
- [ ] Set up database backups

## User Permissions

### Role-Based Access

| Feature | Regular User | Staff | Superuser |
|---------|--------------|-------|-----------|
| View Voters | ✓ | ✓ | ✓ |
| Search & Filter | ✓ | ✓ | ✓ |
| View Categories | ✓ | ✓ | ✓ |
| Import Instructions | ✗ | ✓ | ✓ |
| Admin Panel | ✗ | ✗ | ✓ |
| Manage Areas | ✗ | ✗ | ✓ |
| Manage Voters | ✗ | ✗ | ✓ |

### Menu Visibility

- **Regular Users**: Voter Dashboard, Voter List, Categories
- **Staff Users**: Same as regular + Import Instructions
- **Superusers**: Full access including Admin Panel and Manage Areas

## Custom Error Pages

The application includes custom error pages for:

- **400 Bad Request**: Invalid request handling
- **404 Not Found**: Page not found with navigation options
- **500 Server Error**: Internal error with support information

Error pages are styled to match the application theme and provide helpful navigation.

## Support

For issues or questions, refer to the Django documentation:
- https://docs.djangoproject.com/

## License

This project is based on the clock_shop architecture and follows the same design patterns.

## Voter Data Import

### Excel File Structure

The import command expects Excel files (.xlsx) organized in a nested folder structure:

```
election_votar_data/
├── Upazila1/
│   ├── Union1/
│   │   ├── VoterArea1/
│   │   │   ├── male_voters.xlsx
│   │   │   └── female_voters.xlsx
│   │   └── VoterArea2/
│   │       └── voters.xlsx
│   └── Union2/
│       └── ...
└── Upazila2/
    └── ...
```

### Expected Excel Columns

The import command recognizes these column names (case-insensitive):

| Field | Recognized Column Names |
|-------|------------------------|
| Serial | Serial, serial, SL, sl, S.N., SN |
| Name | Name, name, NAME, নাম |
| Voter No | Voter No, voter_no, VoterNo, VOTER NO, ভোটার নম্বর |
| Father | Father, father, FATHER, Father Name, পিতা |
| Mother | Mother, mother, MOTHER, Mother Name, মাতা |
| Profession | Profession, profession, PROFESSION, পেশা |
| DOB | DOB, dob, Date of Birth, DateOfBirth, জন্ম তারিখ |
| Address | Address, address, ADDRESS, ঠিকানা |

Any additional columns will be stored in the `extra_data` JSON field.

### Import Commands

**Basic Import:**
```bash
python manage.py import_voters --base-path "path/to/excel/files"
```

**Clear existing data and reimport:**
```bash
python manage.py import_voters --base-path "path/to/excel/files" --clear
```

**Preview import (dry run):**
```bash
python manage.py import_voters --base-path "path/to/excel/files" --dry-run
```

**Update search index after manual changes:**
```bash
python manage.py update_search_text
```

### Gender Detection

Gender is automatically detected from the Excel filename:
- Files containing "female" → Female voters
- Files containing "male" → Male voters
- Other files → Unknown gender

## URL Structure

| URL | View | Description |
|-----|------|-------------|
| `/` | Dashboard | Main dashboard |
| `/voters/` | Voter Dashboard | Voter statistics and quick actions |
| `/voters/voters/` | Voter List | Searchable voter list with filters |
| `/voters/voters/<id>/` | Voter Detail | Individual voter information |
| `/voters/categories/` | Category List | Hierarchical category tree |
| `/voters/categories/<id>/` | Category Detail | Category with its voters |
| `/voters/api/categories/` | API | Category dropdown data (AJAX) |
| `/voters/api/search/` | API | Voter search autocomplete |

## API Endpoints

### GET /voters/api/categories/

Returns categories for dependent dropdowns.

**Parameters:**
- `parent_id`: Get children of a specific category
- `level`: Get categories at a specific level

**Response:**
```json
{
  "categories": [
    {"id": 1, "name": "Category Name", "code": "123", "level": 0, "has_children": true}
  ],
  "count": 1
}
```

### GET /voters/api/search/

Search voters with autocomplete.

**Parameters:**
- `q`: Search query (required, min 2 characters)
- `limit`: Max results (default: 15, max: 50)
- `mode`: "autocomplete" or "full"

**Response:**
```json
{
  "voters": [
    {"id": 1, "name": "John Doe", "voter_no": "123456", "father": "...", "mother": "...", "gender": "male"}
  ],
  "count": 1,
  "has_more": false
}
```

## Models

### Category
- Hierarchical structure (Upazila → Union → Voter Area)
- Stores area codes and full paths
- Tracks which categories have voter data

### Voter
- Core voter information (name, voter_no, father, mother, etc.)
- Links to category
- Extra data stored as JSON for flexibility
- Search text field for fast autocomplete

### ExcelColumnSchema
- Tracks discovered Excel column names
- Used for dynamic filtering options

## Extending the Application

### Adding New Voter Fields

1. Add field to `apps/voters/models.py`
2. Update the import command in `apps/voters/management/commands/import_voters.py`
3. Run migrations: `python manage.py makemigrations && python manage.py migrate`
4. Update templates as needed

### Adding New Views

1. Add view function in `apps/voters/views.py`
2. Add URL pattern in `apps/voters/urls.py`
3. Create template in `templates/voters/`
4. Update sidebar in `templates/partials/sidebar.html` if needed

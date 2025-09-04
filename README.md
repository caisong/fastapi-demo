# FastAPI Application

A modern FastAPI application with a complete development infrastructure including authentication, database management, testing, and containerization.

## Features

- **FastAPI Framework**: High-performance API with automatic OpenAPI documentation
- **Authentication**: JWT-based authentication with access and refresh tokens
- **Database**: SQLAlchemy ORM with PostgreSQL/SQLite support
- **Migrations**: Alembic for database schema management
- **Testing**: Comprehensive test suite with pytest
- **Containerization**: Docker and Docker Compose support
- **Development Tools**: Hot reload, linting, formatting
- **Security**: Password hashing, CORS, rate limiting
- **API Documentation**: Automatic Swagger/OpenAPI docs

## Quick Start

> **Windows Users**: If you encounter PostgreSQL driver issues, see [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for detailed Windows-specific instructions.

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Copy the example environment file and configure it:

```bash
copy .env.example .env
```

Edit `.env` with your configuration settings.

### 3. Initialize Database

```bash
python scripts/init_db.py
```

### 4. Run Development Server

```bash
python scripts/dev.py
```

The API will be available at:
- Main API: http://127.0.0.1:8000
- Documentation: http://127.0.0.1:8000/docs
- Alternative docs: http://127.0.0.1:8000/redoc
- Admin Interface: http://127.0.0.1:8000/admin

## Project Structure

```
fastapi-app/
├── app/
│   ├── api/                # API routes
│   │   └── v1/
│   │       ├── endpoints/  # Endpoint modules
│   │       └── api.py      # Main API router
│   ├── core/               # Core functionality
│   │   ├── config.py       # Configuration
│   │   ├── security.py     # Security utilities
│   │   └── middleware.py   # Custom middleware
│   ├── db/                 # Database
│   │   ├── database.py     # Database connection
│   │   └── crud.py         # CRUD operations
│   ├── models/             # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   ├── services/           # Business logic
│   └── utils/              # Utility functions
├── tests/                  # Test suite
├── scripts/                # Development scripts
├── alembic/                # Database migrations
├── requirements.txt        # Python dependencies
├── main.py                 # Application entry point
├── Dockerfile              # Docker configuration
└── docker-compose.yml     # Docker Compose setup
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - Register new user (public)
- `POST /api/v1/auth/login` - OAuth2 login with email/password (form-based)
- `POST /api/v1/auth/login-json` - JSON login with email/password (web-friendly)
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/test-token` - Test token validity

### Users
- `GET /api/v1/users/` - List users (admin only)
- `POST /api/v1/users/` - Create user (admin only)
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update current user
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user (admin only)

### Items
- `GET /api/v1/items/` - List items
- `POST /api/v1/items/` - Create item
- `GET /api/v1/items/{id}` - Get item by ID
- `PUT /api/v1/items/{id}` - Update item
- `DELETE /api/v1/items/{id}` - Delete item

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black .
isort .
```

### Linting

```bash
flake8
mypy .
```

### Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

## Docker Deployment

### Development with Docker

```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Production with Docker

```bash
docker-compose up --build
```

## Configuration

Key configuration options in `.env`:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: JWT secret key
- `ENVIRONMENT`: development/staging/production
- `CORS_ORIGINS`: Allowed CORS origins
- `REDIS_URL`: Redis connection for caching

## Security Features

- JWT authentication with refresh tokens
- Password hashing with bcrypt
- CORS protection
- Rate limiting
- Request/response middleware
- SQL injection protection via SQLAlchemy
- Admin interface with authentication (superuser only)

## Admin Interface

The application includes a web-based admin interface powered by SQLAdmin 0.21.0:

- **URL**: http://127.0.0.1:8000/admin
- **Authentication**: Requires superuser account
- **Features**:
  - User management (view, create, edit, delete)
  - Item management (view, create, edit, delete)
  - Search and filtering capabilities
  - Bulk operations
  - Data export functionality
  - Modern responsive UI

### Admin Access

To access the admin interface:
1. Navigate to http://127.0.0.1:8000/admin
2. Login with superuser credentials:
   - Username: admin@example.com
   - Password: admin123
3. **Change these credentials in production!**

### Troubleshooting Login Issues

If the login doesn't redirect properly:
1. Clear browser cookies and cache
2. Ensure cookies are enabled
3. Try a hard refresh (Ctrl+F5)
4. Check server logs for errors

See `ADMIN_LOGIN_GUIDE.md` for detailed troubleshooting steps.

## Default Admin User

A default superuser is created with:
- Email: admin@example.com
- Password: admin123

**Change these credentials in production!**

## Contributing

1. Follow PEP 8 style guidelines
2. Write tests for new features
3. Update documentation as needed
4. Use type hints
5. Run linting and tests before submitting

## License

This project is licensed under the MIT License.
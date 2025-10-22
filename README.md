# 🚀 HUBBO Backend

Production-ready FastAPI backend with **RBAC** (Role-Based Access Control), **JWT Authentication**, and **Email Integration**. Built as a solid foundation for AI-powered applications.

---

## ✨ Features

### 🔐 Authentication & Security
- **JWT Authentication** - Access & refresh token rotation
- **Argon2 Password Hashing** - Industry-standard security
- **RBAC System** - Role-based access control with granular permissions
- **Email Integration** - Password reset & notifications
- **Rate Limiting** - Brute force protection
- **Security Headers** - CSP, X-Frame-Options, HSTS

### 🤖 AI Ready
- **OpenAI & Anthropic** support
- **LangChain** integration
- **Vector Store** (ChromaDB)
- **Document Processing** - PDF, DOCX support
- **File Upload** system

### 🏗️ Production Ready
- **Docker & Docker Compose** support
- **PostgreSQL** database
- **Health Check** endpoints
- **Comprehensive Logging**
- **Environment Configuration**

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- (Optional) Docker & Docker Compose

### 1. Clone & Setup
```bash
git clone <your-repo-url>
cd backend

# Run setup script
./setup.sh
```

The setup script will:
- Create virtual environment
- Install dependencies
- Create `.env` from template
- Optionally initialize database

### 2. Configure Environment
Edit `.env` file with your settings:
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/hubbo

# Security
SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"

# Email
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-password

# AI (Optional)
OPENAI_API_KEY=sk-your-key-here
```

### 3. Start Development Server
```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

### 4. Access API
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/health

---

## 🔑 Default Credentials

After running database initialization:

| Email | Password | Role | Access Level |
|-------|----------|------|--------------|
| admin@example.com | Admin123! | admin | Full access |
| manager@example.com | Manager123! | manager | User management |
| user@example.com | User123! | user | Basic access |

---

## 🐳 Docker Deployment

### Development
```bash
docker-compose up -d
```

### Production
```bash
# Edit production environment
cp .env.example .env.production
nano .env.production

# Deploy
docker-compose up -d
```

---

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/    # API endpoints
│   ├── core/                # Security, config
│   ├── db/                  # Database setup
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   ├── middleware/          # Custom middleware
│   ├── services/            # Business logic
│   ├── ai/                  # AI integration
│   └── main.py              # FastAPI app
├── tests/                   # Test suite
├── .env.example             # Environment template
├── requirements.txt         # Dependencies
├── setup.sh                 # Setup script
├── Dockerfile               # Docker config
└── docker-compose.yml       # Multi-container setup
```

---

## 🔐 RBAC System

### Permissions
- `view_user` - View user details
- `create_user` - Create users
- `edit_user` - Edit users
- `delete_user` - Delete users
- `manage_roles` - Manage roles
- `manage_permissions` - Manage permissions
- `use_ai` - Use AI features
- `manage_ai` - Manage AI config
- `user:read` - Read files
- `user:write` - Upload files

### Roles
- **admin** - All permissions
- **manager** - User management + AI
- **user** - Basic access + AI
- **guest** - Read-only

### Usage in Code
```python
from app.middleware import require_permission

@router.post("/users/")
def create_user(_: bool = Depends(require_permission("create_user"))):
    # Only users with create_user permission can access
    pass
```

---

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

### Password Management
- `POST /api/v1/password/request-reset` - Request reset
- `POST /api/v1/password/reset-password` - Reset with token
- `POST /api/v1/password/change-password` - Change password

### Users
- `GET /api/v1/users/me` - Current user
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user
- `PATCH /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Roles & Permissions
- `GET /api/v1/roles` - List roles
- `GET /api/v1/permissions` - List permissions

### AI
- `POST /api/v1/ai/chat` - Chat with AI
- `POST /api/v1/ai/documents/upload` - Upload document
- `POST /api/v1/ai/documents/search` - Search documents

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test file
pytest tests/test_auth.py -v
```

---

## 🛠️ Development

### Setup for Development
```bash
./setup.sh
source .venv/bin/activate
uvicorn app.main:app --reload
```

### Database Migrations
```bash
# Initialize database
python -m app.scripts.init_database

# Or use individual scripts
python -m app.scripts.init_db
python -m app.scripts.populate_database
```

---

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available options. Key variables:

```bash
# App
APP_NAME=HUBBO
DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/hubbo

# Security
SECRET_KEY=<generate-secure-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
MAIL_USERNAME=your-email@example.com
MAIL_PASSWORD=your-app-password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# AI
AI_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
AI_MODEL=gpt-3.5-turbo

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

## 📦 Dependencies

### Core
- **FastAPI** - Modern web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **Pydantic** - Data validation

### Security
- **Argon2** - Password hashing
- **python-jose** - JWT tokens
- **passlib** - Password utilities

### AI & ML
- **LangChain** - AI framework
- **OpenAI** - LLM provider
- **ChromaDB** - Vector store
- **tiktoken** - Token counting

### Email
- **fastapi-mail** - Email sending
- **email-validator** - Email validation

---

## 🚀 Production Deployment

### Pre-deployment Checklist
- [ ] Set strong `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configure production database
- [ ] Set up email credentials
- [ ] Configure CORS origins
- [ ] Set up SSL/HTTPS
- [ ] Configure monitoring
- [ ] Set up backups

### Deploy with Docker
```bash
# Production setup
./setup.sh --production

# Start services
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

---

## 📝 License

MIT License - see LICENSE file for details

---

## 🤝 Contributing

This is a boilerplate project. Feel free to customize for your needs.

---

## 📞 Support

- **Documentation:** Check the code comments and docstrings
- **Issues:** Open an issue on your repository
- **API Docs:** http://localhost:8000/docs

---

**Built with ❤️ for HUBBO - Your AI-Powered Application**

# FinFlow 💰

**AI-Powered Personal Finance Management System**

A modern, secure, and intelligent personal finance tracker built with FastAPI, featuring AI-powered transaction categorization, spending insights, and comprehensive financial management tools.

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.105.0-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![AI](https://img.shields.io/badge/AI-OpenAI_GPT--3.5-orange.svg)

## ✨ Features

### 🔐 **Secure Authentication**
- JWT-based authentication with secure session management
- Bcrypt password hashing
- Cookie-based web sessions
- User registration and login system

### 💳 **Account Management**
- Multiple account types (Checking, Savings, Credit Card, Investment, Cash)
- Real-time balance tracking
- Account categorization with visual icons
- Comprehensive account overview

### 💸 **Transaction System**
- Income, expense, and transfer tracking
- Automatic balance calculations
- Transaction categorization and tagging
- Historical transaction management
- Smart filtering and search

### 🤖 **AI-Powered Features**
- **Smart Categorization**: Automatic transaction categorization using GPT-3.5
- **Financial Assistant**: Natural language queries about your finances
- **Spending Insights**: AI-powered analysis of spending patterns
- **Anomaly Detection**: Unusual spending pattern alerts
- **Personalized Recommendations**: Custom financial advice

### 📊 **Analytics & Reporting**
- Interactive spending charts and visualizations
- Monthly and weekly spending trends
- Category-based expense analysis
- Financial health metrics
- Custom date range reporting

### 🎨 **Modern Web Interface**
- Responsive design with Tailwind CSS
- Real-time updates with HTMX
- Interactive components with Alpine.js
- Mobile-friendly interface
- Dark/Light theme support

### 🔒 **Privacy & Security**
- Bank-level security practices
- Data anonymization for AI processing
- User-controlled AI feature settings
- No sensitive data shared with external services
- HTTPS-ready configuration

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.13+ (for local development)
- OpenAI API Key (optional, for AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/adeepivt/finflow.git
   cd finflow
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Generate secure secret key**
   ```bash
   openssl rand -base64 32
   # Copy the output to SECRET_KEY in .env
   ```

4. **Start the application**
   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - Web Interface: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## 📖 Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Application Settings
PROJECT_NAME=FinFlow API
ENVIRONMENT=development
SECRET_KEY=your-secure-secret-key-from-openssl

# Database Configuration
DATABASE_URL=postgresql://finance_user:finance_password_dev@postgres:5432/finance_tracker

# AI Features (Optional)
OPENAI_API_KEY=your-openai-api-key-here
AI_CATEGORIZATION_ENABLED=True
FINANCIAL_ASSISTANT_ENABLED=True

# Security Settings
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### AI Configuration

To enable AI features:
1. Get an OpenAI API key from https://platform.openai.com
2. Add it to your `.env` file
3. Set AI feature flags to `True`

**Note**: AI features work with fallback systems - the app functions fully without OpenAI integration.

## 🏗️ Architecture

### Backend Stack
- **FastAPI**: Modern, fast web framework for building APIs
- **PostgreSQL**: Robust relational database for financial data
- **SQLAlchemy**: ORM with async support
- **Pydantic**: Data validation and settings management
- **JWT**: Secure authentication tokens
- **OpenAI GPT-3.5**: AI-powered financial insights

### Frontend Stack
- **Jinja2**: Server-side template rendering
- **HTMX**: Dynamic interactions without JavaScript
- **Alpine.js**: Minimal framework for reactive components
- **Tailwind CSS**: Utility-first CSS framework
- **Chart.js**: Interactive financial charts

### Infrastructure
- **Docker**: Containerized deployment
- **Docker Compose**: Multi-service orchestration
- **PostgreSQL**: Primary database

## 📁 Project Structure

```
finflow/
├── app/
│   ├── api/v1/           # API endpoints
│   ├── models/           # Database models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   │   └── ai/          # AI-powered services
│   ├── templates/        # Jinja2 templates
│   ├── web/             # Web controllers
│   ├── utils/           # Utility functions
│   └── tests/           # Test suite
├── docker/              # Docker configuration
└── .env                 # Environment variables
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
docker exec -it finflow_api python run_tests.py

# Run specific test categories
docker exec -it finflow_api python -m pytest app/tests/test_auth.py -v
docker exec -it finflow_api python -m pytest app/tests/test_ai_features.py -v
```

### Test Coverage
- User authentication and authorization
- Account management operations
- Transaction processing and validation
- AI feature integration
- API endpoint functionality
- Database operations

## 🚀 Deployment

### Production Deployment

1. **Update environment for production**
   ```env
   ENVIRONMENT=production
   SECRET_KEY=your-production-secret-key
   DATABASE_URL=postgresql://user:password@production-db:5432/finflow
   ```

2. **Use production Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Cloud Deployment Options
- **AWS**: ECS, EC2, or App Runner
- **Google Cloud**: Cloud Run or Compute Engine  
- **Azure**: Container Instances or App Service
- **DigitalOcean**: App Platform or Droplets
- **Railway/Render**: One-click deployment

## 📊 API Documentation

### Authentication Endpoints
- `POST /api/v1/users` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout

### Account Management
- `GET /api/v1/accounts` - List user accounts
- `POST /api/v1/accounts` - Create new account
- `GET /api/v1/accounts/{id}` - Get account details
- `PUT /api/v1/accounts/{id}` - Update account
- `DELETE /api/v1/accounts/{id}` - Delete account

### Transaction Management
- `GET /api/v1/transactions` - List transactions
- `POST /api/v1/transactions` - Create transaction
- `GET /api/v1/transactions/{id}` - Get transaction details
- `PUT /api/v1/transactions/{id}` - Update transaction
- `DELETE /api/v1/transactions/{id}` - Delete transaction
- `GET /api/v1/transactions/summary` - Financial summary

### AI Features
- `POST /api/v1/ai/categorize` - Smart transaction categorization
- `POST /api/v1/ai/ask` - Financial assistant queries
- `GET /api/v1/ai/insights` - Spending insights and recommendations
- `GET /api/v1/ai/security-info` - AI privacy information

## 🔧 Development

### Local Development Setup

1. **Clone and setup**
   ```bash
   git clone https://github.com/adeepivt/finflow.git
   cd finflow
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run locally**
   ```bash
   uvicorn app.main:app --reload
   ```

### Adding New Features

1. **Create feature branch**
   ```bash
   git checkout -b feature/new-feature
   ```

2. **Add database models** in `app/models/`
3. **Create Pydantic schemas** in `app/schemas/`
4. **Implement business logic** in `app/services/`
5. **Add API endpoints** in `app/api/v1/`
6. **Create web templates** in `app/templates/`
7. **Write tests** in `app/tests/`

### Development Guidelines
- Follow PEP 8 style guidelines
- Write comprehensive tests for new features
- Update documentation for API changes
- Use type hints throughout the codebase
- Follow conventional commit messages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FastAPI** for the amazing web framework
- **OpenAI** for GPT-3.5 integration
- **Tailwind CSS** for the design system
- **HTMX** for seamless interactions
- **PostgreSQL** for reliable data storage

## 🎯 Roadmap

### Current Version (v1.0)
- ✅ Core financial tracking
- ✅ AI-powered categorization
- ✅ Web interface
- ✅ Comprehensive API

### Upcoming Features (v1.1)
- [ ] Mobile app (React Native)
- [ ] Bank account integration (Plaid)
- [ ] Investment portfolio tracking
- [ ] Bill payment reminders
- [ ] Financial goal setting

### Future Enhancements (v2.0)
- [ ] Multi-currency support
- [ ] Advanced AI financial coaching
- [ ] Receipt scanning (OCR)
- [ ] Tax report generation
- [ ] Multi-user/family accounts

---

**Built with ❤️ by ADEEP**

*FinFlow - Making personal finance management intelligent and effortless.*
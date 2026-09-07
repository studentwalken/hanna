# Professional SMS Gateway System

A complete, production-ready SMS gateway system that allows you to send and receive messages from multiple Android phones through a web interface and API. Built with FastAPI (Python) backend and React frontend.

## Features

### Core Functionality
- **Multi-device Support**: Connect multiple Android phones and manage them from one dashboard
- **Two-way Messaging**: Send and receive SMS messages
- **Single & Bulk Mode**: Send individual messages or bulk SMS via CSV/Excel upload
- **Flexible Sender Names**: Set different sender names per message
- **SIM Selection**: Choose which SIM slot to use for dual-SIM devices

### User Management (SaaS-style)
- **Role-based Access**: Super Admin, Admin, and User roles
- **Phone Assignment**: Admins can assign specific phones to users
- **Rate Limiting**: Set custom rate limits per user/API key
- **Permission Control**: Granular send/receive permissions

### API Gateway
- **RESTful API**: Full-featured API for external applications
- **API Key Management**: Create, activate/deactivate, and delete API keys
- **Rate Limiting**: Per-key rate limiting
- **Webhook Support**: Get notified on message events

### Dashboard & Analytics
- **Real-time Stats**: Total phones, sent/delivered/failed messages
- **Charts & Graphs**: Visual representation of message activity
- **Recent Activity**: Live feed of system events
- **Connected Devices**: Monitor phone status and last seen time

### Settings & Integrations
- **Delay Configuration**: Control sending speed to avoid carrier limits
- **Working Hours**: Schedule messages during business hours only
- **Telegram Bot**: Get notifications and reports via Telegram
- **Backup & Restore**: Export/import your data

### Security
- **JWT Authentication**: Secure token-based auth
- **Password Hashing**: Bcrypt for password storage
- **CORS Protection**: Configurable cross-origin policies
- **API Key Permissions**: Fine-grained access control

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL/SQLite** - Database support
- **Pydantic** - Data validation
- **Passlib** - Password hashing
- **Python-Jose** - JWT tokens

### Frontend
- **React 18** - UI library
- **React Router** - Navigation
- **TailwindCSS** - Styling
- **Recharts** - Charts and graphs
- **React Hook Form** - Form handling
- **Axios** - HTTP client
- **React Hot Toast** - Notifications

## Installation

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
# DATABASE_URL=sqlite:///./sms_gateway.db
# SECRET_KEY=your-secret-key-here

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure API URL in vite.config.js if needed
# Update target in server proxy to your backend URL

# Start development server
npm run dev
```

## Android App Integration

To connect your Android phone:

1. Install the SMS Gateway Android app from the repository
2. Open the app and grant necessary permissions
3. Enter your backend server URL
4. Login with your credentials
5. The app will register as a device in your dashboard

The Android app will:
- Listen for incoming SMS and forward to backend
- Receive commands from backend to send SMS
- Report device status and SIM information

## API Usage

### Authentication

```bash
# Register
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}

# Login
POST /api/v1/auth/login
{
  "email": "user@example.com",
  "password": "securepassword"
}

# Response includes access_token for subsequent requests
```

### Send Single Message

```bash
POST /api/v1/messages/send
Authorization: Bearer YOUR_TOKEN

{
  "sender_name": "MyBusiness",
  "phone_numbers": ["+1234567890"],
  "content": "Hello from SMS Gateway!",
  "device_id": 1,
  "sim_slot": 1
}
```

### Send Bulk Messages

```bash
POST /api/v1/messages/bulk
Authorization: Bearer YOUR_TOKEN

{
  "sender_name": "MyBusiness",
  "device_id": 1,
  "messages": [
    {"phone": "+1234567890", "content": "Hello John"},
    {"phone": "+0987654321", "content": "Hello Jane"}
  ]
}
```

### External API (for other apps)

```bash
POST /api/v1/external/send
Authorization: Bearer YOUR_API_KEY

{
  "sender_name": "MyApp",
  "recipient_number": "+1234567890",
  "message_content": "Hello from external app!",
  "sim_slot": 1
}
```

### Get Inbox

```bash
GET /api/v1/inbox?page=1&page_size=20
Authorization: Bearer YOUR_TOKEN
```

### Create API Key

```bash
POST /api/v1/api-keys
Authorization: Bearer YOUR_TOKEN

{
  "name": "My Application",
  "rate_limit": 100
}
```

## Project Structure

```
sms_gateway_system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── main.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
└── README.md
```

## Environment Variables

### Backend (.env)
```
DATABASE_URL=sqlite:///./sms_gateway.db
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=True
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]
```

## Deployment

### Production Backend
```bash
# Use PostgreSQL instead of SQLite
# Set DEBUG=False
# Use a proper SECRET_KEY
# Run with gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Production Frontend
```bash
npm run build
# Deploy dist/ folder to nginx, Apache, or CDN
```

## License

MIT License - Feel free to use for personal or commercial projects.

---

Built with ❤️ using FastAPI and React

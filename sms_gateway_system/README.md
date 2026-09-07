# SMS Gateway System - Professional Multi-Device SMS Platform

## Overview

A comprehensive, production-ready SMS gateway system inspired by the android-sms-gateway project. This system transforms Android phones into powerful SMS gateways with full API control, multi-device support, and SaaS-like capabilities.

## Key Features

### 🎯 Core Capabilities
- **Multi-Device Gateway**: Connect multiple Android phones to a single platform
- **API-First Design**: RESTful API for external applications to send/receive SMS
- **Two-Way Communication**: Full support for sending and receiving SMS/MMS
- **Cloud & Local Deployment**: Flexible deployment options

### 📤 Message Sending
- **Single Mode**: Send individual messages with custom sender names
- **Bulk Mode**: CSV/XLSX file upload for mass messaging
- **SIM Selection**: Choose specific SIM cards on multi-SIM devices
- **Phone Selection**: Route messages through specific connected devices
- **Flexible Sender Names**: Per-message sender identification

### 👥 User Management (SaaS Model)
- **Role-Based Access**: Super Admin → Admin → Regular Users
- **User Limits**: Rate limiting per user
- **Phone Assignment**: Admin assigns specific phones to users
- **API Key Management**: Generate and manage API keys per user

### 📊 Dashboard & Analytics
- Total connected phones
- Messages sent/delivered/failed/queued
- Received messages (inbox) count
- Recent activity logs
- Interactive charts for message trends
- User statistics

### 🔌 External API Integration
- **RESTful Endpoints**: Clean, documented API
- **API Key Authentication**: Secure token-based access
- **Webhook Support**: Real-time notifications for message events
- **Multi-Tenant Ready**: Isolated data per user/organization

### ⚙️ Settings & Customization
- **Delay Configuration**: Customizable sending delays
- **Sending Methods**: Multiple delivery strategies
- **Backup System**: Data export/import functionality
- **Telegram Bot Integration**: Status reports and remote control
- **Rate Limiting**: Per-user message rate controls

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React/Vue)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Dashboard│ │Send SMS  │ │  Inbox   │ │ History  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Users   │ │API Keys  │ │ Settings │ │  Docs    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Backend (FastAPI + PostgreSQL)               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                  API Layer                            │   │
│  │  /api/v1/messages  /api/v1/inbox  /api/v1/devices    │   │
│  │  /api/v1/users     /api/v1/api-keys /api/v1/webhooks │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │               Services Layer                          │   │
│  │  MessageService | UserService | DeviceService        │   │
│  │  WebhookService | AnalyticsService                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Database (PostgreSQL)                    │   │
│  │  Users | Devices | Messages | APIKeys | Webhooks     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Android Bridge Service (WebSocket/SSE)          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Phone 1    │  │   Phone 2    │  │   Phone N    │      │
│  │  (SMS App)   │  │  (SMS App)   │  │  (SMS App)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Pages Structure

### Public Pages (No Navigation Bar)
1. **Login Page** (`/login`) - User authentication
2. **Signup Page** (`/signup`) - First-time super admin creation

### Protected Pages (With Navigation Bar)
1. **Dashboard** (`/dashboard`) - Overview, stats, charts, recent activity
2. **Send SMS** (`/send`) - Single/Bulk mode, SIM/phone selection, sender name
3. **Inbox** (`/inbox`) - All received messages from all devices
4. **History** (`/history`) - Outgoing messages history with filters
5. **Users** (`/users`) - User management (Admin only)
6. **API Keys** (`/api-keys`) - Create/manage API keys
7. **API Docs** (`/docs`) - Swagger/OpenAPI documentation
8. **Settings** (`/settings`) - Delay, methods, backups, Telegram, limits
9. **Devices** (`/devices`) - Connected phone management

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy (Async)
- **Migrations**: Alembic
- **Authentication**: JWT (PyJWT)
- **Validation**: Pydantic
- **Task Queue**: Celery + Redis (for bulk operations)
- **Real-time**: WebSocket/SSE for device communication

### Frontend
- **Framework**: React.js or Vue.js
- **UI Library**: Tailwind CSS + Headless UI
- **State Management**: Redux Toolkit / Pinia
- **HTTP Client**: Axios
- **Charts**: Chart.js / Recharts
- **File Upload**: React Dropzone

### Android Bridge
- **Communication**: WebSocket / Server-Sent Events
- **Protocol**: JSON over WSS
- **Fallback**: Long-polling for unstable connections

## API Endpoints Overview

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/signup` - Super admin registration
- `POST /api/v1/auth/refresh` - Refresh token
- `POST /api/v1/auth/logout` - Logout

### Messages
- `POST /api/v1/messages/send` - Send single message
- `POST /api/v1/messages/bulk` - Bulk send (CSV/XLSX)
- `GET /api/v1/messages/history` - Get sent messages
- `GET /api/v1/messages/{id}` - Get message details
- `DELETE /api/v1/messages/{id}/cancel` - Cancel pending message

### Inbox
- `GET /api/v1/inbox` - List received messages
- `GET /api/v1/inbox/{id}` - Get specific message
- `PUT /api/v1/inbox/{id}/read` - Mark as read
- `DELETE /api/v1/inbox/{id}` - Delete message

### Devices
- `GET /api/v1/devices` - List connected phones
- `GET /api/v1/devices/{id}` - Device details
- `PUT /api/v1/devices/{id}` - Update device settings
- `DELETE /api/v1/devices/{id}` - Remove device

### Users (Admin)
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `PUT /api/v1/users/{id}/phones` - Assign phones to user

### API Keys
- `GET /api/v1/api-keys` - List API keys
- `POST /api/v1/api-keys` - Create API key
- `DELETE /api/v1/api-keys/{id}` - Revoke key

### Settings
- `GET /api/v1/settings` - Get system settings
- `PUT /api/v1/settings` - Update settings
- `POST /api/v1/settings/backup` - Create backup
- `POST /api/v1/settings/restore` - Restore from backup

### Webhooks
- `GET /api/v1/webhooks` - List webhooks
- `POST /api/v1/webhooks` - Create webhook
- `DELETE /api/v1/webhooks/{id}` - Delete webhook

## Getting Started

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Node.js 18+ (for frontend)
- Redis (optional, for task queue)
- Android devices with SMS Gateway app installed

### Installation

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### Android App
1. Install the SMS Gateway app on Android devices
2. Configure device to connect to your backend URL
3. Grant necessary permissions (SEND_SMS, READ_SMS, etc.)

## Configuration

Environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/sms_gateway

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (optional)
REDIS_URL=redis://localhost:6379

# Telegram Bot (optional)
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_EXTENSIONS=csv,xlsx

# Rate Limiting
DEFAULT_RATE_LIMIT=100  # messages per hour
```

## License

Apache 2.0

## Support

For issues and feature requests, please open an issue on GitHub.

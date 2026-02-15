# OpenClaw Email Agent - Product Requirements Document

## Overview

A Python-based email agent that integrates with OpenClaw Gateway, enabling AI-powered email management through Gmail using IMAP (reading) and SMTP (sending).

---

## Goals & Objectives

1. **Connect to Gmail** via IMAP/SMTP with secure credential management
2. **Read emails** - Fetch, parse, and process incoming messages
3. **Send emails** - Compose and send messages programmatically
4. **Manage emails** - Mark as read/unread, archive, delete, move to folders
5. **Integrate with OpenClaw** - Expose functionality to the OpenClaw Gateway

---

## Decisions (Finalized)

### 1. AI Integration
- [x] **Basic AI** - Summarization and classification
- [x] Summarize incoming emails via OpenClaw Gateway LLM
- [x] Classify emails by type: Work, Personal, Newsletters, Spam, Notifications
- [ ] ~~Draft/suggest replies~~ (Future phase)
- [ ] ~~Auto-respond~~ (Future phase)

### 2. Running Mode
- [x] **Continuous service** - Poll for new emails every **15 minutes**
- [x] **Webhook callbacks** - POST to OpenClaw when new emails arrive
- [x] **REST API** - OpenClaw can also query on-demand

### 3. Account Support
- [x] **Multiple Gmail accounts** - Design for multi-account from the start

### 4. OpenClaw Integration Method
- [x] **REST API** using **FastAPI** framework
- [x] **Webhook notifications** to OpenClaw Gateway for new emails
- [x] LLM calls routed through OpenClaw Gateway

### 5. Additional Decisions
- [x] **Email threading** - Full conversation tracking and grouping
- [ ] ~~Attachments~~ - Skipped for Phase 1
- [x] **Notifications** - Both webhook (push) + REST (pull)

---

## Functional Requirements

### FR-1: Email Reading
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | Connect to Gmail via IMAP SSL | Must Have |
| FR-1.2 | Authenticate using App Password | Must Have |
| FR-1.3 | List available mailboxes/folders | Should Have |
| FR-1.4 | Fetch emails from inbox | Must Have |
| FR-1.5 | Parse email headers (from, to, subject, date) | Must Have |
| FR-1.6 | Parse email body (plain text and HTML) | Must Have |
| FR-1.7 | Handle attachments | Phase 2 |
| FR-1.8 | Search emails by criteria (sender, subject, date) | Should Have |
| FR-1.9 | Group emails by thread/conversation | Must Have |
| FR-1.10 | Support multiple Gmail accounts | Must Have |

### FR-2: Email Sending
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | Connect to Gmail via SMTP SSL | Must Have |
| FR-2.2 | Send plain text emails | Must Have |
| FR-2.3 | Send HTML emails | Should Have |
| FR-2.4 | Support CC and BCC recipients | Should Have |
| FR-2.5 | Add attachments | Could Have |
| FR-2.6 | Reply to existing email threads | Should Have |

### FR-3: Email Management
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | Mark emails as read/unread | Must Have |
| FR-3.2 | Move emails to folders (Archive, Trash) | Should Have |
| FR-3.3 | Delete emails | Should Have |
| FR-3.4 | Flag/star emails | Could Have |

### FR-4: OpenClaw Integration
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | FastAPI REST endpoints for all email operations | Must Have |
| FR-4.2 | Return structured JSON responses for LLM processing | Must Have |
| FR-4.3 | Support async operations | Must Have |
| FR-4.4 | Webhook POST to OpenClaw on new email arrival | Must Have |
| FR-4.5 | Route LLM calls through OpenClaw Gateway | Must Have |
| FR-4.6 | Auto-generated OpenAPI documentation | Should Have |

### FR-5: AI Features
| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | Summarize email content via OpenClaw LLM | Must Have |
| FR-5.2 | Classify emails (Work, Personal, Newsletters, Spam, Notifications) | Must Have |
| FR-5.3 | Store classification with email metadata | Should Have |

---

## Non-Functional Requirements

### NFR-1: Security
- Credentials stored in environment variables (never hardcoded)
- Support for Gmail App Passwords (2FA compatible)
- Secure SSL/TLS connections only
- No credential logging

### NFR-2: Reliability
- Graceful error handling with meaningful messages
- Automatic reconnection on connection drops
- Logging for debugging and monitoring

### NFR-3: Maintainability
- Modular, class-based architecture
- Clear separation of concerns
- Type hints for better IDE support
- Documented public methods

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      OpenClaw Gateway                            │
│                    (DigitalOcean Droplet)                        │
│  ┌─────────────────┐    ┌─────────────────┐                     │
│  │   Agent Runtime │◄───│   LLM Provider  │                     │
│  └────────┬────────┘    └─────────────────┘                     │
│           │                      ▲                               │
│           │ REST calls           │ LLM requests                  │
│           ▼                      │                               │
└───────────┼──────────────────────┼──────────────────────────────┘
            │                      │
            │ HTTP                 │ HTTP
            ▼                      │
┌───────────────────────────────────────────────────────────────────┐
│                    Email Agent (Python + FastAPI)                  │
├───────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI REST Server                        │ │
│  │  POST /emails/send         GET  /emails                      │ │
│  │  GET  /emails/{id}         GET  /emails/threads              │ │
│  │  POST /emails/{id}/read    GET  /accounts                    │ │
│  │  POST /emails/{id}/archive POST /emails/{id}/classify        │ │
│  └──────────────────────────────────────────────────────────────┘ │
├───────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌────────────────────────────┐│
│  │   Config    │  │   Logger    │  │   OpenClaw Client          ││
│  │  (.env)     │  │             │  │  - webhook_notify()        ││
│  │             │  │             │  │  - llm_request()           ││
│  └─────────────┘  └─────────────┘  └────────────────────────────┘│
├───────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │                   Background Scheduler                       │ │
│  │              (Poll every 15 minutes)                         │ │
│  └─────────────────────────────────────────────────────────────┘ │
├───────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐         ┌────────────────────┐          │
│  │  AccountManager    │         │   AIProcessor      │          │
│  │  - accounts[]      │         │  - summarize()     │          │
│  │  - add_account()   │         │  - classify()      │          │
│  │  - remove_account()│         │                    │          │
│  └────────────────────┘         └────────────────────┘          │
├───────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐    ┌─────────────────────────┐          │
│  │   IMAPClient       │    │      SMTPClient         │          │
│  │  - connect()       │    │  - connect()            │          │
│  │  - fetch_emails()  │    │  - send()               │          │
│  │  - search()        │    │  - reply()              │          │
│  │  - get_threads()   │    │                         │          │
│  │  - mark_read()     │    │                         │          │
│  │  - archive()       │    │                         │          │
│  └────────────────────┘    └─────────────────────────┘          │
└───────────────────────────────────────────────────────────────────┘
            │                               │
            ▼                               ▼
   ┌─────────────────┐             ┌─────────────────┐
   │   IMAP Server   │             │   SMTP Server   │
   │   (Gmail x N)   │             │   (Gmail x N)   │
   └─────────────────┘             └─────────────────┘
```

---

## Project Structure

```
openclaw-email-agent/
├── prd.md                   # This document
├── requirements.txt         # Python dependencies
├── .env.example             # Example environment variables
├── .env                     # Actual credentials (gitignored)
├── .gitignore
├── src/
│   ├── __init__.py
│   ├── config.py            # Configuration loading
│   ├── models.py            # Pydantic models (Email, Thread, Account)
│   ├── imap_client.py       # IMAP operations
│   ├── smtp_client.py       # SMTP operations
│   ├── account_manager.py   # Multi-account management
│   ├── thread_manager.py    # Email threading/conversation logic
│   ├── ai_processor.py      # Summarization & classification via OpenClaw
│   ├── openclaw_client.py   # OpenClaw Gateway integration (webhooks, LLM)
│   ├── scheduler.py         # Background polling scheduler
│   └── api/
│       ├── __init__.py
│       ├── main.py          # FastAPI app setup
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── emails.py    # Email CRUD endpoints
│       │   ├── accounts.py  # Account management endpoints
│       │   └── health.py    # Health check endpoint
│       └── dependencies.py  # FastAPI dependencies
├── main.py                  # Entry point (starts FastAPI + scheduler)
└── tests/
    ├── __init__.py
    ├── test_imap_client.py
    ├── test_smtp_client.py
    ├── test_api.py
    └── conftest.py          # Pytest fixtures
```

---

## Implementation Phases

### Phase 1: Foundation
- [ ] Project setup (requirements.txt, .env, config.py)
- [ ] Pydantic models (Email, Thread, Account, Classification)
- [ ] IMAPClient with connection pooling
- [ ] SMTPClient for sending
- [ ] AccountManager for multi-account support
- [ ] Basic email operations (fetch, send, mark read, archive)

### Phase 2: Threading & API
- [ ] ThreadManager for conversation grouping
- [ ] FastAPI REST endpoints
- [ ] OpenAPI documentation
- [ ] Background scheduler (15-min polling)

### Phase 3: OpenClaw Integration
- [ ] OpenClawClient for Gateway communication
- [ ] Webhook notifications on new emails
- [ ] LLM routing through Gateway

### Phase 4: AI Features
- [ ] AIProcessor class
- [ ] Email summarization via OpenClaw LLM
- [ ] Type-based classification (Work, Personal, Newsletters, Spam, Notifications)

### Phase 5: Polish & Deploy
- [ ] Error handling and logging
- [ ] Unit tests
- [ ] Docker containerization (optional)
- [ ] Deployment documentation

---

## API Endpoints

### Accounts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/accounts` | List all configured accounts |
| POST | `/accounts` | Add a new Gmail account |
| DELETE | `/accounts/{id}` | Remove an account |

### Emails
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/emails` | List emails (with filters: account, folder, unread) |
| GET | `/emails/{id}` | Get single email with full body |
| POST | `/emails` | Send a new email |
| POST | `/emails/{id}/reply` | Reply to an email |
| POST | `/emails/{id}/read` | Mark email as read |
| POST | `/emails/{id}/unread` | Mark email as unread |
| POST | `/emails/{id}/archive` | Archive email |
| DELETE | `/emails/{id}` | Delete email |

### Threads
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/threads` | List email threads/conversations |
| GET | `/threads/{id}` | Get thread with all emails |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/emails/{id}/summarize` | Get AI summary of email |
| POST | `/emails/{id}/classify` | Classify email by type |
| GET | `/emails/{id}/classification` | Get stored classification |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | OpenAPI documentation (auto-generated) |

---

## Webhook Payload

When new emails arrive, POST to OpenClaw Gateway:

```json
{
  "event": "new_email",
  "timestamp": "2026-02-14T12:00:00Z",
  "account": "user@gmail.com",
  "emails": [
    {
      "id": "abc123",
      "thread_id": "thread456",
      "from": "sender@example.com",
      "subject": "Meeting tomorrow",
      "snippet": "Hi, just wanted to confirm...",
      "classification": "Work",
      "received_at": "2026-02-14T11:58:00Z"
    }
  ]
}
```

---

## Prerequisites Checklist

- [ ] Gmail account(s) with IMAP enabled
- [ ] Gmail App Password(s) generated (for 2FA accounts)
- [ ] Python 3.10+ installed
- [ ] OpenClaw Gateway accessible (URL and webhook endpoint)

---

## Configuration

### Environment Variables

```bash
# Server
API_HOST=0.0.0.0
API_PORT=8000

# OpenClaw Gateway
OPENCLAW_GATEWAY_URL=http://your-droplet-ip:port
OPENCLAW_WEBHOOK_ENDPOINT=/webhooks/email
OPENCLAW_API_KEY=your-api-key

# Gmail Accounts (JSON array)
GMAIL_ACCOUNTS='[
  {"email": "account1@gmail.com", "app_password": "xxxx"},
  {"email": "account2@gmail.com", "app_password": "yyyy"}
]'

# Polling
POLL_INTERVAL_MINUTES=15

# Classification Categories
EMAIL_CATEGORIES=Work,Personal,Newsletters,Spam,Notifications
```

---

## Notes

- **Threading**: Uses Gmail's `X-GM-THRID` header for native thread grouping
- **Rate Limits**: Gmail IMAP has limits; polling every 15 min is safe
- **Security**: Never log credentials; use environment variables only

---

## Deployment

### Local Development

```bash
# Clone and setup
cd openclaw-email-agent
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your credentials

# Run
python main.py

# API docs available at http://localhost:8000/docs
```

### Running Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_ai_processor.py -v
```

### Docker Deployment

```bash
# Build and run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f email-agent

# Stop
docker-compose down
```

### Production Deployment (DigitalOcean)

1. **Create Droplet** (Ubuntu 22.04, 1GB RAM minimum)

2. **Install Docker**:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

3. **Clone and Configure**:
```bash
git clone <your-repo> /opt/openclaw-email-agent
cd /opt/openclaw-email-agent
cp .env.example .env
nano .env  # Configure your settings
```

4. **Run with Docker**:
```bash
docker-compose up -d
```

5. **Setup Systemd Service** (optional):
```bash
# /etc/systemd/system/openclaw-email-agent.service
[Unit]
Description=OpenClaw Email Agent
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/openclaw-email-agent
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down

[Install]
WantedBy=multi-user.target
```

6. **Enable and Start**:
```bash
sudo systemctl enable openclaw-email-agent
sudo systemctl start openclaw-email-agent
```

### Connecting to OpenClaw Gateway

1. Configure webhook endpoint in OpenClaw Gateway to receive notifications
2. Set `OPENCLAW_GATEWAY_URL` to your Gateway's address
3. Set `OPENCLAW_WEBHOOK_ENDPOINT` (default: `/webhooks/email`)
4. Set `OPENCLAW_API_KEY` for authentication

The Email Agent will:
- Poll for new emails every 15 minutes
- Classify emails automatically
- POST to Gateway webhook when new emails arrive
- Respond to Gateway REST API calls for email operations


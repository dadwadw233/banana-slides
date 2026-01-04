# Super Banana Slides - API Design

## Overview

RESTful API design for Super Banana Slides commercial version.

**Base URL**: `https://api.super-banana-slides.com/v1`  
**Authentication**: JWT Bearer Token  
**Content-Type**: `application/json`

---

## Authentication

### Register
```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "username": "johndoe"
}

Response 201:
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "quota_balance": 3
  },
  "message": "Registration successful. Please verify your email."
}
```

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}

Response 200:
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "expires_in": 3600,
    "user": {
      "user_id": "uuid",
      "email": "user@example.com",
      "username": "johndoe",
      "quota_balance": 50
    }
  }
}
```

### OAuth Login
```http
POST /auth/oauth/{provider}
Content-Type: application/json

{
  "code": "oauth_code_from_provider"
}

Providers: google, wechat, github
```

---

## User Management

### Get Current User
```http
GET /users/me
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "username": "johndoe",
    "quota_balance": 50,
    "role": "premium",
    "created_at": "2026-01-04T12:00:00Z"
  }
}
```

### Update Profile
```http
PATCH /users/me
Authorization: Bearer {token}
Content-Type: application/json

{
  "username": "newusername",
  "avatar_url": "https://..."
}
```

---

## Quota Management

### Get Quota Balance
```http
GET /quota/balance
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "balance": 50,
    "last_updated": "2026-01-04T12:00:00Z"
  }
}
```

### Get Quota History
```http
GET /quota/transactions?page=1&limit=20
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "transactions": [
      {
        "id": "uuid",
        "amount": -1,
        "type": "consume",
        "description": "Generate image for page",
        "balance_after": 49,
        "created_at": "2026-01-04T12:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100
    }
  }
}
```

---

## Payment & Orders

### Create Order
```http
POST /orders
Authorization: Bearer {token}
Content-Type: application/json

{
  "quota_amount": 50,
  "payment_method": "alipay"
}

Response 201:
{
  "success": true,
  "data": {
    "order_id": "uuid",
    "order_number": "ORD20260104001",
    "amount": 100.00,
    "quota_amount": 50,
    "payment_url": "https://payment.provider.com/...",
    "expires_at": "2026-01-04T13:00:00Z"
  }
}
```

### Get Order Status
```http
GET /orders/{order_id}
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "order_id": "uuid",
    "status": "paid",
    "amount": 100.00,
    "quota_amount": 50,
    "paid_at": "2026-01-04T12:30:00Z"
  }
}
```

---

## Projects

### Create Project
```http
POST /projects
Authorization: Bearer {token}
Content-Type: application/json

{
  "title": "My Presentation",
  "creation_type": "idea",
  "idea_prompt": "A presentation about AI",
  "template_id": "uuid",
  "extra_requirements": "Use blue color scheme"
}

Response 201:
{
  "success": true,
  "data": {
    "project_id": "uuid",
    "title": "My Presentation",
    "status": "draft",
    "created_at": "2026-01-04T12:00:00Z"
  }
}
```

### List Projects
```http
GET /projects?page=1&limit=20&status=completed
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "projects": [
      {
        "project_id": "uuid",
        "title": "My Presentation",
        "status": "completed",
        "page_count": 10,
        "created_at": "2026-01-04T12:00:00Z",
        "updated_at": "2026-01-04T13:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 5
    }
  }
}
```

### Get Project Details
```http
GET /projects/{project_id}
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "project_id": "uuid",
    "title": "My Presentation",
    "description": "...",
    "status": "completed",
    "pages": [
      {
        "page_id": "uuid",
        "order_index": 0,
        "title": "Introduction",
        "image_url": "https://...",
        "thumbnail_url": "https://..."
      }
    ],
    "created_at": "2026-01-04T12:00:00Z"
  }
}
```

### Delete Project
```http
DELETE /projects/{project_id}
Authorization: Bearer {token}

Response 204: No Content
```

---

## PPT Generation

### Generate Outline
```http
POST /projects/{project_id}/generate/outline
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "outline": [
      {
        "title": "Introduction",
        "points": ["Point 1", "Point 2"]
      }
    ]
  }
}
```

### Generate Descriptions
```http
POST /projects/{project_id}/generate/descriptions
Authorization: Bearer {token}

Response 202:
{
  "success": true,
  "data": {
    "task_id": "uuid",
    "status": "running",
    "message": "Generating descriptions..."
  }
}
```

### Generate Images
```http
POST /projects/{project_id}/generate/images
Authorization: Bearer {token}
Content-Type: application/json

{
  "page_ids": ["uuid1", "uuid2"]
}

Response 202:
{
  "success": true,
  "data": {
    "task_id": "uuid",
    "status": "running",
    "progress": 0,
    "total": 2
  }
}
```

### Get Task Status
```http
GET /tasks/{task_id}
Authorization: Bearer {token}

Response 200:
{
  "success": true,
  "data": {
    "task_id": "uuid",
    "status": "completed",
    "progress": 100,
    "completed_items": 2,
    "total_items": 2,
    "result": {
      "generated_pages": ["uuid1", "uuid2"]
    }
  }
}
```

---

## Export

### Export PPTX
```http
POST /projects/{project_id}/export/pptx
Authorization: Bearer {token}
Content-Type: application/json

{
  "page_ids": ["uuid1", "uuid2"]
}

Response 200:
{
  "success": true,
  "data": {
    "download_url": "https://cdn.../export.pptx",
    "expires_at": "2026-01-04T14:00:00Z"
  }
}
```

### Export Editable PPTX
```http
POST /projects/{project_id}/export/editable-pptx
Authorization: Bearer {token}

Response 202:
{
  "success": true,
  "data": {
    "task_id": "uuid",
    "status": "running"
  }
}
```

---

## Templates

### List Templates
```http
GET /templates?category=business&is_premium=false&page=1&limit=20

Response 200:
{
  "success": true,
  "data": {
    "templates": [
      {
        "template_id": "uuid",
        "name": "Modern Business",
        "preview_url": "https://...",
        "category": "business",
        "is_premium": false,
        "rating": 4.5,
        "download_count": 1000
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100
    }
  }
}
```

---

## Error Responses

### Standard Error Format
```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_QUOTA",
    "message": "Insufficient quota balance",
    "details": {
      "required": 1,
      "available": 0
    }
  }
}
```

### Common Error Codes
- `UNAUTHORIZED`: Invalid or missing authentication token
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid request data
- `INSUFFICIENT_QUOTA`: Not enough quota balance
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_ERROR`: Server error

---

## Rate Limiting

- **Free Users**: 100 requests/hour
- **Premium Users**: 1000 requests/hour
- **API Key**: Configurable per key

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704369600
```

---

## Webhooks

### Configure Webhook
```http
POST /webhooks
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["project.completed", "payment.succeeded"],
  "secret": "your-secret-key"
}
```

### Webhook Events
- `project.completed`: Project generation completed
- `payment.succeeded`: Payment successful
- `payment.failed`: Payment failed
- `quota.low`: Quota balance below threshold

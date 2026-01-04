# Super Banana Slides - Database Schema Design

## Overview

This document defines the complete database schema for Super Banana Slides commercial version.

**Database**: PostgreSQL 15+  
**ORM**: SQLAlchemy 2.0+

---

## Core Tables

### 1. Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    username VARCHAR(100),
    full_name VARCHAR(200),
    avatar_url TEXT,
    phone VARCHAR(20),
    
    -- Quota
    quota_balance INTEGER DEFAULT 0,
    
    -- Role & Status
    role VARCHAR(20) DEFAULT 'user', -- 'user', 'premium', 'admin'
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'suspended', 'deleted'
    is_verified BOOLEAN DEFAULT FALSE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    is_phone_verified BOOLEAN DEFAULT FALSE,
    
    -- OAuth
    oauth_provider VARCHAR(50), -- 'google', 'wechat', 'github'
    oauth_id VARCHAR(255),
    
    -- Metadata
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    
    -- Indexes
    CONSTRAINT users_email_key UNIQUE (email),
    CONSTRAINT users_oauth_key UNIQUE (oauth_provider, oauth_id)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_oauth ON users(oauth_provider, oauth_id);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### 2. Quota Transactions Table

```sql
CREATE TABLE quota_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Transaction Details
    amount INTEGER NOT NULL, -- Positive for purchase/gift, negative for consumption
    balance_after INTEGER NOT NULL,
    type VARCHAR(20) NOT NULL, -- 'purchase', 'consume', 'refund', 'gift', 'expire'
    
    -- Related Entities
    order_id UUID REFERENCES orders(id),
    project_id UUID REFERENCES projects(id),
    
    -- Description
    description TEXT,
    metadata JSONB, -- Additional data (e.g., {"action": "generate_image", "page_id": "xxx"})
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT quota_transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_quota_transactions_user_id ON quota_transactions(user_id);
CREATE INDEX idx_quota_transactions_created_at ON quota_transactions(created_at);
CREATE INDEX idx_quota_transactions_type ON quota_transactions(type);
```

### 3. Orders Table

```sql
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Order Details
    order_number VARCHAR(50) UNIQUE NOT NULL, -- e.g., "ORD20260104001"
    amount DECIMAL(10, 2) NOT NULL, -- Total amount in CNY
    quota_amount INTEGER NOT NULL, -- Number of quotas purchased
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'paid', 'failed', 'refunded', 'cancelled'
    
    -- Payment
    payment_method VARCHAR(50), -- 'alipay', 'wechat', 'stripe', 'paypal'
    payment_id TEXT, -- External payment ID
    payment_data JSONB, -- Payment provider response
    
    -- Subscription (if applicable)
    subscription_type VARCHAR(20), -- 'monthly', 'yearly', null for one-time
    subscription_id UUID REFERENCES subscriptions(id),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    paid_at TIMESTAMP,
    refunded_at TIMESTAMP,
    
    -- Indexes
    CONSTRAINT orders_order_number_key UNIQUE (order_number)
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

### 4. Subscriptions Table

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Subscription Details
    type VARCHAR(20) NOT NULL, -- 'monthly', 'yearly'
    quota_per_period INTEGER NOT NULL, -- e.g., 50 for monthly, 800 for yearly
    price DECIMAL(10, 2) NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'cancelled', 'expired'
    
    -- Billing
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    next_billing_date TIMESTAMP,
    
    -- Auto-renewal
    auto_renew BOOLEAN DEFAULT TRUE,
    
    -- External IDs
    stripe_subscription_id VARCHAR(255),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    cancelled_at TIMESTAMP,
    expired_at TIMESTAMP
);

CREATE INDEX idx_subscriptions_user_id ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
CREATE INDEX idx_subscriptions_next_billing_date ON subscriptions(next_billing_date);
```

---

## Project & Content Tables

### 5. Projects Table

```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Basic Info
    title VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Creation
    creation_type VARCHAR(20), -- 'idea', 'outline', 'description'
    idea_prompt TEXT,
    outline_text TEXT,
    description_text TEXT,
    extra_requirements TEXT,
    
    -- Template & Style
    template_id UUID REFERENCES templates(id),
    template_image_url TEXT,
    style_config JSONB, -- {"color_scheme": "blue", "font": "Arial", ...}
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'generating', 'completed', 'archived'
    
    -- Visibility
    is_public BOOLEAN DEFAULT FALSE,
    is_template BOOLEAN DEFAULT FALSE,
    
    -- Stats
    view_count INTEGER DEFAULT 0,
    like_count INTEGER DEFAULT 0,
    fork_count INTEGER DEFAULT 0,
    
    -- Collaboration
    team_id UUID REFERENCES teams(id),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_is_public ON projects(is_public);
CREATE INDEX idx_projects_created_at ON projects(created_at);
```

### 6. Pages Table

```sql
CREATE TABLE pages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Order
    order_index INTEGER NOT NULL,
    
    -- Content
    title VARCHAR(255),
    part VARCHAR(200), -- Section name
    outline_content JSONB,
    description_content JSONB,
    
    -- Generated Assets
    image_url TEXT,
    thumbnail_url TEXT,
    editable_data JSONB, -- For editable PPTX export
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'generating', 'completed', 'failed'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT pages_project_order_key UNIQUE (project_id, order_index)
);

CREATE INDEX idx_pages_project_id ON pages(project_id);
CREATE INDEX idx_pages_order_index ON pages(project_id, order_index);
```

### 7. Page Versions Table

```sql
CREATE TABLE page_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id UUID NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    
    -- Version
    version_number INTEGER NOT NULL,
    
    -- Content Snapshot
    image_url TEXT,
    description_content JSONB,
    
    -- Metadata
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT page_versions_page_version_key UNIQUE (page_id, version_number)
);

CREATE INDEX idx_page_versions_page_id ON page_versions(page_id);
```

---

## Template & Asset Tables

### 8. Templates Table

```sql
CREATE TABLE templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    preview_url TEXT,
    
    -- Categorization
    category VARCHAR(50), -- 'business', 'education', 'creative', etc.
    tags TEXT[], -- Array of tags
    
    -- Pricing
    is_premium BOOLEAN DEFAULT FALSE,
    price DECIMAL(10, 2) DEFAULT 0,
    
    -- Author
    author_id UUID REFERENCES users(id),
    is_official BOOLEAN DEFAULT FALSE,
    
    -- Stats
    download_count INTEGER DEFAULT 0,
    rating DECIMAL(3, 2) DEFAULT 0, -- 0.00 to 5.00
    review_count INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'published', 'archived'
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_templates_category ON templates(category);
CREATE INDEX idx_templates_is_premium ON templates(is_premium);
CREATE INDEX idx_templates_status ON templates(status);
```

### 9. Materials Table

```sql
CREATE TABLE materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    -- File Info
    filename VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    file_type VARCHAR(50), -- 'image', 'pdf', 'docx', etc.
    file_size INTEGER, -- in bytes
    
    -- Metadata
    is_global BOOLEAN DEFAULT FALSE, -- Global materials vs project-specific
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_materials_user_id ON materials(user_id);
CREATE INDEX idx_materials_project_id ON materials(project_id);
```

---

## Team & Collaboration Tables

### 10. Teams Table

```sql
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Basic Info
    name VARCHAR(255) NOT NULL,
    description TEXT,
    avatar_url TEXT,
    
    -- Owner
    owner_id UUID NOT NULL REFERENCES users(id),
    
    -- Quota
    quota_pool INTEGER DEFAULT 0,
    
    -- Status
    status VARCHAR(20) DEFAULT 'active',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_teams_owner_id ON teams(owner_id);
```

### 11. Team Members Table

```sql
CREATE TABLE team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    team_id UUID NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Role
    role VARCHAR(20) DEFAULT 'member', -- 'owner', 'admin', 'member', 'viewer'
    
    -- Timestamps
    joined_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT team_members_team_user_key UNIQUE (team_id, user_id)
);

CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);
```

---

## System Tables

### 12. Tasks Table

```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    
    -- Task Info
    task_type VARCHAR(50) NOT NULL, -- 'generate_outline', 'generate_descriptions', 'generate_images'
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    
    -- Progress
    progress INTEGER DEFAULT 0, -- 0-100
    total_items INTEGER,
    completed_items INTEGER DEFAULT 0,
    
    -- Result
    result JSONB,
    error_message TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_tasks_user_id ON tasks(user_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
```

### 13. API Keys Table

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Key Info
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(20) NOT NULL, -- First few chars for identification
    name VARCHAR(100),
    
    -- Permissions
    scopes TEXT[], -- Array of scopes: ['projects:read', 'projects:write', ...]
    
    -- Rate Limiting
    rate_limit INTEGER DEFAULT 100, -- Requests per hour
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Usage Stats
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
```

---

## Indexes Summary

### Performance Optimization
- All foreign keys have indexes
- Frequently queried columns (status, created_at) have indexes
- Composite indexes for common query patterns

### Full-Text Search (Optional)
```sql
-- Add full-text search to projects
ALTER TABLE projects ADD COLUMN search_vector tsvector;

CREATE INDEX idx_projects_search ON projects USING gin(search_vector);

-- Trigger to update search_vector
CREATE TRIGGER projects_search_update
BEFORE INSERT OR UPDATE ON projects
FOR EACH ROW EXECUTE FUNCTION
tsvector_update_trigger(search_vector, 'pg_catalog.english', title, description);
```

---

## Migration Strategy

### Phase 1: Core Tables
1. users
2. quota_transactions
3. orders
4. projects
5. pages

### Phase 2: Advanced Features
6. subscriptions
7. templates
8. materials
9. page_versions

### Phase 3: Collaboration
10. teams
11. team_members

### Phase 4: API & System
12. tasks
13. api_keys

---

## Data Retention Policy

- **User Data**: Soft delete (set deleted_at), hard delete after 90 days
- **Projects**: Soft delete, hard delete after 30 days for free users, 180 days for premium
- **Orders**: Never delete (legal requirement)
- **Quota Transactions**: Never delete (audit trail)
- **Tasks**: Auto-delete after 7 days if completed

---

## Backup Strategy

- **Full Backup**: Daily at 2 AM UTC
- **Incremental Backup**: Every 6 hours
- **Retention**: 30 days for daily backups, 7 days for incremental
- **Point-in-Time Recovery**: Enabled (WAL archiving)

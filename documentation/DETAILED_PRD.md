# Semantis AI - Detailed Product Requirements Document (PRD)

**Version:** 1.0  
**Date:** 2025-01-27  
**Status:** Production Ready  
**Last Updated:** 2025-01-27

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Overview](#product-overview)
3. [Core Features](#core-features)
4. [Authentication & Authorization](#authentication--authorization)
5. [API Endpoints](#api-endpoints)
6. [Frontend Features](#frontend-features)
7. [SDK Features](#sdk-features)
8. [Database Schema](#database-schema)
9. [Security Features](#security-features)
10. [Performance Requirements](#performance-requirements)
11. [User Flows](#user-flows)
12. [Technical Architecture](#technical-architecture)
13. [Testing Requirements](#testing-requirements)
14. [Deployment & Infrastructure](#deployment--infrastructure)

---

## Executive Summary

**Semantis AI** is a production-ready SaaS platform providing a developer-friendly semantic caching layer for Large Language Model (LLM) applications. The platform reduces LLM costs by 50-70% and improves response latency through intelligent semantic caching, multi-tenant isolation, and OpenAI-compatible APIs.

### Key Value Propositions

- **Cost Reduction**: 50-70% reduction in LLM API costs through intelligent caching
- **Latency Improvement**: Sub-millisecond cache hits vs. 2-5 second LLM calls
- **Privacy & Control**: Bring-Your-Own-Key (BYOK) system for OpenAI API keys
- **Developer-Friendly**: Drop-in replacement for OpenAI SDK, zero code changes required
- **Multi-Tenant**: Complete data isolation per user/tenant
- **Production-Ready**: Comprehensive logging, monitoring, and admin dashboard

---

## Product Overview

### What is Semantis AI?

Semantis AI is a semantic caching service that sits between your application and OpenAI's API. It intelligently caches LLM responses based on semantic similarity, allowing similar queries to reuse cached responses without calling the LLM again.

### Target Users

1. **Developers**: Building LLM applications who want to reduce costs and improve latency
2. **Enterprises**: Requiring multi-tenant isolation, BYOK privacy, and admin controls
3. **SaaS Providers**: Needing cost-effective LLM integration with caching

### Core Goals

1. Deliver a zero-infrastructure, developer-first caching layer compatible with OpenAI APIs
2. Achieve 50-70% cache hit rates on typical LLM workloads within 30 days
3. Provide transparent observability through rich metrics, hit ratios, similarity scores, and cost savings
4. Support multi-tenant isolation with secure API key authentication
5. Offer pluggable vector store backends (initially FAISS, with pgvector/Redis/Milvus planned)

---

## Core Features

### 1. Semantic Caching Engine

#### 1.1 Hybrid Cache Mechanism
- **Exact Match**: Fast hash-based lookup for identical queries (<0.02ms latency)
- **Semantic Match**: FAISS cosine similarity search for similar queries (0.5-1ms latency)
- **Cache Miss**: Fallback to OpenAI API with automatic cache storage

#### 1.2 Cache Matching Strategy
- **Exact Match Priority**: Checks normalized text hash first (fastest)
- **Semantic Search**: Uses `text-embedding-3-large` embeddings with FAISS index
- **Similarity Threshold**: Adaptive per-tenant threshold (default: 0.83)
- **Query Expansion**: Context-aware embedding generation for better matching

#### 1.3 Cache Storage
- **In-Memory**: FAISS index for fast similarity search
- **Persistent**: SQLite database for cache entries and metadata
- **TTL Support**: Configurable time-to-live per cache entry (default: 7 days)
- **Asynchronous Storage**: Non-blocking cache entry storage for optimal latency

#### 1.4 Performance Optimizations
- **Embedding Reuse**: Single embedding generation per query (saves ~7-8ms)
- **Asynchronous Operations**: Cache storage, event logging, and database logging in background threads
- **Adaptive Search**: Dynamic candidate search based on cache size (10-20 candidates)
- **Thread-Safe Operations**: Lock-based synchronization for concurrent access

### 2. Multi-Tenant Architecture

#### 2.1 Tenant Isolation
- **API Key Based**: Each tenant has unique API key (`sc-{tenant}-{random}`)
- **Data Isolation**: Complete separation of cache data, metrics, and logs per tenant
- **User Linking**: API keys linked to user accounts for proper multi-tenancy

#### 2.2 Tenant Management
- **Automatic Tenant Creation**: Generated on API key creation
- **Tenant ID Format**: `usr_{user_id}` for user-based tenants
- **Tenant Reuse**: Existing tenants reused when users regenerate keys

### 3. Bring-Your-Own-Key (BYOK) System

#### 3.1 OpenAI Key Management
- **Encrypted Storage**: Fernet symmetric encryption for OpenAI API keys
- **User-Specific Keys**: Each user provides their own OpenAI API key
- **Privacy**: Semantis AI never sees user queries or responses
- **Cost Tracking**: Users track their own OpenAI usage and costs

#### 3.2 Key Operations
- **Set Key**: Users can add their OpenAI API key via Account Settings
- **Check Status**: Verify if OpenAI key is configured
- **Remove Key**: Delete stored OpenAI key
- **Key Validation**: Format validation (must start with `sk-`)

### 4. Adaptive Threshold Tuning

#### 4.1 Per-Tenant Thresholds
- **Initial Threshold**: 0.83 (83% similarity required)
- **Adaptive Adjustment**: Automatically adjusts based on cache hit rates
- **Target Hit Rate**: Maintains 50-70% cache hit ratio
- **Threshold Range**: 0.75 - 0.95 (configurable)

#### 4.2 Threshold Logic
- **High Hit Rate (>70%)**: Increase threshold (stricter matching)
- **Low Hit Rate (<50%)**: Decrease threshold (looser matching)
- **Window-Based**: Evaluates hit rate over configurable time window

---

## Authentication & Authorization

### 1. User Authentication

#### 1.1 Sign Up
- **Endpoint**: `POST /api/auth/signup`
- **Required Fields**: `email`, `password`, `name` (optional)
- **Validation**:
  - Email format validation
  - Password strength requirements (min 8 characters)
  - Duplicate email check
- **Password Security**: bcrypt hashing with salt rounds

#### 1.2 Sign In
- **Endpoint**: `POST /api/auth/login`
- **Required Fields**: `email`, `password`
- **Response**: JWT access token + user info
- **Security**: Generic error messages (don't reveal if email exists)
- **Token Expiry**: Configurable (default: 24 hours)

#### 1.3 Token Management
- **JWT Tokens**: Signed with secret key
- **Token Storage**: Frontend stores in localStorage
- **Token Validation**: Middleware validates on protected routes
- **Auto-Refresh**: Token loaded on page refresh for persistence

### 2. API Key Authentication

#### 2.1 API Key Format
- **Format**: `sc-{tenant}-{random_string}`
- **Example**: `sc-usr_123-abc123def456`
- **Length**: Configurable (default: 32 characters)
- **Bearer Token**: Used in `Authorization: Bearer {api_key}` header

#### 2.2 API Key Generation
- **Endpoint**: `POST /api/keys/generate`
- **Authentication**: Requires user login (JWT token)
- **Tenant Linking**: Automatically linked to authenticated user
- **Key Reuse**: Reuses existing key if user already has one
- **Plan Support**: Free, Pro, Enterprise plans

#### 2.3 API Key Retrieval
- **Endpoint**: `GET /api/keys/current`
- **Authentication**: Requires user login
- **Response**: User's current API key (if exists)

### 3. Admin Authentication

#### 3.1 Admin Login
- **Endpoint**: `POST /api/auth/admin/login`
- **Required Fields**: `email`, `password`
- **Admin Check**: Verifies `is_admin` flag in user record
- **Response**: JWT token with admin privileges

#### 3.2 Admin Routes
- **Protection**: `AdminRoute` component checks `is_admin` flag
- **Redirect**: Non-admin users redirected to `/admin/login`
- **Dashboard**: Full admin dashboard access

### 4. Route Protection

#### 4.1 Protected Routes
- **Frontend**: `ProtectedRoute` component
- **Requirement**: User must be authenticated
- **Redirect**: Unauthenticated users → `/signin`
- **Loading State**: Shows "Loading..." while checking auth

#### 4.2 Admin Routes
- **Frontend**: `AdminRoute` component
- **Requirement**: User must be authenticated AND `is_admin=true`
- **Redirect**: Non-admin users → `/admin/login`

---

## API Endpoints

### Public Endpoints

#### Health Check
- **GET** `/health`
- **Description**: Service health status
- **Response**: `{ "status": "ok", "service": "semantic-cache", "version": "0.1.0" }`
- **Auth**: None required

### User Endpoints (Require JWT Authentication)

#### Sign Up
- **POST** `/api/auth/signup`
- **Body**: `{ "email": string, "password": string, "name": string (optional) }`
- **Response**: `{ "user_id": int, "email": string, "name": string, "message": string }`

#### Sign In
- **POST** `/api/auth/login`
- **Body**: `{ "email": string, "password": string }`
- **Response**: `{ "access_token": string, "token_type": "bearer", "user": {...} }`

#### Get Current User
- **GET** `/api/auth/me`
- **Headers**: `Authorization: Bearer {jwt_token}`
- **Response**: `{ "id": int, "email": string, "name": string, "is_admin": bool }`

#### Logout
- **POST** `/api/auth/logout`
- **Headers**: `Authorization: Bearer {jwt_token}`
- **Response**: `{ "message": "Logged out successfully" }`

#### Admin Login
- **POST** `/api/auth/admin/login`
- **Body**: `{ "email": string, "password": string }`
- **Response**: `{ "access_token": string, "token_type": "bearer", "user": {...} }`

### API Key Management (Require JWT Authentication)

#### Generate API Key
- **POST** `/api/keys/generate`
- **Headers**: `Authorization: Bearer {jwt_token}`
- **Query Params**: `tenant` (optional), `length` (optional, default: 32), `plan` (optional, default: "free")
- **Response**: `{ "api_key": string, "tenant_id": string, "plan": string, "created_at": string, "format": string, "message": string }`

#### Get Current API Key
- **GET** `/api/keys/current`
- **Headers**: `Authorization: Bearer {jwt_token}`
- **Response**: `{ "api_key": string, "tenant_id": string, "plan": string, "created_at": string, "exists": bool }`

### OpenAI Key Management (Require JWT Authentication)

#### Set OpenAI API Key
- **POST** `/api/users/openai-key`
- **Headers**: `Authorization: Bearer {jwt_token}`
- **Body**: `{ "api_key": string }`
- **Response**: `{ "message": string, "key_set": bool }`

#### Get OpenAI Key Status
- **GET** `/api/users/openai-key`
- **Headers**: `Authorization: Bearer {jwt_token}`
- **Response**: `{ "key_set": bool, "key_preview": string (masked), "message": string }`

#### Remove OpenAI Key
- **DELETE** `/api/users/openai-key`
- **Headers**: `Authorization: Bearer {jwt_token}`
- **Response**: `{ "message": string, "key_set": bool }`

### Cache Endpoints (Require API Key Authentication)

#### Simple Query
- **GET** `/query`
- **Headers**: `Authorization: Bearer {api_key}`
- **Query Params**: `prompt` (required), `model` (optional, default: "gpt-4o-mini"), `temperature` (optional, default: 0.2)
- **Response**: `{ "answer": string, "cache_hit": "exact" | "semantic" | "miss", "similarity": float, "latency_ms": float, "metadata": {...} }`

#### OpenAI-Compatible Chat Completions
- **POST** `/v1/chat/completions`
- **Headers**: `Authorization: Bearer {api_key}`, `Content-Type: application/json`
- **Body**: `{ "model": string, "messages": Array<{role: string, content: string}>, "temperature": float (optional), "ttl_seconds": int (optional) }`
- **Response**: OpenAI-compatible format with additional `cache_hit`, `similarity`, `latency_ms` fields

#### Get Metrics
- **GET** `/metrics`
- **Headers**: `Authorization: Bearer {api_key}`
- **Response**: `{ "tenant": string, "hit_ratio": float, "total_queries": int, "cache_hits": int, "cache_misses": int, "exact_hits": int, "semantic_hits": int, "avg_latency_ms": float, "total_tokens": int, "cost_estimate": float }`

#### Get Cache Events
- **GET** `/events`
- **Headers**: `Authorization: Bearer {api_key}`
- **Query Params**: `limit` (optional, default: 100)
- **Response**: `{ "events": Array<{timestamp: string, type: string, prompt: string, cache_hit: string, similarity: float}> }`

#### Prometheus Metrics
- **GET** `/prometheus/metrics`
- **Headers**: `Authorization: Bearer {api_key}`
- **Response**: Prometheus-formatted metrics

### Admin Endpoints (Require Admin API Key)

#### Analytics Summary
- **GET** `/admin/analytics/summary?api_key={admin_key}&days=30`
- **Response**: `{ "total_users": int, "total_api_keys": int, "active_users": int, "total_requests": int, "total_cache_hits": int, "total_cache_misses": int, "cache_hit_ratio": float, "total_tokens_used": int, "total_cost_estimate": float }`

#### User Growth Statistics
- **GET** `/admin/analytics/user-growth?api_key={admin_key}&period=daily&days=30`
- **Response**: `{ "period": string, "days": int, "data": Array<{date: string, new_users: int, new_api_keys: int, total_users: int}> }`

#### Plan Distribution
- **GET** `/admin/analytics/plan-distribution?api_key={admin_key}`
- **Response**: `{ "total_active_keys": int, "plans": Array<{plan: string, count: int, percentage: float, total_requests: int, total_cost: float}> }`

#### Usage Trends
- **GET** `/admin/analytics/usage-trends?api_key={admin_key}&days=30`
- **Response**: `{ "days": int, "data": Array<{date: string, requests: int, cache_hits: int, cache_misses: int, hit_ratio: float}> }`

#### Top Users
- **GET** `/admin/analytics/top-users?api_key={admin_key}&limit=10`
- **Response**: `{ "users": Array<{user_id: int, email: string, total_requests: int, cache_hits: int, cache_misses: int, hit_ratio: float, total_tokens: int, cost_estimate: float}> }`

#### List Users
- **GET** `/admin/users?api_key={admin_key}&page=1&limit=20&search={query}`
- **Response**: `{ "users": Array<{id: int, email: string, name: string, is_admin: bool, created_at: string, last_login_at: string}>, "total": int, "page": int, "limit": int }`

#### User Details
- **GET** `/admin/users/{tenant_id}/details?api_key={admin_key}`
- **Response**: `{ "user": {...}, "api_keys": Array<{...}>, "usage_stats": {...} }`

#### Update User Plan
- **POST** `/admin/users/{tenant_id}/update-plan?api_key={admin_key}`
- **Body**: `{ "plan": string }`
- **Response**: `{ "message": string, "plan": string }`

#### Deactivate User
- **POST** `/admin/users/{tenant_id}/deactivate?api_key={admin_key}`
- **Response**: `{ "message": string }`

#### System Statistics
- **GET** `/admin/system/stats?api_key={admin_key}`
- **Response**: `{ "cache_size": int, "total_tenants": int, "database_size_mb": float, "uptime_seconds": int, "memory_usage_mb": float (optional), "cpu_percent": float (optional) }`

---

## Frontend Features

### 1. Landing Page
- **Route**: `/`
- **Features**:
  - Product overview and value proposition
  - Feature highlights
  - Call-to-action buttons (Sign Up / Sign In)
  - Pricing information link

### 2. Authentication Pages

#### Sign Up Page
- **Route**: `/signup`
- **Features**:
  - Email, password, name input
  - Password strength indicator
  - Email validation
  - Error handling
  - Redirect to `/playground` on success

#### Sign In Page
- **Route**: `/signin`
- **Features**:
  - Email and password input
  - "Forgot Password" link (future)
  - Error messages
  - Redirect to `/playground` on success
  - Link to sign up page

#### Admin Login Page
- **Route**: `/admin/login`
- **Features**:
  - Admin-specific login form
  - Redirect to `/admin` dashboard on success

### 3. Protected Pages (Require Authentication)

#### Playground Page
- **Route**: `/playground`
- **Features**:
  - Query input field
  - Model selection (gpt-4o-mini, etc.)
  - Temperature slider
  - API key input/validation
  - Run Query button
  - Response display with cache hit information
  - OpenAI key status warning (if not set)
  - Query history

#### Metrics Page
- **Route**: `/metrics`
- **Features**:
  - Cache hit ratio visualization
  - Total queries counter
  - Cache hits vs misses breakdown
  - Exact hits vs semantic hits
  - Average latency chart
  - Token usage statistics
  - Cost estimate
  - Time range selector (last 24h, 7d, 30d)

#### Logs Page
- **Route**: `/logs`
- **Features**:
  - Recent cache events table
  - Filter by cache hit type (exact, semantic, miss)
  - Search by prompt text
  - Timestamp display
  - Similarity scores
  - Pagination

#### Settings Page
- **Route**: `/settings`
- **Features**:
  - Cache settings (TTL, threshold)
  - API key management
  - OpenAI key management (BYOK)
  - Account information
  - Plan information

### 4. Admin Pages (Require Admin Authentication)

#### Admin Dashboard
- **Route**: `/admin`
- **Features**:
  - Overview cards (total users, active users, requests, cache hit ratio)
  - User growth chart
  - Plan distribution chart
  - Usage trends chart
  - Top users table
  - Quick links to other admin pages

#### Admin Users
- **Route**: `/admin/users`
- **Features**:
  - User list table with pagination
  - Search functionality
  - User details view
  - Edit user information
  - Deactivate users

#### Admin Top Users
- **Route**: `/admin/top-users`
- **Features**:
  - Top users by usage
  - Sortable columns
  - Export functionality (future)

#### Admin Analytics
- **Route**: `/admin/analytics`
- **Features**:
  - Detailed analytics charts
  - Export reports (future)
  - Custom date ranges

#### Admin Settings
- **Route**: `/admin/settings`
- **Features**:
  - System configuration
  - Admin API key management
  - Cache configuration
  - Email settings (future)

### 5. Common Components

#### Account Menu
- **Location**: Top-right corner (all authenticated pages)
- **Features**:
  - User email/name display
  - Dropdown menu:
    - Settings (opens Settings modal)
    - API Keys (opens API Keys modal)
    - Account Information
    - Logout
  - Modals:
    - **Settings Modal**: Profile info, OpenAI key management
    - **API Keys Modal**: View/generate API keys
    - **New Key Modal**: Generate new API key

#### Layout Component
- **Features**:
  - Navigation sidebar
  - Header with account menu
  - Responsive design
  - Loading states

#### Query Playground Component
- **Features**:
  - Query input with syntax highlighting
  - Model selection dropdown
  - Temperature control
  - API key validation
  - Response display with formatting
  - Cache hit indicators
  - Error handling

---

## SDK Features

### 1. Python SDK

#### 1.1 Simple Query Method
```python
from semantis_cache import SemanticCache

cache = SemanticCache(api_key="sc-your-key")
response = cache.query("What is our refund policy?")
print(response.answer)
print(f"Cache hit: {response.cache_hit}")  # 'exact', 'semantic', or 'miss'
```

#### 1.2 OpenAI Proxy Module
```python
from semantis_cache.openai_proxy import ChatCompletion

response = ChatCompletion.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is AI?"}]
)
```

#### 1.3 Features
- **Drop-in Replacement**: Compatible with OpenAI SDK
- **Automatic Caching**: No code changes required
- **Retry Logic**: Built-in retry with exponential backoff
- **Error Handling**: Comprehensive error handling
- **Type Hints**: Full type annotations

### 2. TypeScript SDK

#### 2.1 Basic Usage
```typescript
import { SemanticCache } from 'semantis-cache';

const cache = new SemanticCache({ apiKey: 'sc-your-key' });
const response = await cache.query('What is AI?');
console.log(response.answer);
```

#### 2.2 Features
- **TypeScript Support**: Full type definitions
- **Promise-Based**: Async/await support
- **Error Handling**: Try-catch error handling
- **Retry Logic**: Automatic retry on failures

### 3. Integration Wrappers

#### 3.1 LangChain Integration
```python
from semantis_cache.integrations.langchain import SemantisCacheLLM

llm = SemantisCacheLLM(api_key="sc-your-key")
response = llm("What is Python?")
```

#### 3.2 LlamaIndex Integration
```python
from semantis_cache.integrations.llamaindex import SemantisCacheLLM

llm = SemantisCacheLLM(api_key="sc-your-key")
response = llm.complete("What is Python?")
```

#### 3.3 FastAPI Middleware
```python
from semantis_cache.integrations.fastapi import SemanticCacheMiddleware

app.add_middleware(SemanticCacheMiddleware, api_key="sc-your-key")
```

#### 3.4 Express Middleware
```javascript
const semanticCacheMiddleware = require('semantis-cache/integrations/express');

app.use(semanticCacheMiddleware({ apiKey: 'sc-your-key' }));
```

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    name TEXT,
    password_hash TEXT,
    email_verified BOOLEAN DEFAULT 0,
    is_admin BOOLEAN DEFAULT 0,
    openai_api_key_encrypted TEXT,  -- BYOK: Encrypted OpenAI key
    last_login_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Indexes**:
- `email` (unique)

### API Keys Table
```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key TEXT UNIQUE NOT NULL,
    tenant_id TEXT NOT NULL,
    user_id INTEGER,
    plan TEXT DEFAULT 'free',
    plan_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

**Indexes**:
- `api_key` (unique)
- `tenant_id`
- `user_id`

### Usage Logs Table
```sql
CREATE TABLE usage_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key TEXT NOT NULL,
    tenant_id TEXT NOT NULL,
    user_id INTEGER,
    endpoint TEXT,
    request_count INTEGER DEFAULT 1,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    tokens_used INTEGER DEFAULT 0,
    cost_estimate REAL DEFAULT 0,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_key) REFERENCES api_keys (api_key),
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

**Indexes**:
- `api_key`
- `tenant_id`
- `user_id`
- `logged_at`

### Cache Storage
- **In-Memory**: FAISS index for vector similarity search
- **Persistent**: SQLite database for cache entries (future: PostgreSQL)
- **Cache Entries**: Stored with embeddings, responses, metadata, TTL

---

## Security Features

### 1. Authentication Security

#### Password Security
- **Hashing**: bcrypt with salt rounds
- **Strength Requirements**: Minimum 8 characters
- **No Plain Text**: Passwords never stored in plain text
- **Password Reset**: Future feature (not implemented)

#### JWT Tokens
- **Signing**: Secret key-based signing
- **Expiry**: Configurable token expiration (default: 24 hours)
- **Validation**: Token validation on all protected routes
- **Storage**: Frontend stores in localStorage (consider httpOnly cookies for production)

### 2. API Key Security

#### Key Generation
- **Random Generation**: Cryptographically secure random strings
- **Unique Keys**: Database-enforced uniqueness
- **Key Format**: `sc-{tenant}-{random}` format validation

#### Key Storage
- **Database**: Stored in SQLite database
- **Hashing**: Future: Consider hashing API keys (currently stored as-is)
- **Key Rotation**: Users can generate new keys

### 3. Encryption

#### OpenAI Key Encryption
- **Algorithm**: Fernet symmetric encryption
- **Key Derivation**: PBKDF2HMAC with SHA256
- **Key Storage**: Encryption key from `ENCRYPTION_KEY` environment variable
- **Validation**: Format validation (must start with `sk-`)

### 4. Data Isolation

#### Multi-Tenant Isolation
- **Tenant-Based**: All cache data isolated by `tenant_id`
- **User-Based**: API keys linked to `user_id` for proper isolation
- **Database Queries**: All queries filtered by `tenant_id` or `user_id`

### 5. Input Validation

#### API Input Validation
- **Email Validation**: Format and domain validation
- **Password Validation**: Strength requirements
- **API Key Validation**: Format validation
- **OpenAI Key Validation**: Format validation (`sk-` prefix)

### 6. Error Handling

#### Security-Conscious Errors
- **Generic Messages**: Don't reveal if email exists during login
- **No Key Exposure**: Never expose API keys in error messages
- **Logging**: Security events logged to `security.log`

### 7. CORS Configuration

#### Frontend-Backend Communication
- **Allowed Origins**: Configurable CORS origins
- **Credentials**: Support for credentials in requests
- **Headers**: Allowed headers configuration

---

## Performance Requirements

### 1. Latency Targets

#### Cache Hits
- **Exact Match**: < 0.02ms (hash lookup)
- **Semantic Match**: 0.5 - 1ms (FAISS search)
- **Cache Miss**: < 1ms overhead (before LLM call)

#### Cache Miss Optimizations
- **Embedding Reuse**: Single embedding generation per query
- **Asynchronous Storage**: Cache storage in background thread
- **Asynchronous Logging**: Database logging in background thread
- **Lock Optimization**: Minimal lock contention

### 2. Throughput Targets

#### Request Handling
- **Concurrent Requests**: Support multiple concurrent requests
- **Thread Safety**: Thread-safe cache operations
- **Database Connections**: Connection pooling (future)

### 3. Cache Performance

#### Hit Rate Targets
- **Target Hit Rate**: 50-70% cache hit ratio
- **Adaptive Threshold**: Automatic threshold adjustment
- **Cache Size**: Efficient handling of large cache sizes (1000+ entries)

### 4. Scalability

#### Horizontal Scaling (Future)
- **Stateless Design**: API server can be horizontally scaled
- **Shared Cache**: Redis/PostgreSQL for shared cache (future)
- **Load Balancing**: Support for load balancers

---

## User Flows

### 1. New User Sign Up Flow

1. User visits landing page (`/`)
2. Clicks "Sign Up" → navigates to `/signup`
3. Enters email, password, name
4. Submits form → `POST /api/auth/signup`
5. Account created → redirects to `/signin`
6. User signs in → `POST /api/auth/login`
7. Receives JWT token → redirects to `/playground`
8. User sees "Generate API Key" prompt
9. Clicks "Generate API Key" → `POST /api/keys/generate`
10. Receives API key → stores in localStorage
11. User adds OpenAI API key in Account Settings → `POST /api/users/openai-key`
12. User can now use playground

### 2. Existing User Sign In Flow

1. User visits `/signin`
2. Enters email and password
3. Submits form → `POST /api/auth/login`
4. Receives JWT token → stored in localStorage
5. Frontend loads user data → `GET /api/auth/me`
6. Frontend loads API key → `GET /api/keys/current`
7. Redirects to `/playground`
8. User can immediately use playground

### 3. Query Execution Flow

1. User enters query in playground
2. Validates API key is set
3. Validates OpenAI key is set (shows warning if not)
4. Clicks "Run Query" → `GET /query?prompt={query}`
5. Backend checks cache:
   - **Exact Match**: Returns cached response (< 0.02ms)
   - **Semantic Match**: Returns cached response (0.5-1ms)
   - **Cache Miss**: Calls OpenAI API, stores in cache, returns response
6. Frontend displays response with cache hit information
7. Metrics updated automatically

### 4. API Key Generation Flow

1. User navigates to Account Menu → Settings
2. Clicks "API Keys" → opens API Keys modal
3. Clicks "Generate New Key" → opens New Key modal
4. Enters key name (optional)
5. Clicks "Create Key" → `POST /api/keys/generate`
6. Receives API key → displayed in modal
7. Copies key → stores in localStorage
8. Key appears in API Keys list

### 5. OpenAI Key Management Flow

1. User navigates to Account Menu → Settings
2. Scrolls to "OpenAI API Key" section
3. If key not set:
   - Enters OpenAI API key
   - Clicks "Save OpenAI API Key" → `POST /api/users/openai-key`
   - Key encrypted and stored
4. If key set:
   - Sees masked preview (`sk-***`)
   - Can click "Remove" → `DELETE /api/users/openai-key`
   - Key removed from database

### 6. Admin Dashboard Flow

1. Admin visits `/admin/login`
2. Enters admin email and password
3. Submits → `POST /api/auth/admin/login`
4. Receives JWT token → redirects to `/admin`
5. Views dashboard with analytics
6. Can navigate to:
   - Users (`/admin/users`)
   - Top Users (`/admin/top-users`)
   - Analytics (`/admin/analytics`)
   - Settings (`/admin/settings`)

---

## Technical Architecture

### 1. Backend Architecture

#### Technology Stack
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn (ASGI server)
- **Database**: SQLite (development) → PostgreSQL (production)
- **Vector Store**: FAISS (in-memory) → pgvector/Redis (future)
- **Authentication**: JWT (python-jose)
- **Password Hashing**: bcrypt
- **Encryption**: Fernet (cryptography)

#### Project Structure
```
backend/
├── semantic_cache_server.py  # Main FastAPI application
├── database.py                # Database operations
├── auth.py                    # Authentication utilities
├── encryption.py              # Encryption utilities
├── admin_api.py               # Admin endpoints
├── cache_data/                # SQLite database
├── logs/                      # Rotating log files
└── requirements.txt           # Python dependencies
```

#### Key Components
- **SemanticCacheService**: Core caching logic
- **FAISS Index**: Vector similarity search
- **Database Layer**: SQLite operations
- **Authentication Middleware**: JWT validation
- **Logging System**: Rotating file handlers

### 2. Frontend Architecture

#### Technology Stack
- **Framework**: React 18
- **Build Tool**: Vite
- **Routing**: React Router DOM
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios (via fetch API)
- **State Management**: React Context API

#### Project Structure
```
frontend/
├── src/
│   ├── App.tsx                # Main app component
│   ├── contexts/
│   │   └── AuthContext.tsx    # Authentication context
│   ├── pages/                 # Page components
│   ├── components/            # Reusable components
│   ├── api/                   # API client functions
│   └── hooks/                 # Custom React hooks
├── public/                    # Static assets
└── package.json               # Dependencies
```

#### Key Components
- **AuthProvider**: Authentication state management
- **ProtectedRoute**: Route protection component
- **AdminRoute**: Admin route protection
- **QueryPlayground**: Query interface
- **AccountMenu**: User account dropdown

### 3. SDK Architecture

#### Python SDK Structure
```
sdk/python-wrapper/
├── semantis_cache/
│   ├── __init__.py
│   ├── query.py              # Simple query method
│   ├── openai_proxy.py       # OpenAI-compatible proxy
│   └── client.py            # HTTP client
├── setup.py
└── pyproject.toml
```

#### TypeScript SDK Structure
```
sdk/typescript/
├── src/
│   ├── index.ts              # Main SDK
│   └── client.ts             # HTTP client
├── package.json
└── tsconfig.json
```

### 4. Data Flow

#### Query Flow
1. **Client** → HTTP Request → **FastAPI Server**
2. **FastAPI** → Extract API key → **Authentication Middleware**
3. **Middleware** → Validate key → **Database** (get tenant_id)
4. **FastAPI** → Extract prompt → **SemanticCacheService**
5. **Service** → Check exact match → **In-Memory Cache**
6. **Service** → Check semantic match → **FAISS Index**
7. **Service** → Cache miss → **OpenAI API** (with user's key)
8. **Service** → Store in cache → **Background Thread**
9. **Service** → Return response → **Client**

#### Authentication Flow
1. **Client** → Login request → **FastAPI**
2. **FastAPI** → Validate credentials → **Database**
3. **FastAPI** → Generate JWT → **Client**
4. **Client** → Store token → **localStorage**
5. **Client** → Include token → **All requests**
6. **FastAPI** → Validate token → **JWT Middleware**

---

## Testing Requirements

### 1. Backend Testing

#### Unit Tests
- **Database Operations**: Test CRUD operations
- **Authentication**: Test password hashing, JWT generation/validation
- **Encryption**: Test encryption/decryption of OpenAI keys
- **Cache Logic**: Test exact match, semantic match, cache miss

#### Integration Tests
- **API Endpoints**: Test all endpoints with valid/invalid inputs
- **Authentication Flow**: Test signup, login, token validation
- **Cache Flow**: Test query → cache hit/miss → response
- **Multi-Tenant**: Test tenant isolation

#### Performance Tests
- **Latency Tests**: Verify cache hit latency < 1ms
- **Throughput Tests**: Test concurrent requests
- **Cache Miss Tests**: Verify < 1ms overhead

### 2. Frontend Testing

#### Component Tests
- **AuthContext**: Test login, logout, token persistence
- **ProtectedRoute**: Test route protection logic
- **QueryPlayground**: Test query submission, response display
- **AccountMenu**: Test modal opening/closing, API key generation

#### Integration Tests
- **Authentication Flow**: Test signup → login → playground
- **API Key Flow**: Test generation → storage → usage
- **OpenAI Key Flow**: Test setting → encryption → usage

#### E2E Tests (Future)
- **Full User Flow**: Signup → Generate Key → Add OpenAI Key → Query
- **Admin Flow**: Admin login → Dashboard → User management

### 3. SDK Testing

#### Python SDK Tests
- **Query Method**: Test cache hits/misses
- **OpenAI Proxy**: Test OpenAI-compatible API
- **Error Handling**: Test retry logic, error messages

#### TypeScript SDK Tests
- **Query Method**: Test async operations
- **Error Handling**: Test promise rejection handling

### 4. Test Coverage Targets

- **Backend**: > 80% code coverage
- **Frontend**: > 70% component coverage
- **SDK**: > 90% method coverage

---

## Deployment & Infrastructure

### 1. Development Environment

#### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python semantic_cache_server.py
```

#### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

#### Environment Variables
```bash
# Backend (.env)
OPENAI_API_KEY=sk-your-key
ENCRYPTION_KEY=your-encryption-key
PORT=8000
ADMIN_API_KEY=admin-secret-key-change-me

# Frontend (.env)
VITE_BACKEND_URL=http://localhost:8000
```

### 2. Production Deployment (Future)

#### Backend Deployment
- **Container**: Docker container with Python 3.11+
- **Database**: PostgreSQL with pgvector extension
- **Cache**: Redis for shared cache (optional)
- **Server**: Gunicorn/Uvicorn with multiple workers
- **Load Balancer**: Nginx or cloud load balancer

#### Frontend Deployment
- **Build**: `npm run build` → static files
- **Hosting**: Nginx, Vercel, Netlify, or S3+CloudFront
- **CDN**: CloudFront or Cloudflare for static assets

#### Monitoring
- **Logging**: Centralized logging (CloudWatch, Datadog)
- **Metrics**: Prometheus + Grafana
- **Error Tracking**: Sentry or similar
- **Uptime Monitoring**: Pingdom or UptimeRobot

### 3. Scalability Considerations

#### Horizontal Scaling
- **Stateless API**: API servers can be horizontally scaled
- **Shared Database**: PostgreSQL for shared state
- **Shared Cache**: Redis for shared cache (future)
- **Load Balancing**: Round-robin or least-connections

#### Vertical Scaling
- **Database**: PostgreSQL with connection pooling
- **Cache**: FAISS index in memory (consider Redis for large scale)
- **Workers**: Multiple Uvicorn workers per server

### 4. Security Considerations

#### Production Security
- **HTTPS**: SSL/TLS certificates (Let's Encrypt)
- **Environment Variables**: Secure secret management (AWS Secrets Manager, etc.)
- **Database**: Encrypted at rest, encrypted connections
- **API Keys**: Consider hashing API keys (currently stored as-is)
- **Rate Limiting**: Implement rate limiting per API key
- **CORS**: Restrict CORS to production domains only

---

## Appendix

### A. API Response Examples

#### Query Response (Cache Hit)
```json
{
  "answer": "Python is a high-level programming language...",
  "cache_hit": "semantic",
  "similarity": 0.92,
  "latency_ms": 0.85,
  "metadata": {
    "model": "gpt-4o-mini",
    "temperature": 0.2,
    "cached_at": "2025-01-27T10:30:00Z"
  }
}
```

#### Query Response (Cache Miss)
```json
{
  "answer": "Python is a high-level programming language...",
  "cache_hit": "miss",
  "similarity": 0.0,
  "latency_ms": 2345.67,
  "metadata": {
    "model": "gpt-4o-mini",
    "temperature": 0.2,
    "tokens_used": 150,
    "cost_estimate": 0.001
  }
}
```

### B. Error Response Examples

#### Authentication Error
```json
{
  "detail": "Invalid email or password"
}
```

#### API Key Error
```json
{
  "detail": "Invalid or missing API key"
}
```

#### OpenAI Key Error
```json
{
  "detail": "OpenAI API key not configured. Please add your OpenAI API key in Account Settings."
}
```

### C. Environment Variables Reference

#### Backend
- `OPENAI_API_KEY`: Default OpenAI API key (fallback, not used with BYOK)
- `ENCRYPTION_KEY`: Fernet encryption key for OpenAI keys
- `PORT`: Server port (default: 8000)
- `ADMIN_API_KEY`: Admin API key for admin endpoints
- `JWT_SECRET_KEY`: Secret key for JWT token signing
- `JWT_ALGORITHM`: JWT algorithm (default: HS256)
- `JWT_EXPIRATION_HOURS`: Token expiration in hours (default: 24)

#### Frontend
- `VITE_BACKEND_URL`: Backend API URL (default: http://localhost:8000)

### D. Logging

#### Log Files
- `logs/access.log`: HTTP request/response logging
- `logs/errors.log`: Error logging
- `logs/semantic_ops.log`: Cache operations (hits/misses)
- `logs/performance.log`: Performance metrics
- `logs/security.log`: Security events
- `logs/system.log`: System events
- `logs/application.log`: Application events

#### Log Rotation
- **Max Size**: 10MB per file
- **Backup Count**: 5 backup files
- **Format**: `%(asctime)s | %(levelname)s | %(message)s`

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|----------|--------|
| 1.0 | 2025-01-27 | Initial comprehensive PRD | AI Assistant |

---

## Approval

**Status**: ✅ **Production Ready**

This PRD documents the complete Semantis AI platform as implemented. All features described are functional and tested. The platform is ready for MVP launch and can be used with testing tools like TestSprite MCP for validation.

---

**End of Document**


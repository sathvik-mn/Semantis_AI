# Bolt AI Frontend Generation Prompt

**Copy and paste this entire prompt into Bolt AI to generate the admin dashboard frontend.**

---

## Project Overview

Create a comprehensive admin dashboard for Semantis AI - a semantic caching service for LLM applications. The dashboard should provide complete visibility into:
- User growth and analytics
- Subscription plan distribution
- Usage statistics and trends
- User management
- System health and performance

## Backend API Base URL

```
http://localhost:8000
```

All admin endpoints require authentication via `api_key` query parameter (admin API key).

## API Endpoints Reference

### Authentication
All admin endpoints require `?api_key=<ADMIN_API_KEY>` query parameter.

**Admin API Key**: Set via `ADMIN_API_KEY` environment variable (default: "admin-secret-key-change-me")

---

### 1. Analytics Summary
**GET** `/admin/analytics/summary?api_key=<KEY>&days=30`

Returns overall analytics summary.

**Response:**
```json
{
  "total_users": 150,
  "total_api_keys": 175,
  "active_users": 120,
  "total_requests": 45000,
  "total_cache_hits": 36000,
  "total_cache_misses": 9000,
  "cache_hit_ratio": 80.0,
  "total_tokens_used": 4500000,
  "total_cost_estimate": 1250.50
}
```

---

### 2. User Growth Statistics
**GET** `/admin/analytics/user-growth?api_key=<KEY>&period=daily&days=30`

Get user growth over time (daily, weekly, or monthly).

**Query Parameters:**
- `period`: "daily" | "weekly" | "monthly"
- `days`: Number of days to look back (1-365)

**Response:**
```json
{
  "period": "daily",
  "days": 30,
  "data": [
    {
      "date": "2024-01-15",
      "new_users": 5,
      "new_api_keys": 8,
      "total_users": 150
    },
    ...
  ]
}
```

---

### 3. Plan Distribution
**GET** `/admin/analytics/plan-distribution?api_key=<KEY>`

Get subscription plan distribution statistics.

**Response:**
```json
{
  "total_active_keys": 175,
  "plans": [
    {
      "plan": "free",
      "count": 120,
      "percentage": 68.57,
      "total_requests": 30000,
      "total_cost": 500.00
    },
    {
      "plan": "pro",
      "count": 45,
      "percentage": 25.71,
      "total_requests": 12000,
      "total_cost": 600.00
    },
    {
      "plan": "enterprise",
      "count": 10,
      "percentage": 5.71,
      "total_requests": 3000,
      "total_cost": 150.50
    }
  ]
}
```

---

### 4. Usage Trends
**GET** `/admin/analytics/usage-trends?api_key=<KEY>&period=daily&days=30`

Get usage trends over time.

**Query Parameters:**
- `period`: "daily" | "weekly" | "monthly"
- `days`: Number of days (1-365)

**Response:**
```json
{
  "period": "daily",
  "days": 30,
  "data": [
    {
      "date": "2024-01-15",
      "requests": 1500,
      "cache_hits": 1200,
      "cache_misses": 300,
      "cache_hit_ratio": 80.0,
      "tokens_used": 150000,
      "cost_estimate": 41.67
    },
    ...
  ]
}
```

---

### 5. Top Users
**GET** `/admin/analytics/top-users?api_key=<KEY>&limit=10&sort_by=usage_count&days=30`

Get top users by usage.

**Query Parameters:**
- `limit`: Number of users to return (1-100)
- `sort_by`: "usage_count" | "requests" | "cost"
- `days`: Days to look back (1-365)

**Response:**
```json
{
  "limit": 10,
  "sort_by": "usage_count",
  "days": 30,
  "users": [
    {
      "tenant_id": "user123",
      "api_key": "sc-user123-abc...",
      "email": "user@example.com",
      "name": "John Doe",
      "plan": "pro",
      "usage_count": 5000,
      "created_at": "2024-01-01T10:00:00",
      "last_used_at": "2024-01-15T15:30:00",
      "total_requests": 5000,
      "total_cache_hits": 4000,
      "total_cache_misses": 1000,
      "cache_hit_ratio": 80.0,
      "total_tokens": 500000,
      "total_cost": 138.89
    },
    ...
  ]
}
```

---

### 6. List All Users
**GET** `/admin/users?api_key=<KEY>&limit=100&offset=0&search=<optional>`

List all users with pagination and search.

**Query Parameters:**
- `limit`: Number of users per page (1-1000)
- `offset`: Pagination offset
- `search`: Optional search term (email or name)

**Response:**
```json
{
  "total": 150,
  "limit": 100,
  "offset": 0,
  "users": [
    {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "created_at": "2024-01-01T10:00:00",
      "updated_at": "2024-01-15T15:30:00",
      "api_key_count": 2,
      "total_usage": 5000,
      "last_used_at": "2024-01-15T15:30:00"
    },
    ...
  ]
}
```

---

### 7. User Details
**GET** `/admin/users/{tenant_id}/details?api_key=<KEY>`

Get detailed information about a specific tenant/user.

**Response:**
```json
{
  "tenant_id": "user123",
  "api_key": "sc-user123-abc...",
  "email": "user@example.com",
  "name": "John Doe",
  "plan": "pro",
  "plan_expires_at": "2024-12-31T23:59:59",
  "is_active": true,
  "created_at": "2024-01-01T10:00:00",
  "last_used_at": "2024-01-15T15:30:00",
  "usage_count": 5000,
  "usage_stats_30d": {
    "total_requests": 5000,
    "total_hits": 4000,
    "total_misses": 1000,
    "total_tokens": 500000,
    "total_cost": 138.89
  },
  "cache_stats": {
    "tenant": "user123",
    "requests": 5000,
    "hits": 4000,
    "semantic_hits": 3500,
    "misses": 1000,
    "hit_ratio": 0.8,
    "semantic_hit_ratio": 0.7,
    "avg_latency_ms": 150.5,
    "sim_threshold": 0.72,
    "entries": 450
  },
  "recent_activity": [
    {
      "endpoint": "/v1/chat/completions",
      "requests": 4500,
      "hits": 3600,
      "misses": 900,
      "tokens": 450000,
      "cost": 125.00
    },
    ...
  ]
}
```

---

### 8. Update User Plan
**POST** `/admin/users/{tenant_id}/update-plan?api_key=<KEY>&plan=pro&expires_at=<optional>`

Update a user's subscription plan.

**Query Parameters:**
- `plan`: New plan name (e.g., "free", "pro", "enterprise")
- `expires_at`: Optional expiration date (ISO format)

**Response:**
```json
{
  "success": true,
  "message": "Plan updated to pro for tenant user123"
}
```

---

### 9. Deactivate User
**POST** `/admin/users/{tenant_id}/deactivate?api_key=<KEY>`

Deactivate a user's API key.

**Response:**
```json
{
  "success": true,
  "message": "API key deactivated for tenant user123"
}
```

---

### 10. System Statistics
**GET** `/admin/system/stats?api_key=<KEY>`

Get system-wide statistics.

**Response:**
```json
{
  "cache": {
    "total_tenants": 175,
    "total_cache_entries": 12500,
    "avg_entries_per_tenant": 71.43
  },
  "database": {
    "total_users": 150,
    "active_api_keys": 175
  },
  "daily_usage": {
    "requests_24h": 1500,
    "cache_hits_24h": 1200,
    "cache_misses_24h": 300
  }
}
```

---

## Frontend Requirements

### Dashboard Layout

Create a modern, professional admin dashboard with the following sections:

#### 1. **Overview Dashboard (Main Page)**

**Cards/Widgets:**
- Total Users (large card with trend arrow)
- Active Users (large card with trend arrow)
- Total Requests (large card with trend arrow)
- Cache Hit Ratio (large card with percentage)
- Total Revenue/Cost (large card with currency)
- Active API Keys (medium card)

**Charts:**
- **User Growth Chart**: Line chart showing daily/weekly/monthly user growth (use `/admin/analytics/user-growth`)
  - X-axis: Date
  - Y-axis: Count
  - Multiple lines: New Users, New API Keys, Total Users
  - Toggle buttons: Daily / Weekly / Monthly
  
- **Usage Trends Chart**: Line chart showing requests over time (use `/admin/analytics/usage-trends`)
  - X-axis: Date
  - Y-axis: Requests
  - Show cache hits vs misses as stacked area or dual lines
  - Toggle buttons: Daily / Weekly / Monthly

- **Plan Distribution Chart**: Donut/Pie chart (use `/admin/analytics/plan-distribution`)
  - Show distribution of plans (free, pro, enterprise)
  - Display count and percentage
  - Color-coded segments

- **Revenue by Plan Chart**: Bar chart (from plan distribution)
  - X-axis: Plan name
  - Y-axis: Revenue/Cost
  - Stacked or grouped bars

#### 2. **Users Page**

**Table:**
- List all users with columns:
  - Email
  - Name
  - Plan
  - API Key Count
  - Total Usage
  - Last Used
  - Created Date
  - Actions (View Details, Update Plan, Deactivate)

**Features:**
- Pagination
- Search by email/name
- Sort by columns
- Filter by plan
- Click on user to view details

#### 3. **User Details Modal/Page**

When clicking on a user, show detailed information:
- User Information (email, name, plan, status)
- Usage Statistics (30-day stats)
- Cache Statistics (hit ratio, entries, latency)
- Recent Activity (by endpoint)
- Actions: Update Plan, Deactivate

#### 4. **Top Users Page**

**Table:**
- Top users by usage
- Columns: Email, Plan, Usage Count, Requests, Cache Hits, Cost, Last Used
- Sortable: Usage Count, Requests, Cost
- Filter by time period (7, 30, 90 days)

#### 5. **Analytics Page**

**Tabs/Sections:**
- **Growth Analytics**: User growth charts with period toggles
- **Usage Analytics**: Usage trends with period toggles
- **Plan Analytics**: Plan distribution and revenue
- **Performance Analytics**: Cache hit ratios, latency trends

**Features:**
- Date range picker (default: last 30 days)
- Period toggle (Daily / Weekly / Monthly)
- Export data as CSV/JSON
- Real-time refresh option

#### 6. **Settings/System Page**

**System Health:**
- Cache Statistics (tenants, entries, avg entries)
- Database Statistics (users, active keys)
- Daily Usage (requests, hits, misses)
- System Resource Usage (if available)

**Admin Settings:**
- Change admin API key (if needed)
- System configuration

---

## Design Requirements

### UI/UX:
- **Modern Design**: Clean, professional admin dashboard aesthetic
- **Color Scheme**: 
  - Primary: Blue/Purple (professional)
  - Success: Green
  - Warning: Orange
  - Error: Red
  - Neutral: Gray
- **Responsive**: Works on desktop, tablet, and mobile
- **Dark Mode**: Optional dark theme toggle
- **Loading States**: Show loading spinners/skeletons while fetching data
- **Error Handling**: Display error messages for failed API calls
- **Empty States**: Friendly messages when no data available

### Components Needed:
1. **Navigation**: Sidebar or top nav with menu items
   - Dashboard (Overview)
   - Users
   - Analytics
   - Top Users
   - Settings

2. **Charts Library**: Use Chart.js, Recharts, or similar
   - Line charts
   - Bar charts
   - Pie/Donut charts
   - Area charts

3. **Data Tables**: Sortable, paginated tables
   - Search functionality
   - Filter options
   - Export capabilities

4. **Modal/Dialog**: For user details and actions

5. **Cards/Widgets**: For displaying summary statistics

6. **Date Range Picker**: For filtering analytics

### Features:
- **Real-time Updates**: Auto-refresh every 30-60 seconds (optional)
- **Export**: Export tables and charts as CSV/PDF
- **Search & Filter**: Search users, filter by plan/date
- **Responsive Tables**: Scrollable on mobile
- **Toast Notifications**: Success/error messages for actions

---

## Technical Stack (Suggested)

- **Framework**: React with TypeScript (or Next.js)
- **UI Library**: 
  - Tailwind CSS + shadcn/ui (recommended)
  - OR Material-UI
  - OR Ant Design
- **Charts**: 
  - Recharts (React-friendly)
  - OR Chart.js with react-chartjs-2
  - OR ApexCharts
- **HTTP Client**: Axios or fetch
- **State Management**: React Query / SWR (for data fetching and caching)
- **Icons**: Lucide React or Heroicons

---

## API Configuration

**Environment Variables:**
```javascript
const API_BASE_URL = "http://localhost:8000";
const ADMIN_API_KEY = "admin-secret-key-change-me"; // From backend .env
```

**API Client Setup:**
```javascript
// Example Axios setup
import axios from 'axios';

const adminApi = axios.create({
  baseURL: 'http://localhost:8000/admin',
  params: {
    api_key: process.env.REACT_APP_ADMIN_API_KEY || 'admin-secret-key-change-me'
  }
});
```

---

## Page Routes

1. `/` - Dashboard Overview
2. `/users` - Users List
3. `/users/:tenantId` - User Details
4. `/analytics` - Analytics Page
5. `/top-users` - Top Users
6. `/settings` - System Settings

---

## Data Fetching Pattern

**Example API Call:**
```javascript
// Fetch analytics summary
const fetchAnalyticsSummary = async (days = 30) => {
  const response = await fetch(
    `${API_BASE_URL}/admin/analytics/summary?api_key=${ADMIN_API_KEY}&days=${days}`
  );
  return response.json();
};
```

---

## Key Features to Implement

1. **Dashboard Overview**
   - Display all key metrics at a glance
   - Quick links to detailed pages
   - Real-time or near-real-time updates

2. **User Management**
   - Browse all users
   - Search and filter
   - View detailed user information
   - Update user plans
   - Deactivate users

3. **Analytics & Reporting**
   - Visual charts and graphs
   - Time period selection
   - Export capabilities
   - Trend analysis

4. **Business Insights**
   - Growth metrics
   - Plan distribution
   - Revenue tracking
   - Usage patterns

5. **System Monitoring**
   - Cache statistics
   - Database health
   - Daily usage metrics

---

## Notes for Bolt AI

1. **Authentication**: All API calls require `api_key` query parameter
2. **Error Handling**: Handle 401 (unauthorized), 404 (not found), 500 (server error)
3. **Loading States**: Show loading indicators for all async operations
4. **Data Formatting**: 
   - Format numbers with commas (1,500)
   - Format currency ($1,250.50)
   - Format dates (Jan 15, 2024)
   - Format percentages (80.0%)
5. **Responsive Design**: Ensure all pages work on mobile devices
6. **Accessibility**: Use semantic HTML and ARIA labels
7. **Performance**: Optimize chart rendering, use pagination for large tables

---

**Start building the admin dashboard frontend in the `frontend/` folder, ensuring it connects to all the above API endpoints and provides a comprehensive view of the application's analytics, users, and system health.**


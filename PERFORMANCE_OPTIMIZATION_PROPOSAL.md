# Performance Optimization Proposal
## Issue: Dashboard Slow When Processing Complaints

---

## 🔍 Problem Analysis

### Current Situation
When complaints are being processed in the background (with document analysis via VLLM/LLM), the officer dashboard becomes **very slow** to load.

### Root Causes Identified

#### 1. **Database Connection Pool Bottleneck** ⚠️ CRITICAL
```python
# src/database.py (Line 36-38)
self.pool = SimpleConnectionPool(
    minconn=1,
    maxconn=10,  # ❌ ONLY 10 CONNECTIONS!
```

**Problem:**
- Total available connections: **10**
- Background workers: **5 concurrent complaint processors**
- Each background worker may hold 1-2 connections during processing
- Dashboard queries need connections but have to **wait in line**

**Math:**
```
Total connections: 10
Background tasks using: ~3-5 connections (at any moment)
Available for dashboard: 5-7 connections
```

When multiple officers access the dashboard simultaneously while complaints are processing, they compete for the remaining connections.

---

#### 2. **ThreadPoolExecutor Configuration**
```python
# src/main.py (Line 70)
executor = ThreadPoolExecutor(max_workers=5)  # 5 concurrent processors
```

**Problem:**
- Allows 5 complaints to process simultaneously
- Each takes 10-30 seconds (LLM API calls are SLOW)
- These threads are not async, so they block resources

---

#### 3. **No Request Prioritization**
- Background tasks (complaint processing) and user requests (dashboard) are treated equally
- No way to prioritize officer dashboard queries over background processing

---

#### 4. **Long-Running Processing Pipeline**
Each complaint processing involves:
1. ✅ Read from database (fast - ~10ms)
2. ❌ VLLM extraction (SLOW - 5-10 seconds)
3. ❌ Classification (SLOW - 3-5 seconds)
4. ❌ Sector determination (SLOW - 3-5 seconds)
5. ❌ Akta generation (SLOW - 3-5 seconds)
6. ❌ Summary generation (SLOW - 3-5 seconds)
7. ❌ Embedding generation (FAST - ~500ms)
8. ❌ Auto-grouping into cases (MEDIUM - 1-2 seconds)
9. ✅ Update database (fast - ~50ms)

**Total time per complaint: 20-35 seconds**

While LLM API calls don't hold database connections, the ThreadPoolExecutor threads occupy resources.

---

## 💡 Solutions (Ranked by Impact)

### Solution 1: Increase Database Connection Pool ⭐⭐⭐⭐⭐
**Impact:** HIGH | **Effort:** LOW | **Risk:** LOW

#### Implementation
```python
# src/database.py
self.pool = SimpleConnectionPool(
    minconn=5,      # Increase minimum connections
    maxconn=50,     # 🔥 Increase to 50 connections
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)
```

#### Why 50?
```
Background workers: 5 × 2 connections = 10 connections
Dashboard queries: 10 concurrent officers × 2 connections = 20 connections
Audit logs: 5 connections
Buffer: 15 connections
Total: 50 connections
```

#### PostgreSQL Configuration
Check your PostgreSQL's `max_connections`:
```bash
psql -U postgres -c "SHOW max_connections;"
# Default is usually 100

# If needed, increase in postgresql.conf:
# max_connections = 200
```

#### ✅ Benefits
- Immediate improvement
- Minimal code changes
- Low risk

#### ⚠️ Considerations
- PostgreSQL must support the connection count
- More memory usage (each connection ~10MB)

---

### Solution 2: Reduce Background Worker Concurrency ⭐⭐⭐⭐
**Impact:** HIGH | **Effort:** LOW | **Risk:** LOW

#### Implementation
```python
# src/main.py
# Change from 5 to 2 concurrent workers
executor = ThreadPoolExecutor(max_workers=2)  # 🔥 Reduce to 2
```

#### Trade-offs
**Pros:**
- ✅ Less resource contention
- ✅ More connections available for dashboard
- ✅ Lower server load

**Cons:**
- ❌ Slower complaint processing throughput
- ❌ Queue builds up if many complaints submitted

#### When to Use
- If you don't receive many complaints simultaneously (< 10 per hour)
- If processing speed is less important than dashboard responsiveness

---

### Solution 3: Implement Connection Pool Per Service ⭐⭐⭐
**Impact:** MEDIUM | **Effort:** MEDIUM | **Risk:** MEDIUM

#### Implementation
Create separate connection pools:

```python
# src/database.py
class Database:
    def __init__(self):
        # Main pool for user requests (priority)
        self.main_pool = SimpleConnectionPool(
            minconn=5,
            maxconn=30,  # Priority pool
            ...
        )

        # Background pool for processing tasks
        self.background_pool = SimpleConnectionPool(
            minconn=2,
            maxconn=10,  # Limited pool
            ...
        )

    def get_connection(self, priority='main'):
        pool = self.main_pool if priority == 'main' else self.background_pool
        return pool.getconn()
```

Then modify complaint processing to use background pool:
```python
# In background tasks
with db.get_connection(priority='background') as conn:
    ...
```

#### ✅ Benefits
- Dashboard gets guaranteed connections
- Background tasks can't starve dashboard

#### ⚠️ Drawbacks
- More complex code
- Need to refactor many database calls

---

### Solution 4: Use Redis/Queue for Background Processing ⭐⭐⭐⭐⭐
**Impact:** VERY HIGH | **Effort:** HIGH | **Risk:** MEDIUM

#### Architecture
```
┌────────────┐        ┌─────────┐        ┌──────────────┐
│  FastAPI   │──────▶ │  Redis  │──────▶ │ Celery Worker│
│  (Main)    │        │  Queue  │        │ (Background) │
└────────────┘        └─────────┘        └──────────────┘
     │                                            │
     │                                            │
     └──────────────▶ PostgreSQL ◀───────────────┘
           (Main Pool)            (Separate Pool)
```

#### Implementation Steps

**1. Install Celery + Redis**
```bash
pip install celery redis
```

**2. Create Celery App**
```python
# src/celery_app.py
from celery import Celery
import os

celery_app = Celery(
    'sprm_tasks',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0')
)

celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='Asia/Kuala_Lumpur',
    enable_utc=True,
)
```

**3. Create Background Task**
```python
# src/tasks.py
from celery_app import celery_app
from complaint_service import ComplaintService

@celery_app.task(name='process_complaint')
def process_complaint_task(complaint_id: int):
    """Process complaint in background via Celery"""
    service = ComplaintService()
    return service.process_complaint_new(complaint_id)
```

**4. Modify Main App**
```python
# src/main.py
from tasks import process_complaint_task

@app.post("/complaints/submit", response_model=ComplaintResponse)
async def submit_complaint(...):
    # Save complaint
    complaint_id = service.save_complaint(complaint_data)

    # Queue for background processing (non-blocking!)
    process_complaint_task.delay(complaint_id)  # 🔥 Async queue

    return ComplaintResponse(...)
```

**5. Run Celery Worker**
```bash
# Start Celery worker (separate process)
celery -A celery_app worker --loglevel=info --concurrency=2
```

#### ✅ Benefits
- ✅ **Complete isolation** of background tasks
- ✅ Separate database pool for workers
- ✅ Can scale workers independently
- ✅ Task monitoring and retry logic
- ✅ Dashboard never blocked

#### ⚠️ Drawbacks
- Requires Redis server
- More infrastructure complexity
- Deployment changes needed

---

### Solution 5: Add Database Query Optimization ⭐⭐⭐
**Impact:** MEDIUM | **Effort:** LOW | **Risk:** LOW

#### Current Dashboard Query
The dashboard uses pre-computed analytics tables, which is good! But we can optimize further:

```python
# src/simple_analytics.py
def get_simple_analytics():
    """Get pre-computed analytics"""
    # Currently makes 4 separate queries:
    # 1. Summary
    # 2. Top entities (LIMIT 50)
    # 3. Sectors
    # 4. Patterns
```

#### Optimization: Add Indexes
```sql
-- Add these indexes if not exist
CREATE INDEX IF NOT EXISTS idx_analytics_entities_type_count
    ON analytics_entities(entity_type, count DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_sectors_count
    ON analytics_sectors(complaint_count DESC);

CREATE INDEX IF NOT EXISTS idx_analytics_patterns_count
    ON analytics_patterns(count DESC);
```

#### Optimization: Use Single Query with UNION
```python
def get_simple_analytics_optimized():
    """Optimized version using fewer queries"""
    with db.get_cursor() as cursor:
        # Get everything in ONE query
        cursor.execute("""
            -- Summary
            SELECT 'summary' as type, row_to_json(s.*) as data
            FROM analytics_summary s WHERE id = 1

            UNION ALL

            -- Top entities
            SELECT 'entities' as type, json_agg(row_to_json(e.*)) as data
            FROM (
                SELECT entity_type, entity_value, count
                FROM analytics_entities
                ORDER BY count DESC
                LIMIT 50
            ) e

            -- ... similar for sectors and patterns
        """)
```

---

### Solution 6: Implement Request Timeout for Background Tasks ⭐⭐
**Impact:** LOW | **Effort:** LOW | **Risk:** LOW

#### Implementation
Set timeout for LLM API calls:
```python
# src/openrouter_service.py
class OpenRouterService:
    def call_api(self, ...):
        response = requests.post(
            self.api_url,
            headers=headers,
            json=payload,
            timeout=15  # 🔥 Add timeout (15 seconds max)
        )
```

#### ✅ Benefits
- Prevents stuck workers
- Failed requests fail fast
- More predictable resource usage

---

## 🎯 Recommended Implementation Plan

### Phase 1: Quick Wins (1 hour) ⚡
**Do these immediately:**

1. ✅ **Increase database connection pool to 50** (Solution 1)
   ```python
   maxconn=50  # in src/database.py
   ```

2. ✅ **Reduce background workers to 2** (Solution 2)
   ```python
   max_workers=2  # in src/main.py
   ```

3. ✅ **Add LLM API timeout** (Solution 6)
   ```python
   timeout=15  # in openrouter_service.py
   ```

**Expected Result:** Dashboard should be 70-80% faster

---

### Phase 2: Medium-term (1-2 days) 📊
**After testing Phase 1:**

4. ✅ **Add database indexes** (Solution 5)
5. ✅ **Monitor connection pool usage**
   ```python
   # Add monitoring endpoint
   @app.get("/admin/db-pool-status")
   def get_pool_status():
       return {
           "size": db.pool._used if db.pool else 0,
           "available": db.pool._maxconn - len(db.pool._used)
       }
   ```

---

### Phase 3: Long-term (1-2 weeks) 🚀
**For production scalability:**

6. ✅ **Implement Celery + Redis** (Solution 4)
7. ✅ **Separate connection pools** (Solution 3)

---

## 📊 Testing & Monitoring

### Before Changes
**Measure baseline:**
```bash
# Measure dashboard load time
time curl http://localhost:8000/analytics/dashboard

# Check active connections
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity WHERE datname = 'sprm_db';"
```

### After Changes
**Compare improvements:**
```bash
# Should be faster
time curl http://localhost:8000/analytics/dashboard

# Check connection usage
curl http://localhost:8000/admin/db-pool-status
```

### Load Testing (Optional)
```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test dashboard under load
ab -n 100 -c 10 http://localhost:8000/analytics/dashboard

# Results should show:
# - Faster response time
# - No failed requests
```

---

## 🔧 Quick Fix Code Changes

### File 1: `src/database.py`
```python
# Line 36-38
self.pool = SimpleConnectionPool(
    minconn=5,      # 🔥 Changed from 1
    maxconn=50,     # 🔥 Changed from 10
    host=db_host,
    port=db_port,
    database=db_name,
    user=db_user,
    password=db_password
)
```

### File 2: `src/main.py`
```python
# Line 70
executor = ThreadPoolExecutor(max_workers=2)  # 🔥 Changed from 5
```

### File 3: `src/openrouter_service.py`
Find all `requests.post()` calls and add:
```python
timeout=15  # 🔥 Add 15-second timeout
```

---

## ✅ Summary

| Solution | Impact | Effort | Priority |
|----------|--------|--------|----------|
| Increase DB pool (10→50) | ⭐⭐⭐⭐⭐ | 2 min | 🔴 DO NOW |
| Reduce workers (5→2) | ⭐⭐⭐⭐ | 1 min | 🔴 DO NOW |
| Add API timeout | ⭐⭐ | 5 min | 🔴 DO NOW |
| Add DB indexes | ⭐⭐⭐ | 10 min | 🟡 SOON |
| Celery + Redis | ⭐⭐⭐⭐⭐ | 1 day | 🟢 LATER |
| Separate pools | ⭐⭐⭐ | 2 hours | 🟢 LATER |

---

## 🤔 Which Solution Should You Choose?

### If you want QUICK fix (5 minutes):
✅ Solution 1 + 2: Increase pool + reduce workers

### If you want BEST fix (1 day):
✅ Solution 4: Celery + Redis (production-ready)

### If you want BALANCED (1 hour):
✅ Solution 1 + 2 + 5: Pool + workers + indexes

---

Let me know which approach you'd like to take, and I can implement it for you! 🚀

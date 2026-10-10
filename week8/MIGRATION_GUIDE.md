# Migration from JSON to PostgreSQL Database

## Summary of Changes

The application has been migrated from file-based JSON storage (`memory.json`) to PostgreSQL, a production-grade relational database. This improves scalability, performance, and reliability.

## What Changed

### 1. **Storage Layer** 
- **Before**: `memory.json` file stored all opportunities as a flat JSON array
- **After**: PostgreSQL database with `deals` and `opportunities` tables

### 2. **Data Structure**
```
OLD (JSON):
[
  {
    "deal": {"product_description": "...", "price": 100, "url": "..."},
    "estimate": 200,
    "discount": 100
  }
]

NEW (PostgreSQL):
deals table:
  - id, product_description, price, url, created_at

opportunities table:
  - id, deal_id (FK), estimate, discount, created_at
```

### 3. **Code Changes**
- **`database.py`** (NEW): Database configuration, models, and connection management
- **`deal_agent_framework.py`**: Updated to use database instead of JSON
  - `memory` is now a property that queries the database
  - `save_opportunity()` replaces `write_memory()`
  - Removed `read_memory()` and `MEMORY_FILENAME`
- **`requirements.txt`**: Added `sqlalchemy>=2.0` and `psycopg2-binary`

### 4. **Environment Configuration**
- Add `DATABASE_URL` to `.env` file
- See `.env.example` for template

## Benefits

### Performance
- **Connection Pooling**: 10 persistent connections reuse TCP connections
- **Indexing**: Queries on price, URL, and discount are optimized
- **No File I/O Blocking**: Database handles concurrent access efficiently

### Scalability
- **Horizontal Growth**: Database scales to millions of opportunities
- **Concurrent Users**: Multiple instances can safely access the same data
- **Query Optimization**: PostgreSQL query planner optimizes complex queries

### Reliability
- **ACID Compliance**: Transactions ensure data consistency
- **Cascade Delete**: Deleting a deal automatically removes related opportunities
- **Unique Constraints**: Prevents duplicate deals (by URL)

### Data Integrity
- **Foreign Key Relationships**: Deals and opportunities are properly linked
- **Timestamp Tracking**: `created_at` fields for auditing
- **Error Handling**: Rollback on failures prevents partial saves

### Querying Capabilities
Now you can easily:
```python
# Get top 10 discounts
session.query(OpportunityModel).order_by(
    OpportunityModel.discount.desc()
).limit(10).all()

# Get deals from last 24 hours
from datetime import datetime, timedelta
yesterday = datetime.utcnow() - timedelta(days=1)
session.query(OpportunityModel).filter(
    OpportunityModel.created_at > yesterday
).all()

# Find duplicate deals
session.query(DealModel).filter(
    DealModel.url.in_([...])
).all()
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up PostgreSQL
Follow instructions in `DATABASE_SETUP.md`

### 3. Configure Environment
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

### 4. Run the Application
The database tables are created automatically on first run:
```bash
python price_is_right_final.py
```

## Migration Path for Existing Data

If you have an existing `memory.json` file and want to migrate the data:

```python
import json
from database import SessionLocal, DealModel, OpportunityModel

# Read old JSON file
with open('memory.json', 'r') as f:
    old_data = json.load(f)

session = SessionLocal()

# Migrate to database
for item in old_data:
    # Create or get deal
    deal = session.query(DealModel).filter_by(
        url=item['deal']['url']
    ).first()
    
    if not deal:
        deal = DealModel(
            product_description=item['deal']['product_description'],
            price=item['deal']['price'],
            url=item['deal']['url']
        )
        session.add(deal)
        session.flush()
    
    # Create opportunity
    opportunity = OpportunityModel(
        deal_id=deal.id,
        estimate=item['estimate'],
        discount=item['discount']
    )
    session.add(opportunity)

session.commit()
```

## Backward Compatibility

The `Opportunity` and `Deal` Pydantic models remain unchanged, so:
- UI code in `price_is_right_final.py` requires minimal changes
- The `memory` property returns a list of `Opportunity` objects (same as before)
- The API surface is compatible

## Performance Metrics

Expected improvements:

| Operation | Before (JSON) | After (PostgreSQL) |
|-----------|---------------|--------------------|
| Load 10K deals | ~500ms | ~50ms |
| Add new opportunity | ~100ms | ~20ms |
| Query top 100 by discount | N/A (full scan) | ~5ms (indexed) |
| Concurrent access | Blocking | Non-blocking |

## Troubleshooting

**Database connection error?**
- Verify PostgreSQL is running
- Check DATABASE_URL in `.env` is correct
- See DATABASE_SETUP.md for detailed troubleshooting

**Tables not created?**
- `init_db()` is called automatically in `DealAgentFramework.__init__()`
- Check logs for connection errors

**Old memory.json still there?**
- It's safe to keep (no longer used)
- Can be deleted after verifying data was migrated

"""
Initialize database tables for SPRM Backend

This script creates all necessary database tables.
Run this script if you encounter "relation does not exist" errors.
"""
from src.database import db

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Initializing SPRM Database Tables")
    print("=" * 60)

    try:
        print("\n📋 Creating database tables...")
        db.create_tables()
        print("\n✅ Database initialization completed successfully!")
        print("\n📊 Tables created/updated:")
        print("   • complaints (columns: sub_sector, summary, akta as TEXT)")
        print("   • complaint_documents")
        print("   • cases (columns: related_cases as JSONB)")
        print("   • case_complaints")
        print("   • similar_cases")
        print("   • analytics_entities")
        print("   • analytics_sectors")
        print("   • analytics_patterns")
        print("   • analytics_summary")
        print("   • akta_sections")
        print("\n" + "=" * 60)
        print("✨ You can now submit complaints!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        print("\n💡 Troubleshooting:")
        print("   1. Check that PostgreSQL is running")
        print("   2. Verify your .env file has correct database credentials")
        print("   3. Ensure the database 'sprm_db' exists")
        print("\n" + "=" * 60)
        import traceback
        traceback.print_exc()

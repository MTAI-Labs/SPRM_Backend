#!/usr/bin/env python3
"""
Create the missing generated_letters table
"""
from src.database import db

print("🔧 Creating generated_letters table...")
try:
    db.create_tables()
    print("✅ Success! The generated_letters table has been created.")
    print("\n📝 Verifying table exists...")

    # Verify the table was created
    with db.get_cursor() as cursor:
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'generated_letters'
        """)
        result = cursor.fetchone()

        if result:
            print(f"✅ Table 'generated_letters' exists in database!")

            # Show table structure
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'generated_letters'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()

            print("\n📊 Table structure:")
            print("-" * 60)
            for col in columns:
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"  {col['column_name']:<20} {col['data_type']:<20} {nullable}")
            print("-" * 60)

        else:
            print("❌ Table not found! Something went wrong.")

except Exception as e:
    print(f"❌ Error: {e}")
    raise

import sqlite3

for db in ['seamark_inventory.db', 'dashboard/seamark_inventory.db']:
    try:
        conn = sqlite3.connect(db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\nDatabase: {db}")
        print(f"Tables: {tables}")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            print(f"  {table[0]}: {cursor.fetchone()[0]} rows")
            cursor.execute(f"PRAGMA table_info({table[0]})")
            cols = [row[1] for row in cursor.fetchall()]
            print(f"  Columns: {cols}")
        conn.close()
    except Exception as e:
        print(f"Error with {db}: {e}")


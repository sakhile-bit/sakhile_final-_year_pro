"""
Test MySQL connection with provided credentials
"""

import mysql.connector
from mysql.connector import Error

# Connection credentials
config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'stanford',
    'password': '0987654321',
    'database': 'digital_hygiene'
}

try:
    # Establish connection
    print("🔄 Attempting to connect to MySQL...")
    connection = mysql.connector.connect(**config)
    
    if connection.is_connected():
        print("✓ Successfully connected to MySQL!")
        
        # Get database info
        db_info = connection.get_server_info()
        print(f"✓ MySQL Server version: {db_info}")
        
        # Create cursor and test query
        cursor = connection.cursor()
        cursor.execute("SELECT DATABASE();")
        current_db = cursor.fetchone()
        print(f"✓ Current database: {current_db[0]}")
        
        # Check tables
        cursor.execute("""
            SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = 'digital_hygiene'
        """)
        tables = cursor.fetchall()
        print(f"\n✓ Tables in database ({len(tables)}):")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"  - {table[0]}: {count} rows")
        
        cursor.close()
        connection.close()
        print("\n✓ Connection test successful! Ready to use in Flask app.")
        
except Error as e:
    print(f"❌ Error connecting to MySQL:")
    print(f"   {e}")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected error:")
    print(f"   {e}")
    exit(1)

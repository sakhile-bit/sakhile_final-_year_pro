try:
    import mysql.connector
    print('✓ mysql.connector is installed')
except ImportError as e:
    print(f'❌ mysql.connector NOT installed: {e}')

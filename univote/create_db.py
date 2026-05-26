import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5433,
        user='postgres',
        password='password2006',
        dbname='postgres'
    )
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'univote_db'")
    exists = cur.fetchone()

    if not exists:
        cur.execute('CREATE DATABASE univote_db')
        print('SUCCESS: Database univote_db created!')
    else:
        print('OK: Database univote_db already exists.')

    cur.close()
    conn.close()
except Exception as e:
    print(f'ERROR: {e}')

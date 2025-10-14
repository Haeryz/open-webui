import sqlite3
import json

db_path = "/app/backend/data/webui.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT data FROM config")
result = cursor.fetchone()

if result:
    data = json.loads(result[0])
    system_prompt = data.get('ui', {}).get('default_system_prompt', 'NOT FOUND')
    print("=" * 80)
    print("System prompt from database (first 300 chars):")
    print(system_prompt[:300] if system_prompt else "EMPTY")
    print("=" * 80)
else:
    print("No config entry found in database")

conn.close()

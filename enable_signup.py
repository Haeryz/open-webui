import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
cursor = conn.cursor()

# Get current config
cursor.execute("SELECT id, data FROM config WHERE id = 1")
row = cursor.fetchone()

if row:
    config_id, config_data = row
    config = json.loads(config_data)
    
    # Enable signup
    if 'ui' not in config:
        config['ui'] = {}
    config['ui']['enable_signup'] = True
    
    # Update database
    cursor.execute("UPDATE config SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", 
                   (json.dumps(config), config_id))
    conn.commit()
    
    print("✓ Signup enabled successfully!")
    print(f"Current config: {config}")
else:
    print("No config found")

conn.close()

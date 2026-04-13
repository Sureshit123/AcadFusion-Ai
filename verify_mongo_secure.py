import os
from pymongo import MongoClient
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()

MONGO_URI = os.environ.get('MONGO_URI')

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['vtu_analyzer']
    coll = db['users']
    
    # Let's check what's currently in the DB
    users = list(coll.find())
    print(f"Number of users: {len(users)}")
    
    for u in users:
        pwd = u.get('password')
        is_hashed = pwd.startswith('pbkdf2:sha256') or pwd.startswith('scrypt')
        print(f"User: {u.get('username')}")
        print(f" - Password is hashed: {is_hashed}")
        if not is_hashed:
            print(f" - WARNING: Password '{pwd}' is still in plain text!")
        else:
            print(f" - Secure Hash: {pwd[:20]}...")

except Exception as e:
    print(f"Error: {e}")

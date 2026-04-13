import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ.get('MONGO_URI')
print(f"Testing connection to: {MONGO_URI.split('@')[-1]}") # Hide credentials

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    # Trigger a command to check connection
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
    
    db = client['vtu_analyzer']
    coll = db['users']
    
    count = coll.count_documents({})
    print(f"Number of users in 'vtu_analyzer.users': {count}")
    
    if count > 0:
        print("Users found:")
        for user in coll.find():
            print(f" - {user.get('username')}")
    else:
        print("No users found in the database yet.")

except Exception as e:
    print(f"Connection failed: {e}")

import os
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        self.mongo_uri = os.environ.get('MONGO_URI', 'mongodb://127.0.0.1:27017/')
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.db = self.client['vtu_analyzer']
            self.users = self.db['users']
            self.schedules = self.db['schedules']
            self.teachers = self.db['teachers']
            # Ping
            self.client.admin.command('ping')
            print("Successfully connected to MongoDB.")
        except Exception as e:
            print(f"MongoDB Connection Error: {e}")
            self.users = None

    def get_user_by_email(self, email):
        if self.users is None: return None
        return self.users.find_one({'email': email})

    def create_user(self, name, email, password):
        if self.users is None: return False
        hashed_pw = generate_password_hash(password)
        try:
            self.users.insert_one({
                'name': name,
                'email': email,
                'password_hash': hashed_pw
            })
            return True
        except Exception as e:
            print(f"Create User Error: {e}")
            return False

    def verify_user(self, email, password):
        user = self.get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None

    def save_timetable(self, semester, timetable_data, creator_email):
        try:
            self.schedules.update_one(
                {'semester': semester},
                {'$set': {
                    'data': timetable_data,
                    'created_by': creator_email,
                    'last_updated': os.times()
                }},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Save Timetable Error: {e}")
            return False

    def get_teacher_schedule(self, teacher_name):
        teacher = self.teachers.find_one({'name': teacher_name})
        return teacher['busy_slots'] if teacher else []

    def update_teacher_schedule(self, teacher_name, new_slots):
        self.teachers.update_one(
            {'name': teacher_name},
            {'$set': {'busy_slots': new_slots}},
            upsert=True
        )

    def get_department_resources(self, user_id):
        config = self.db['config'].find_one({'key': 'department_resources', 'user_id': user_id})
        if not config: return {'teachers': [], 'lab_rooms': 3}
        return {
            'teachers': config.get('teachers', []),
            'lab_rooms': config.get('lab_rooms', 3)
        }

    def update_department_resources(self, user_id, lab_rooms, teacher_list):
        self.db['config'].update_one(
            {'key': 'department_resources', 'user_id': user_id},
            {'$set': {
                'lab_rooms': lab_rooms,
                'teachers': teacher_list
            }},
            upsert=True
        )

    def save_cycle(self, cycle_type, data, user_id):
        # s_type: 'odd' or 'even'
        self.db['cycles'].update_one(
            {'cycle_type': cycle_type, 'user_id': user_id},
            {'$set': {
                'data': data,
                'timestamp': os.times()
            }},
            upsert=True
        )


# Global database instance
db_instance = Database()

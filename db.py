from pymongo import MongoClient
from config import Config

client = MongoClient(Config.MONGO_URI)
db = client[Config.DATABASE_NAME]

# Collections
users_collection = db["users"]
questions_collection = db["questions"]
counters_collection = db["counters"]

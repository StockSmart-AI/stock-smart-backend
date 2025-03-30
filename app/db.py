# from pymongo import MongoClient
import os
import mongoengine as me
from dotenv import load_dotenv

load_dotenv()

me.connect(
    db=os.getenv("mongodb_database_name"),
    host=os.getenv("MONGO_URI")
    )

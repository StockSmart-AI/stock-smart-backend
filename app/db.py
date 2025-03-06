from pymongo import MongoClient
import os

mongo_client = MongoClient(os.getenv("MONGO_URI"), tls=True, tlsAllowInvalidCertificates=True)
db_name = os.getenv("mongodb_database_name")  # Get the database name from the environment variables
db = mongo_client[db_name]

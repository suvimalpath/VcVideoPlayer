import pymongo 
import os

DB_NAME = os.environ.get("DB_NAME","")
DB_URL = os.environ.get("DB_URL","")
mongo = pymongo.MongoClient(DB_URL)
db = mongo[DB_NAME]
dbcol = db["USER"]

def add_user(chat_id):
            user_id = int(chat_id)
            user_det = {"_id":user_id}
            try:
            	dbcol.insert_one(user_det)
            except:
            	pass 

def check_chat(id):
	user = dbcol.find_one({"_id":id})
	if user :
		return True
	else:
		return False

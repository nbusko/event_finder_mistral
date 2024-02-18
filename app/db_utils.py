import os
import json
import uuid
from motor.motor_asyncio import AsyncIOMotorClient
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

class MongoDB:
    def __init__(self, mongo_ip="mongodb://mongodb:27017/") -> None:
        self.client = AsyncIOMotorClient(mongo_ip)
        self.collection = self.client["events_db"]["main"]
    
    async def init_db(self, events_dir):
        docs_cnt = await self.collection.count_documents({})
        if docs_cnt > 0:
            raise Exception("DB is not empty")

        if not os.path.exists(events_dir):
            raise Exception(f"{events_dir} is not existing")

        self.event_dict = set()

        with open(f'{events_dir}') as json_file:
            self.event_dict = json.load(json_file)
        
        if not self.event_dict:
            raise Exception(f"Files are empty or corrupted")

        event_docs = [{"id": uuid.uuid4(), "event": event} for event in self.event_dict]
        result = await self.collection.insert_many(event_docs)

        if not result:
            raise Exception(f"Updating failed")

        return f"Inserted {len(result.inserted_ids)} dois"
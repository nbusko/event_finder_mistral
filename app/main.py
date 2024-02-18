from fastapi import FastAPI
import uvicorn
from db_utils import MongoDB
import os
from pprint import pprint

from router import router


app = FastAPI(
    title="ITMO_mega_school_task_3",
    version="0.0.1",
    docs_url="/docs",
    redoc_url="/docs/redoc",
)

mongo_login = os.getenv("MONGO_LOGIN", "root")
mongo_passwd = os.getenv("MONGO_PASSWD", "rpasswd")
try:
    app.include_router(router)
except Exception as e:
    pprint(e)
mongo_session = MongoDB(f"mongodb://{mongo_login}:{mongo_passwd}@localhost:27017/")

@app.on_event("startup")
async def init_events_db():
    try:
        await mongo_session.init_db(os.getenv("EVENTS_DIR"))
    except Exception as e:
        pprint(e)
        pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
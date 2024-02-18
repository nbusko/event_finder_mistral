from fastapi import FastAPI, Request, APIRouter
from AImanager import AImanager
from contracts import Data

router = APIRouter(tags=["task"])

ai_manager = AImanager()

@router.post("/process")
async def process(data: Data):
    string = data.string
    result = await ai_manager.process(string)
    return {"result": result}
from pydantic import BaseModel

class Data(BaseModel):
    string: str
    result: str = None
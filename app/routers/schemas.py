from pydantic import BaseModel

class Music_play(BaseModel):
    music : str
    author : str
    name : str
    genre : str

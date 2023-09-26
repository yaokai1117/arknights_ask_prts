from fastapi import FastAPI
from pydantic import BaseModel
from processor import Processor

class Message(BaseModel):
    content: str

app = FastAPI()

@app.get('/')
def read_root():
    return "It's working!"

@app.post('/message/')
async def post_message(message: Message):
    processor = Processor()
    return processor.process(message.content)

if __name__ ==  '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)

from fastapi import FastAPI
from processor import Processor
from data_model import AskPrtsRequest

app = FastAPI()

@app.get('/')
def read_root():
    return "It's working!"

@app.post('/ask/')
async def post_message(request: AskPrtsRequest):
    processor = Processor()
    return await processor.process(request.content)

if __name__ ==  '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=9888)

import os
from dotenv import load_dotenv  # nopep8
load_dotenv()  # nopep8

from fastapi import FastAPI
from processor import Processor
from data_model import AskPrtsRequest, AskPrtsReponse
from utils import start_session, save_session

PORT = int(os.getenv("CHAT_API_PORT"))

app = FastAPI()


@app.get('/')
def read_root():
    return "It's working!"


@app.post('/ask/')
async def post_message(request: AskPrtsRequest) -> AskPrtsReponse:
    log_entry = start_session(request.content, session_id=request.session_id)
    processor = Processor(log_entry)
    final_response = await processor.chain.ainvoke({Processor.INPUT_KEY: request.content})
    save_session(log_entry)
    return AskPrtsReponse(content=final_response, session_id=str(log_entry.session_id))

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=PORT)

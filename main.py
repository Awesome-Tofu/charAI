from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
from PyCharacterAI import Client
from pydantic import BaseModel
from pymongo import MongoClient
import uvicorn
import re
mongo_client = MongoClient('mongodb+srv://kazuha321:kazuha321@cluster0.oafdfob.mongodb.net/?retryWrites=true&w=majority')


app = FastAPI()


class Item(BaseModel):
    item_id: int

async def char_ai(token: str, character_id: str, unique_id: str, message: str) -> dict:
    db = mongo_client['char_ai']
    chat_collection = db['chats']

    client = Client()
    await client.authenticate_with_token(token)

    username = (await client.fetch_user())['user']['username']
    print(f'Authenticated as {username}')

    chat_doc = chat_collection.find_one({'unique_id': unique_id})

    if chat_doc is None:
        chat = await client.create_chat(character_id)
        history_id = chat.history_id
        chat_collection.insert_one({'unique_id': unique_id, 'history_id': history_id})
    else:
        chat = await client.create_or_continue_chat(character_id=character_id, history_id=chat_doc['history_id'])

    answer = await chat.send_message(message)
    resp = answer.text.replace(username, "human")
    resp = re.sub(r'gojo', 'human', resp, flags=re.IGNORECASE)
    ren = {
        "your_username": username,
        "character_name": answer.src_character_name,
        "reply": resp
    }
    return ren
    
@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')

@app.get(
    "/char_ai/{token}/{character_id}/{unique_id}/{message}", tags=["AI"], summary="Generate AI Images"
)
async def character_ai(token: str, character_id: str, unique_id: str, message: str):
    """
    token: your [token](https://pycai.gitbook.io/welcome/api/values#key-token)\n
    character_id: [character id](https://pycai.gitbook.io/welcome/api/values#char-char_external_id)\n
    message: prompt\n
    unique_id: unique id to save chat history for a particular user
    """

    output = await char_ai(token, character_id, unique_id, message)
    if output is not None:
        return output
    else:
        print(f"STATUS FALSE at output")
        raise HTTPException(status_code=404, detail="Something went wrong!")


@app.get("/items/")
async def list_items():
    return [{"item_id": 1, "name": "Foo"}, {"item_id": 2, "name": "Bar"}]


@app.post("/items/")
async def create_item(item: Item):
    return item

PORT = int(os.environ.get("PORT") or 8000)

if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=PORT, reload=True)


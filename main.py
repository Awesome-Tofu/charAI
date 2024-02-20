from fastapi import FastAPI, HTTPException, Response, Query
from pymongo import MongoClient
from PyCharacterAI import Client
import re
import uvicorn
import os

mongo_client = MongoClient('mongodb+srv://kazuha321:kazuha321@cluster0.oafdfob.mongodb.net/?retryWrites=true&w=majority')

app = FastAPI(
    title="Tofu API Documentation",
    version="1.0",
    description="Just my API collection",
    openapi_url="/api/v1/openapi.json",
    redoc_url="/api/v1/redoc",
    # docs_url=None,
    contact={
        "name": "Tofu",
        "email": "adityaraj6311@gmail.com",
        "url": "https://aditya-info.vercel.app/",
    },
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
)

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

PORT = int(os.environ.get("PORT") or 7000)

if __name__ == "__main__":
    uvicorn.run("new:app", host="localhost", port=PORT, reload=True)

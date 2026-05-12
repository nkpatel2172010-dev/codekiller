from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from database import get_db
import litellm
import json
from datetime import datetime

router = APIRouter()

SYSTEM_PROMPT = """You are CodeKILLER AI — the ultimate elite coding assistant.
Always write clean, production-ready, well-commented code with modern best practices (2026). 
Think step by step and explain your decisions."""

@router.post("/chat")
async def chat_completions(request: Request, db=Depends(get_db)):
    body = await request.json()
    messages = body.get("messages", [])
    model = body.get("model", "codemind-ai")
    chat_id = body.get("chat_id")

    if chat_id:
        chat = await db.chats.find_one({"id": chat_id})
        if not chat:
            raise HTTPException(404, "Chat not found")
    else:
        chat = {
            "id": str(datetime.utcnow().timestamp()),
            "title": "New Chat",
            "messages": [],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        await db.chats.insert_one(chat)

    # Save user message
    user_msg = messages[-1]
    await db.chats.update_one(
        {"id": chat["id"]},
        {"$push": {"messages": user_msg}, "$set": {"updated_at": datetime.utcnow()}}
    )

    async def generate():
        try:
            response = await litellm.acompletion(
                model=model,
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                stream=True,
                temperature=0.75,
                max_tokens=4096,
            )

            full_text = ""
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_text += delta
                    yield f"data: {json.dumps({'delta': delta})}\n\n"

            # Save AI response
            await db.chats.update_one(
                {"id": chat["id"]},
                {
                    "$push": {"messages": {"role": "assistant", "content": full_text}},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/chats")
async def get_all_chats(db=Depends(get_db)):
    chats = await db.chats.find().sort("updated_at", -1).to_list(50)
    return [{"id": c["id"], "title": c.get("title", "New Chat")} for c in chats]


@router.get("/chat/{chat_id}")
async def get_chat(chat_id: str, db=Depends(get_db)):
    chat = await db.chats.find_one({"id": chat_id})
    if not chat:
        raise HTTPException(404, "Chat not found")
    return chat

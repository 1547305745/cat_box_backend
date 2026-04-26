from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import requests
import time

from models.database import get_db, Character
from models.schemas import UserCreate, ChatRequest, ChatResponse
from core.managers import UserManager, CharacterManager, ConversationManager, MessageManager
from config import settings

router = APIRouter(prefix="/api", tags=["chat"])


def char_to_dict(c):
    return {
        "id": c.id, "name": c.name, "personality": c.personality,
        "backstory": c.backstory, "speaking_style": c.speaking_style,
        "first_greeting": c.first_greeting, "bio": c.bio,
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None
    }


@router.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    return UserManager.create_user(user, db)


@router.get("/users/{user_id}")
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = UserManager.get_user(user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


@router.get("/characters")
def list_characters(db: Session = Depends(get_db)):
    return [char_to_dict(c) for c in CharacterManager.get_all_characters(db)]


@router.get("/characters/{character_id}")
def get_character(character_id: str, db: Session = Depends(get_db)):
    character = CharacterManager.get_character(character_id, db)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    return char_to_dict(character)


@router.post("/characters")
def create_character(character: dict, db: Session = Depends(get_db)):
    from models.schemas import CharacterCreate
    try:
        char = CharacterManager.create_character(CharacterCreate(**character), db)
        return char_to_dict(char)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/characters/{character_id}")
def delete_character(character_id: str, db: Session = Depends(get_db)):
    character = CharacterManager.get_character(character_id, db)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    CharacterManager.delete_character(character_id, db)
    return {"message": "角色已删除"}


@router.get("/conversations")
def list_conversations(user_id: str, db: Session = Depends(get_db)):
    conversations = ConversationManager.get_user_conversations(user_id, db)
    return conversations


@router.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conversation = ConversationManager.get_conversation(conversation_id, db)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = MessageManager.get_conversation_messages(conversation_id, db)
    return {
        "id": conversation.id,
        "user_id": conversation.user_id,
        "character_id": conversation.character_id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    }


@router.post("/conversations")
def create_conversation(conversation: dict, db: Session = Depends(get_db)):
    from models.schemas import ConversationCreate
    try:
        conv = ConversationManager.create_conversation(ConversationCreate(**conversation), db)
        return {
            "id": conv.id,
            "user_id": conv.user_id,
            "character_id": conv.character_id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
            "updated_at": conv.updated_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str, db: Session = Depends(get_db)):
    conversation = ConversationManager.get_conversation(conversation_id, db)
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")
    ConversationManager.delete_conversation(conversation_id, db)
    return {"message": "会话已删除"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        user = UserManager.get_user(request.user_id, db)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        character = CharacterManager.get_character(request.character_id, db)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")

        if not request.conversation_id:
            from models.schemas import ConversationCreate
            conv_data = ConversationCreate(
                id=f"conv_{user.id}_{character.id}_{int(time.time())}",
                user_id=user.id,
                character_id=character.id,
                title=request.message[:20] or "新对话"
            )
            conversation = ConversationManager.create_conversation(conv_data, db)
            request.conversation_id = conversation.id
            is_new_conversation = True
        else:
            conversation = ConversationManager.get_conversation(request.conversation_id, db)
            if not conversation:
                raise HTTPException(status_code=404, detail="会话不存在")
            is_new_conversation = False

        # 先获取最近的消息，再添加新消息，避免重复
        recent_messages = MessageManager.get_conversation_messages(request.conversation_id, db, limit=20)

        MessageManager.add_message(request.conversation_id, "user", request.message, db)

        system_prompt = f"你是{character.name}，{character.personality or ''}。{character.backstory or ''}"
        if character.speaking_style:
            system_prompt += f" 你的说话风格是：{character.speaking_style}"
        system_prompt += "\n请用中文回复，保持角色一致性。"
        system_prompt += "\n重要：请用（）表示动作，保持对话自然流畅。"

        messages = [{"role": "system", "content": system_prompt}]

        if is_new_conversation and character.first_greeting:
            greeting_message = character.first_greeting
            MessageManager.add_message(request.conversation_id, "assistant", greeting_message, db)
            system_prompt_with_greeting = system_prompt + f"\n重要：你有一个开场白，在首次对话时必须说。开场白是：{greeting_message}\n开场白要用（）表示动作，控制在100字以内。"
            messages = [{"role": "system", "content": system_prompt_with_greeting}]

        for msg in recent_messages:
            messages.append({"role": "user" if msg.role == "user" else "assistant", "content": msg.content})
        messages.append({"role": "user", "content": request.message})

        response = requests.post(
            f"{settings.openai_base_url}/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {settings.openai_api_key}"},
            json={"model": settings.llm_model, "messages": messages, "temperature": 0.8},
            timeout=30
        )

        if response.status_code == 200:
            response_text = response.json()['choices'][0]['message']['content']
        else:
            response_text = f"抱歉，API调用失败：{response.status_code}"

        MessageManager.add_message(request.conversation_id, "assistant", response_text, db)

        return ChatResponse(
            conversation_id=request.conversation_id,
            character_id=request.character_id,
            character_name=character.name,
            response=response_text,
            retrieved_memories=[]
        )
    except HTTPException:
        raise
    except Exception as e:
        response_text = f"抱歉，我暂时无法回应你的消息。错误：{str(e)}"
        if 'conversation' in locals() and request.conversation_id:
            MessageManager.add_message(request.conversation_id, "assistant", response_text, db)
        return ChatResponse(
            conversation_id=getattr(request, 'conversation_id', ''),
            character_id=request.character_id,
            character_name=getattr(character, 'name', ''),
            response=response_text,
            retrieved_memories=[]
        )


@router.delete("/memories/character/{character_id}")
def clear_character_memories(character_id: str):
    from memory.manager import MemoryManager
    memory_manager = MemoryManager()
    memory_manager.clear_character_memories(character_id)
    return {"message": "角色记忆已清除"}

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    id: str
    name: str


class CharacterBase(BaseModel):
    id: str
    name: str
    personality: Optional[str] = None
    backstory: Optional[str] = None
    speaking_style: Optional[str] = None


class CharacterCreate(CharacterBase):
    pass


class ConversationCreate(BaseModel):
    id: str
    user_id: str
    character_id: str
    title: Optional[str] = "新对话"


class ChatRequest(BaseModel):
    user_id: str
    conversation_id: Optional[str] = None
    character_id: str
    message: str


class ChatResponse(BaseModel):
    conversation_id: str
    character_id: str
    character_name: str
    response: str
    retrieved_memories: List[str] = []


# 开放剧情模式相关模型

class ScriptBase(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    style: Optional[str] = "古风"
    author: Optional[str] = "AI"
    is_public: Optional[bool] = False


class ScriptCreate(ScriptBase):
    pass


class ScriptStageBase(BaseModel):
    id: str
    stage_number: int
    title: str
    description: Optional[str] = None
    goal: str
    opening_line: Optional[str] = None
    opening_character_id: Optional[str] = None
    completion_condition: str


class ScriptStageCreate(ScriptStageBase):
    script_id: str


class ScriptCharacterBase(BaseModel):
    id: str
    character_id: str
    character_type: str  # main, support, narrator
    role_in_script: Optional[str] = None
    is_essential: Optional[bool] = False


class ScriptCharacterCreate(ScriptCharacterBase):
    script_id: str


class ScriptSessionBase(BaseModel):
    id: Optional[str] = None
    user_id: str
    script_id: str


class ScriptSessionCreate(ScriptSessionBase):
    pass


class ScriptChatRequest(BaseModel):
    user_id: str
    script_id: Optional[str] = None
    session_id: Optional[str] = None
    message: str


class ScriptChatResponse(BaseModel):
    session_id: str
    script_id: str
    script_title: str
    current_stage_id: Optional[str] = None
    current_stage_title: Optional[str] = None
    current_scene: Optional[str] = None
    current_characters: Optional[str] = None
    messages: List[dict]
    is_completed: bool

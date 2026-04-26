from sqlalchemy import create_engine, Column, String, Text, DateTime, ForeignKey, Integer, Boolean, Enum as SQLEnum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from config import settings

engine = create_engine(
    f"sqlite:///{settings.sqlite_db_path}",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class MemoryType(str, enum.Enum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    USER_PREFERENCE = "user_preference"


class CharacterType(str, enum.Enum):
    MAIN = "main"
    SUPPORT = "support"
    NARRATOR = "narrator"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    script_sessions = relationship("ScriptSession", back_populates="user", cascade="all, delete-orphan")


class Character(Base):
    __tablename__ = "characters"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    personality = Column(Text)
    backstory = Column(Text)
    speaking_style = Column(Text)
    system_prompt_template = Column(Text)
    first_greeting = Column(Text)
    bio = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    conversations = relationship("Conversation", back_populates="character")
    script_characters = relationship("ScriptCharacter", back_populates="character")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    character_id = Column(String, ForeignKey("characters.id"), nullable=False)
    title = Column(String, default="新对话")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    character = relationship("Character", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    turn_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Memory(Base):
    __tablename__ = "memories"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    character_id = Column(String, ForeignKey("characters.id"), nullable=True)
    memory_type = Column(SQLEnum(MemoryType), nullable=False)
    content = Column(Text, nullable=False)
    importance_score = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed_at = Column(DateTime, default=datetime.utcnow)
    vector_id = Column(String, nullable=True)

    user = relationship("User", back_populates="memories")


# 开放剧情模式相关模型

class Script(Base):
    __tablename__ = "scripts"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    style = Column(String, default="古风")  # 古风/现代/欧式等
    author = Column(String, default="AI")
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stages = relationship("ScriptStage", back_populates="script", cascade="all, delete-orphan")
    script_characters = relationship("ScriptCharacter", back_populates="script", cascade="all, delete-orphan")


class ScriptStage(Base):
    __tablename__ = "script_stages"

    id = Column(String, primary_key=True)
    script_id = Column(String, ForeignKey("scripts.id"), nullable=False)
    stage_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    goal = Column(Text, nullable=False)
    opening_line = Column(Text)  # 开场白
    opening_character_id = Column(String, nullable=True)  # 开场白角色
    completion_condition = Column(Text)  # 完成条件
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    script = relationship("Script", back_populates="stages")


class ScriptCharacter(Base):
    __tablename__ = "script_characters"

    id = Column(String, primary_key=True)
    script_id = Column(String, ForeignKey("scripts.id"), nullable=False)
    character_id = Column(String, ForeignKey("characters.id"), nullable=False)
    character_type = Column(SQLEnum(CharacterType), nullable=False)
    role_in_script = Column(String)  # 在剧本中的角色定位
    is_essential = Column(Boolean, default=False)  # 是否关键角色
    created_at = Column(DateTime, default=datetime.utcnow)

    script = relationship("Script", back_populates="script_characters")
    character = relationship("Character", back_populates="script_characters")


class ScriptSession(Base):
    __tablename__ = "script_sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    script_id = Column(String, ForeignKey("scripts.id"), nullable=False)
    current_stage_id = Column(String, ForeignKey("script_stages.id"), nullable=True)
    current_scene = Column(Text)  # 当前场景描述
    current_characters = Column(Text)  # 当前在场角色
    is_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="script_sessions")
    script = relationship("Script")
    current_stage = relationship("ScriptStage")
    messages = relationship("ScriptMessage", back_populates="session", cascade="all, delete-orphan")


class ScriptMessage(Base):
    __tablename__ = "script_messages"

    id = Column(String, primary_key=True)
    session_id = Column(String, ForeignKey("script_sessions.id"), nullable=False)
    role = Column(String, nullable=False)  # user, character, narrator
    character_id = Column(String, nullable=True)  # 如果是角色消息
    content = Column(Text, nullable=False)
    turn_number = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ScriptSession", back_populates="messages")


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
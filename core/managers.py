from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from models.database import User, Character, Conversation, Message


class UserManager:
    @staticmethod
    def create_user(user_data, db: Session) -> User:
        user = User(id=user_data.id, name=user_data.name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user(user_id: str, db: Session) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        return db.query(User).all()

    @staticmethod
    def delete_user(user_id: str, db: Session) -> bool:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False


class CharacterManager:
    @staticmethod
    def create_character(character_data, db: Session) -> Character:
        character = Character(
            id=character_data.id,
            name=character_data.name,
            personality=character_data.personality,
            backstory=character_data.backstory,
            speaking_style=character_data.speaking_style
        )
        db.add(character)
        db.commit()
        db.refresh(character)
        return character

    @staticmethod
    def get_character(character_id: str, db: Session) -> Optional[Character]:
        return db.query(Character).filter(Character.id == character_id).first()

    @staticmethod
    def get_all_characters(db: Session, active_only: bool = True) -> List[Character]:
        query = db.query(Character)
        if active_only:
            query = query.filter(Character.is_active == True)
        return query.all()

    @staticmethod
    def delete_character(character_id: str, db: Session) -> bool:
        character = db.query(Character).filter(Character.id == character_id).first()
        if character:
            character.is_active = False
            db.commit()
            return True
        return False


class ConversationManager:
    @staticmethod
    def create_conversation(conversation_data, db: Session) -> Conversation:
        conversation_id = conversation_data.id or str(uuid.uuid4())
        conversation = Conversation(
            id=conversation_id,
            user_id=conversation_data.user_id,
            character_id=conversation_data.character_id,
            title=conversation_data.title or "新对话"
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def get_conversation(conversation_id: str, db: Session) -> Optional[Conversation]:
        return db.query(Conversation).filter(Conversation.id == conversation_id).first()

    @staticmethod
    def get_user_conversations(user_id: str, db: Session) -> List[Conversation]:
        return db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.updated_at.desc()).all()

    @staticmethod
    def delete_conversation(conversation_id: str, db: Session) -> bool:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False


class MessageManager:
    @staticmethod
    def add_message(conversation_id: str, role: str, content: str, db: Session) -> Message:
        last_message = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.turn_number.desc()).first()

        turn_number = 1 if last_message is None else last_message.turn_number + 1

        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            turn_number=turn_number
        )
        db.add(message)

        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conversation:
            conversation.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def get_conversation_messages(conversation_id: str, db: Session, limit: Optional[int] = None) -> List[Message]:
        query = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.turn_number.asc())
        if limit:
            query = query.limit(limit)
        return query.all()

    @staticmethod
    def get_recent_messages(conversation_id: str, max_turns: int, db: Session) -> List[Message]:
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.turn_number.desc()).limit(max_turns).all()
        return list(reversed(messages))

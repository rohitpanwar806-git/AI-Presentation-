"""
Session Memory Management System
Maintains context from presentations without storing security information
"""
from typing import Dict, List, Any
from datetime import datetime
import json
from dataclasses import dataclass, asdict, field


@dataclass
class SessionMessage:
    """Single message in session context"""
    role: str  # 'audience', 'avatar', 'system'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    avatar_id: str = ""
    voice_id: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentContext:
    """Context extracted from uploaded document"""
    document_id: str
    document_name: str
    document_type: str  # 'pdf', 'pptx', 'docx'
    extracted_text: str
    key_topics: List[str] = field(default_factory=list)
    summary: str = ""
    upload_time: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class PresentationSession:
    """Complete presentation session context"""
    session_id: str
    user_id: str
    avatar_id: str
    voice_id: str
    document: DocumentContext
    start_time: str
    end_time: str = ""
    messages: List[SessionMessage] = field(default_factory=list)
    session_summary: str = ""
    audience_count: int = 0
    presentation_title: str = ""
    
    def add_message(self, message: SessionMessage) -> None:
        """Add message to session"""
        self.messages.append(message)
    
    def get_context_for_llm(self) -> str:
        """Get formatted context for LLM"""
        context = f"""
Presentation Session Context:
Title: {self.presentation_title}
Avatar: {self.avatar_id}
Voice: {self.voice_id}
Document: {self.document.document_name}

Document Topics: {', '.join(self.document.key_topics)}
Document Summary: {self.document.summary}

Recent Discussion:
"""
        # Add last 10 messages for context
        for msg in self.messages[-10:]:
            context += f"\n[{msg.role.upper()}]: {msg.content}"
        
        return context
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (excluding sensitive info)"""
        return {
            "session_id": self.session_id,
            "avatar_id": self.avatar_id,
            "voice_id": self.voice_id,
            "document_name": self.document.document_name,
            "start_time": self.start_time,
            "message_count": len(self.messages),
            "audience_count": self.audience_count,
            "presentation_title": self.presentation_title
        }


class SessionMemoryManager:
    """Manages presentation session memory (non-persistent)"""
    
    def __init__(self):
        self.sessions: Dict[str, PresentationSession] = {}
        self.user_session_history: Dict[str, List[str]] = {}  # user_id -> [session_ids]
    
    def create_session(
        self,
        user_id: str,
        avatar_id: str,
        voice_id: str,
        document: DocumentContext,
        presentation_title: str = ""
    ) -> str:
        """Create new presentation session"""
        from uuid import uuid4
        session_id = str(uuid4())
        
        session = PresentationSession(
            session_id=session_id,
            user_id=user_id,
            avatar_id=avatar_id,
            voice_id=voice_id,
            document=document,
            start_time=datetime.now().isoformat(),
            presentation_title=presentation_title
        )
        
        self.sessions[session_id] = session
        
        if user_id not in self.user_session_history:
            self.user_session_history[user_id] = []
        self.user_session_history[user_id].append(session_id)
        
        return session_id
    
    def get_session(self, session_id: str) -> PresentationSession:
        """Get session by ID"""
        return self.sessions.get(session_id)
    
    def add_message_to_session(
        self,
        session_id: str,
        role: str,
        content: str,
        avatar_id: str = "",
        voice_id: str = ""
    ) -> bool:
        """Add message to session context"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        message = SessionMessage(
            role=role,
            content=content,
            avatar_id=avatar_id,
            voice_id=voice_id
        )
        session.add_message(message)
        return True
    
    def get_session_context(self, session_id: str) -> str:
        """Get formatted context for LLM"""
        session = self.get_session(session_id)
        if not session:
            return ""
        return session.get_context_for_llm()
    
    def end_session(self, session_id: str, summary: str = "") -> bool:
        """End presentation session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        session.end_time = datetime.now().isoformat()
        session.session_summary = summary
        return True
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for user"""
        session_ids = self.user_session_history.get(user_id, [])
        return [
            self.sessions[sid].to_dict()
            for sid in session_ids
            if sid in self.sessions
        ]
    
    def clear_old_sessions(self, max_sessions_per_user: int = 10) -> None:
        """Keep only recent sessions to manage memory"""
        for user_id, session_ids in self.user_session_history.items():
            if len(session_ids) > max_sessions_per_user:
                # Keep only recent sessions
                sessions_to_keep = session_ids[-max_sessions_per_user:]
                for session_id in session_ids[:-max_sessions_per_user]:
                    if session_id in self.sessions:
                        del self.sessions[session_id]
                self.user_session_history[user_id] = sessions_to_keep


# Global instance
_session_manager = SessionMemoryManager()


def get_session_manager() -> SessionMemoryManager:
    """Get global session memory manager"""
    return _session_manager

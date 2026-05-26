"""
Presentation Session Endpoints
Manages live presentation sessions with avatar assistance
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import PyPDF2
from backend.api.auth import _get_current_user
from backend.services.session_memory import (
    get_session_manager,
    DocumentContext,
    SessionMemoryManager
)
from backend.services.document_analyzer import (
    get_document_analyzer,
    get_augmented_llm,
    DocumentAnalyzer,
    DocumentAugmentedLLM
)

router = APIRouter()


class StartPresentationRequest(BaseModel):
    """Start a presentation session"""
    document_filename: str
    avatar_id: str
    voice_id: str
    presentation_title: str = ""
    audience_count: int = 0


class StartPresentationResponse(BaseModel):
    """Response when presentation starts"""
    session_id: str
    message: str
    document_summary: str
    key_topics: list


class AudienceQuestion(BaseModel):
    """Audience member asks question"""
    session_id: str
    question: str
    name: str = "Audience Member"


class AvatarResponse(BaseModel):
    """Avatar response to question"""
    answer: str
    confidence: str = "high"
    referenced_document: bool = True
    follow_up: Optional[str] = None


class EndPresentationRequest(BaseModel):
    """End presentation session"""
    session_id: str
    session_summary: str = ""
    feedback: str = ""


class SessionInfo(BaseModel):
    """Information about a session"""
    session_id: str
    presentation_title: str
    avatar_id: str
    voice_id: str
    duration_minutes: float
    message_count: int
    audience_count: int


def extract_text_from_file(file_path: str) -> str:
    """Extract text from document (PDF, PPTX, DOCX)"""
    try:
        if file_path.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = ""
                for page in pdf_reader.pages[:10]:  # First 10 pages
                    text += page.extract_text()
                return text
        elif file_path.endswith('.txt'):
            with open(file_path, 'r') as f:
                return f.read()
        else:
            # For PPTX, DOCX would need python-pptx, python-docx
            return f"Document type for {file_path} requires additional processing"
    except Exception as e:
        return f"Error extracting text: {str(e)}"


@router.post("/start", response_model=StartPresentationResponse)
async def start_presentation(
    request: StartPresentationRequest,
    current_user = Depends(_get_current_user)
) -> StartPresentationResponse:
    """
    Start a new presentation session with avatar
    """
    try:
        session_manager: SessionMemoryManager = get_session_manager()
        document_analyzer: DocumentAnalyzer = get_document_analyzer()
        
        # Placeholder: In production, load actual document from storage
        # For now, create a sample document context
        sample_text = f"""
        This is a presentation about {request.presentation_title}.
        The document has been uploaded and is ready for analysis.
        """
        
        # Analyze document
        analysis = document_analyzer.analyze_document(
            sample_text,
            request.document_filename
        )
        
        # Create document context
        document = DocumentContext(
            document_id=request.document_filename,
            document_name=request.document_filename,
            document_type=request.document_filename.split('.')[-1],
            extracted_text=sample_text,
            key_topics=analysis.get("topics", []),
            summary=analysis.get("summary", "")
        )
        
        # Create session
        user_id = getattr(current_user, "id", "unknown")
        session_id = session_manager.create_session(
            user_id=str(user_id),
            avatar_id=request.avatar_id,
            voice_id=request.voice_id,
            document=document,
            presentation_title=request.presentation_title
        )
        
        # Set audience count
        session = session_manager.get_session(session_id)
        session.audience_count = request.audience_count
        
        return StartPresentationResponse(
            session_id=session_id,
            message=f"🎬 Presentation session started with {request.presentation_title}",
            document_summary=analysis.get("summary", ""),
            key_topics=analysis.get("topics", [])
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to start presentation: {str(e)}"
        )


@router.post("/question", response_model=AvatarResponse)
async def ask_question(
    request: AudienceQuestion,
    current_user = Depends(_get_current_user)
) -> AvatarResponse:
    """
    Answer an audience question using document and session context
    """
    try:
        session_manager: SessionMemoryManager = get_session_manager()
        augmented_llm: DocumentAugmentedLLM = get_augmented_llm()
        
        # Get session
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # Get document and session context
        doc_context = session.document.extracted_text[:2000]
        session_context = session.get_context_for_llm()
        
        # Generate answer
        answer = augmented_llm.answer_question(
            question=request.question,
            document_context=doc_context,
            session_context=session_context
        )
        
        # Add messages to session
        session_manager.add_message_to_session(
            request.session_id,
            "audience",
            request.question
        )
        session_manager.add_message_to_session(
            request.session_id,
            "avatar",
            answer,
            avatar_id=session.avatar_id,
            voice_id=session.voice_id
        )
        
        return AvatarResponse(
            answer=answer,
            confidence="high",
            referenced_document=True,
            follow_up="Would you like to know more about any specific aspect?"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to answer question: {str(e)}"
        )


@router.post("/end", response_model=dict)
async def end_presentation(
    request: EndPresentationRequest,
    current_user = Depends(_get_current_user)
) -> dict:
    """
    End presentation session and store summary
    """
    try:
        session_manager: SessionMemoryManager = get_session_manager()
        
        session = session_manager.get_session(request.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        # End session
        session_manager.end_session(
            request.session_id,
            request.session_summary
        )
        
        # Calculate session stats
        from datetime import datetime
        start_time = datetime.fromisoformat(session.start_time)
        end_time = datetime.fromisoformat(session.end_time)
        duration = (end_time - start_time).total_seconds() / 60
        
        return {
            "status": "success",
            "session_id": request.session_id,
            "message": "📌 Presentation session ended successfully",
            "duration_minutes": round(duration, 2),
            "message_count": len(session.messages),
            "audience_count": session.audience_count,
            "summary_recorded": bool(request.session_summary)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to end presentation: {str(e)}"
        )


@router.get("/session/{session_id}", response_model=dict)
async def get_session_info(
    session_id: str,
    current_user = Depends(_get_current_user)
) -> dict:
    """
    Get information about a presentation session
    """
    session_manager: SessionMemoryManager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    from datetime import datetime
    start_time = datetime.fromisoformat(session.start_time)
    if session.end_time:
        end_time = datetime.fromisoformat(session.end_time)
        duration = (end_time - start_time).total_seconds() / 60
    else:
        duration = (datetime.now() - start_time).total_seconds() / 60
    
    return {
        "session_id": session.session_id,
        "presentation_title": session.presentation_title,
        "avatar_id": session.avatar_id,
        "voice_id": session.voice_id,
        "document_name": session.document.document_name,
        "duration_minutes": round(duration, 2),
        "message_count": len(session.messages),
        "audience_count": session.audience_count,
        "key_topics": session.document.key_topics,
        "is_active": not bool(session.end_time)
    }


@router.post("/feedback/{session_id}", response_model=dict)
async def submit_feedback(
    session_id: str,
    feedback: dict,
    current_user = Depends(_get_current_user)
) -> dict:
    """
    Submit feedback about presentation session
    """
    session_manager: SessionMemoryManager = get_session_manager()
    session = session_manager.get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Store feedback in session (can be persisted to DB later)
    feedback_text = feedback.get("comments", "")
    rating = feedback.get("rating", 0)
    
    return {
        "status": "success",
        "message": "🙏 Thank you for your feedback!",
        "session_id": session_id,
        "rating_received": rating
    }

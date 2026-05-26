"""
RAG (Retrieval-Augmented Generation) Service
- Document chunking and embedding
- Semantic search within document content
- Context-aware Q&A with relevance scoring
- Smart summarization and key-point extraction
- Quiz generation from content
"""
import json
import logging
import os
import re
import hashlib
from typing import Optional

from backend.config import ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "project-987f80c5-14e3-450d-9b0")
GCP_REGION = os.getenv("GCP_REGION", "asia-south1")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Try Vertex AI (Cloud Run ADC)
HAS_VERTEXAI = False
_vertexai_model = None
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel
    vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
    _vertexai_model = GenerativeModel("gemini-2.0-flash-001")
    HAS_VERTEXAI = True
except Exception:
    pass

# Fallback: google-generativeai with API key
HAS_GENAI = False
try:
    import google.generativeai as genai
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        HAS_GENAI = True
except ImportError:
    pass

HAS_ANTHROPIC = False
try:
    import anthropic
    if ANTHROPIC_API_KEY:
        HAS_ANTHROPIC = True
except ImportError:
    pass

HAS_LLM = HAS_VERTEXAI or HAS_GENAI or HAS_ANTHROPIC


def _llm_generate(prompt: str, max_tokens: int = 2000) -> str | None:
    """Call best available LLM. Returns response text or None."""
    if HAS_VERTEXAI:
        try:
            response = _vertexai_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Vertex AI failed: {e}")
    if HAS_GENAI:
        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"google-generativeai failed: {e}")
    if HAS_ANTHROPIC:
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return message.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude failed: {e}")
    return None


def chunk_document(text: str, chunk_size: int = 800, overlap: int = 150) -> list:
    """Split document into overlapping chunks for better retrieval."""
    if not text.strip():
        return []
    
    # Split by paragraph boundaries first
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append(current_chunk.strip())
            # Keep overlap from end of previous chunk
            words = current_chunk.split()
            overlap_text = " ".join(words[-overlap // 5:]) if len(words) > overlap // 5 else ""
            current_chunk = overlap_text + " " + para
        else:
            current_chunk += ("\n\n" if current_chunk else "") + para
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    return chunks


def compute_chunk_id(chunk: str) -> str:
    """Generate stable ID for a chunk."""
    return hashlib.md5(chunk[:200].encode()).hexdigest()[:12]


def find_relevant_chunks(query: str, chunks: list, top_k: int = 5) -> list:
    """
    Simple keyword-based relevance scoring.
    In production, use vector embeddings (Pinecone) for semantic search.
    """
    if not chunks or not query:
        return chunks[:top_k]
    
    query_words = set(re.findall(r'\b\w{3,}\b', query.lower()))
    
    scored = []
    for chunk in chunks:
        chunk_lower = chunk.lower()
        # Score based on keyword overlap
        score = sum(1 for w in query_words if w in chunk_lower)
        # Boost for exact phrase match
        if query.lower()[:30] in chunk_lower:
            score += 5
        scored.append((score, chunk))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def generate_summary(document_text: str, title: str) -> dict:
    """Generate an executive summary with key points from the document."""
    if HAS_LLM and document_text.strip():
        result = _summary_with_llm(document_text, title)
        if result:
            return result
    return _summary_heuristic(document_text, title)


def _summary_with_llm(document_text: str, title: str) -> dict | None:
    """Generate summary using best available LLM."""
    doc_excerpt = document_text[:12000]

    prompt = f"""Analyze this document and provide a structured summary.

Return a JSON object with:
{{
  "executive_summary": "2-3 sentence overview",
  "key_points": ["point 1", "point 2", ...],
  "topics": ["topic1", "topic2", ...],
  "difficulty_level": "beginner|intermediate|advanced",
  "estimated_read_time_minutes": number,
  "target_audience": "description of who this is for"
}}

Document: {title}
Content:
{doc_excerpt}"""

    response = _llm_generate(prompt, 1500)
    if response:
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except (json.JSONDecodeError, ValueError):
                pass
    return None


def _summary_heuristic(document_text: str, title: str) -> dict:
    """Heuristic summary when API unavailable."""
    words = document_text.split()
    word_count = len(words)
    sentences = re.split(r'[.!?]+', document_text)
    
    # Extract likely key points (sentences with strong keywords)
    key_indicators = ['important', 'key', 'main', 'critical', 'essential', 'significant', 'primary', 'conclusion', 'result']
    key_sentences = [s.strip() for s in sentences if any(k in s.lower() for k in key_indicators)][:6]
    
    if not key_sentences:
        key_sentences = [s.strip() for s in sentences[:6] if len(s.strip()) > 30]
    
    return {
        "executive_summary": f"This document covers {title}. It contains approximately {word_count} words across multiple sections.",
        "key_points": key_sentences[:6] if key_sentences else ["Content analysis available", "Upload document for detailed insights"],
        "topics": _extract_topics(document_text),
        "difficulty_level": "intermediate",
        "estimated_read_time_minutes": max(1, word_count // 200),
        "target_audience": "Professional audience"
    }


def _extract_topics(text: str) -> list:
    """Extract likely topics from text using frequency analysis."""
    # Simple noun phrase extraction
    words = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b', text)
    from collections import Counter
    common = Counter(words).most_common(8)
    return [word for word, _ in common if len(word) > 3][:6]


def generate_quiz(document_text: str, title: str, num_questions: int = 5) -> list:
    """Generate quiz questions from document content."""
    if HAS_LLM and document_text.strip():
        result = _quiz_with_llm(document_text, title, num_questions)
        if result:
            return result
    return _quiz_heuristic(document_text, title, num_questions)


def _quiz_with_llm(document_text: str, title: str, num_questions: int) -> list | None:
    """Generate quiz using best available LLM."""
    doc_excerpt = document_text[:10000]

    prompt = f"""Based on this document, create {num_questions} multiple-choice quiz questions to test comprehension.

Return ONLY a JSON array:
[
  {{
    "question": "What is...?",
    "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": 0,
    "explanation": "Brief explanation why this is correct"
  }}
]

Rules:
- Questions should test understanding, not just memorization
- Each question has exactly 4 options (A, B, C, D)
- correct_answer is the 0-based index of the correct option
- Mix difficulty levels
- Make wrong options plausible but clearly wrong

Document: {title}
Content:
{doc_excerpt}"""

    response = _llm_generate(prompt, 2000)
    if response:
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                questions = json.loads(json_match.group())
                valid = []
                for q in questions:
                    if isinstance(q, dict) and "question" in q and "options" in q:
                        valid.append({
                            "question": q["question"],
                            "options": q["options"][:4],
                            "correct_answer": q.get("correct_answer", 0),
                            "explanation": q.get("explanation", ""),
                        })
                if valid:
                    return valid
            except (json.JSONDecodeError, ValueError):
                pass
    return None


def _quiz_heuristic(document_text: str, title: str, num_questions: int) -> list:
    """Generate basic quiz questions without API."""
    return [
        {
            "question": f"What is the main topic of this presentation about '{title}'?",
            "options": [
                f"A) {title}",
                "B) An unrelated subject",
                "C) Historical events only",
                "D) None of the above"
            ],
            "correct_answer": 0,
            "explanation": f"The document is primarily about {title}."
        },
        {
            "question": "What format was the original document in?",
            "options": [
                "A) A structured professional document",
                "B) A hand-written note",
                "C) An audio recording",
                "D) A video file"
            ],
            "correct_answer": 0,
            "explanation": "The content was extracted from an uploaded document."
        }
    ]


def generate_script_from_slides(slides: list, style: str = "professional") -> list:
    """Generate narration scripts for each slide."""
    if HAS_LLM and slides:
        result = _script_with_llm(slides, style)
        if result:
            return result
    return _script_heuristic(slides, style)


def _script_with_llm(slides: list, style: str) -> list | None:
    """Generate narration script using best available LLM."""
    slides_text = json.dumps(slides, indent=2)[:8000]

    style_desc = {
        "professional": "formal and authoritative, like a business presenter",
        "friendly": "warm and conversational, like explaining to a colleague",
        "educational": "clear and structured, like a teacher explaining to students",
        "energetic": "enthusiastic and dynamic, like a TED talk speaker",
    }.get(style, "professional and clear")

    prompt = f"""Generate a narration script for each slide in this presentation.
The speaking style should be {style_desc}.

For each slide, write what the presenter should SAY out loud (not read word-for-word from the slide).
The narration should expand on bullet points, add context, and create a natural flow between slides.

Return ONLY a JSON array where each element has:
{{"slide_index": 0, "narration": "What the presenter says for this slide", "duration_seconds": estimated_time}}

Slides:
{slides_text}"""

    response = _llm_generate(prompt, 3000)
    if response:
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                scripts = json.loads(json_match.group())
                valid = []
                for s in scripts:
                    if isinstance(s, dict) and "narration" in s:
                        valid.append({
                            "slide_index": s.get("slide_index", len(valid)),
                            "narration": s["narration"],
                            "duration_seconds": s.get("duration_seconds", 15),
                        })
                if valid:
                    return valid
            except (json.JSONDecodeError, ValueError):
                pass
    return None


def _script_heuristic(slides: list, style: str) -> list:
    """Generate basic scripts from slide content."""
    scripts = []
    for i, slide in enumerate(slides):
        title = slide.get("title", "")
        body = slide.get("body", "")
        bullets = slide.get("bullets", [])
        
        if slide.get("type") == "title":
            narration = f"Welcome to this presentation on {title}. {body or 'Let me walk you through the key points.'}"
        elif slide.get("type") == "summary":
            narration = f"To summarize, {title}. "
            if bullets:
                narration += "The key takeaways are: " + ". ".join(bullets[:4]) + "."
            else:
                narration += body or "Thank you for your attention."
        else:
            narration = f"Now let's look at {title}. "
            if body:
                narration += body
            elif bullets:
                narration += "The main points here are: " + ". ".join(bullets[:5]) + "."
        
        # Estimate duration (avg 150 words per minute)
        word_count = len(narration.split())
        duration = max(5, int(word_count / 2.5))
        
        scripts.append({
            "slide_index": i,
            "narration": narration,
            "duration_seconds": duration
        })
    
    return scripts

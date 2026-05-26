"""
Agentic Pipeline Service
- Document analysis using Anthropic Claude
- Content extraction and structuring
- Slide generation from document content
- Q&A tutor mode (avatar answers questions within document context)
"""
import os
import re
from typing import Optional
from backend.config import ANTHROPIC_API_KEY

# Try to import anthropic; graceful fallback if not available
try:
    import anthropic
    HAS_ANTHROPIC = bool(ANTHROPIC_API_KEY)
except ImportError:
    HAS_ANTHROPIC = False

# Try to import document parsers
try:
    from PyPDF2 import PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from pptx import Presentation as PptxPresentation
    HAS_PPTX = True
except ImportError:
    HAS_PPTX = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False


def extract_text_from_file(file_path: str) -> str:
    """Extract text content from uploaded document."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.pdf' and HAS_PDF:
        return _extract_pdf(file_path)
    elif ext == '.pptx' and HAS_PPTX:
        return _extract_pptx(file_path)
    elif ext == '.docx' and HAS_DOCX:
        return _extract_docx(file_path)
    else:
        return ""


def _extract_pdf(file_path: str) -> str:
    """Extract text from PDF."""
    text_parts = []
    reader = PdfReader(file_path)
    for page in reader.pages[:50]:  # Limit to 50 pages
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text.strip())
    return "\n\n".join(text_parts)


def _extract_pptx(file_path: str) -> str:
    """Extract text from PowerPoint."""
    text_parts = []
    prs = PptxPresentation(file_path)
    for slide_num, slide in enumerate(prs.slides[:50], 1):
        slide_text = []
        for shape in slide.shapes:
            if shape.has_text_frame:
                for paragraph in shape.text_frame.paragraphs:
                    text = paragraph.text.strip()
                    if text:
                        slide_text.append(text)
        if slide_text:
            text_parts.append(f"[Slide {slide_num}]\n" + "\n".join(slide_text))
    return "\n\n".join(text_parts)


def _extract_docx(file_path: str) -> str:
    """Extract text from Word document."""
    text_parts = []
    doc = DocxDocument(file_path)
    for para in doc.paragraphs[:200]:  # Limit paragraphs
        text = para.text.strip()
        if text:
            text_parts.append(text)
    return "\n\n".join(text_parts)


def generate_slides_from_content(document_text: str, title: str) -> list:
    """
    Use Claude to analyze the document and generate structured presentation slides.
    Falls back to a heuristic approach if API is unavailable.
    """
    if HAS_ANTHROPIC and document_text.strip():
        return _generate_with_claude(document_text, title)
    else:
        return _generate_heuristic(document_text, title)


def _generate_with_claude(document_text: str, title: str) -> list:
    """Generate slides using Claude API."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Truncate document to avoid token limits
    max_chars = 15000
    doc_excerpt = document_text[:max_chars]
    if len(document_text) > max_chars:
        doc_excerpt += "\n\n[... document continues ...]"

    prompt = f"""Analyze the following document and create a professional presentation with 8-12 slides. 
Each slide should have a title and content (either a paragraph or bullet points).

Return ONLY a JSON array of slides in this exact format:
[
  {{"title": "Slide Title", "body": "Optional paragraph text or null", "bullets": ["bullet 1", "bullet 2"] or null, "type": "title|content|summary"}},
  ...
]

Rules:
- First slide should be a title slide with type "title"
- Last slide should be a summary/conclusion with type "summary"
- Middle slides should be type "content"
- Each slide should have EITHER body OR bullets (not both)
- Bullet points should be concise (under 15 words each)
- Keep content clear and professional
- Extract key insights, facts, and takeaways from the document

Document Title: {title}

Document Content:
{doc_excerpt}"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Extract JSON from response (might be wrapped in markdown code blocks)
        json_match = re.search(r'\[[\s\S]*\]', response_text)
        if json_match:
            import json
            slides = json.loads(json_match.group())
            # Validate structure
            valid_slides = []
            for s in slides:
                if isinstance(s, dict) and "title" in s:
                    valid_slides.append({
                        "title": str(s.get("title", "")),
                        "body": s.get("body"),
                        "bullets": s.get("bullets") if isinstance(s.get("bullets"), list) else None,
                        "type": s.get("type", "content")
                    })
            if valid_slides:
                return valid_slides
    except Exception:
        pass

    # Fallback to heuristic if Claude fails
    return _generate_heuristic(document_text, title)


def _generate_heuristic(document_text: str, title: str) -> list:
    """Generate slides using text heuristics when API is unavailable."""
    slides = [
        {"title": title, "body": "AI-Generated Presentation", "bullets": None, "type": "title"}
    ]

    if not document_text.strip():
        # No content extracted - generate placeholder slides
        slides.extend([
            {"title": "Overview", "body": "This presentation covers the key topics from your uploaded document.", "bullets": None, "type": "content"},
            {"title": "Key Points", "body": None, "bullets": ["Content analysis in progress", "AI-powered slide generation", "Professional avatar delivery", "Interactive Q&A available"], "type": "content"},
            {"title": "Summary", "body": "Your AI presenter is ready to deliver this content to your team.", "bullets": None, "type": "summary"}
        ])
        return slides

    # Split into paragraphs/sections
    paragraphs = [p.strip() for p in document_text.split('\n\n') if p.strip() and len(p.strip()) > 20]

    # Group into slide-sized chunks (max 10 slides from content)
    chunk_size = max(1, len(paragraphs) // 8)
    chunks = []
    for i in range(0, min(len(paragraphs), 40), chunk_size):
        chunk = paragraphs[i:i + chunk_size]
        chunks.append("\n".join(chunk))
        if len(chunks) >= 8:
            break

    for idx, chunk in enumerate(chunks):
        # Extract a title from the first line
        lines = chunk.split('\n')
        slide_title = lines[0][:60] if lines else f"Section {idx + 1}"
        # If title is too long, truncate
        if len(slide_title) > 50:
            slide_title = slide_title[:47] + "..."

        # Decide between body text or bullets
        remaining_lines = lines[1:] if len(lines) > 1 else lines
        if len(remaining_lines) >= 3:
            bullets = [line[:80] for line in remaining_lines[:6]]
            slides.append({"title": slide_title, "body": None, "bullets": bullets, "type": "content"})
        else:
            body = " ".join(remaining_lines)[:250]
            slides.append({"title": slide_title, "body": body or None, "bullets": None, "type": "content"})

    # Add summary slide
    slides.append({
        "title": "Summary & Next Steps",
        "body": None,
        "bullets": [
            "Key insights have been extracted from your document",
            "Ask your AI tutor any questions about this content",
            "Share this presentation with your team",
            "Track engagement through analytics"
        ],
        "type": "summary"
    })

    return slides


def answer_question(document_text: str, question: str, presentation_title: str, chat_history: Optional[list] = None) -> str:
    """
    Answer a question about the document content using Claude.
    Acts as a tutor/expert on the uploaded document.
    """
    if HAS_ANTHROPIC and document_text.strip():
        return _answer_with_claude(document_text, question, presentation_title, chat_history)
    else:
        return _answer_fallback(question, presentation_title)


def _answer_with_claude(document_text: str, question: str, title: str, chat_history: Optional[list] = None) -> str:
    """Answer using Claude with document context."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Truncate document
    max_chars = 12000
    doc_excerpt = document_text[:max_chars]

    system_prompt = f"""You are an AI tutor and presentation expert. You are presenting a document titled "{title}".
Your role is to:
1. Answer questions about the document content accurately
2. Explain concepts from the document in a clear, educational way
3. Help the viewer understand key points
4. Stay within the context of the document - if asked something unrelated, politely redirect

Keep answers concise (2-4 sentences for simple questions, up to a paragraph for complex ones).
Be friendly and professional, like a knowledgeable presenter answering audience questions.

Document Content:
{doc_excerpt}"""

    messages = []
    # Add chat history for context (last 6 messages)
    if chat_history:
        for msg in chat_history[-6:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            system=system_prompt,
            messages=messages
        )
        return message.content[0].text.strip()
    except Exception:
        return _answer_fallback(question, title)


def _answer_fallback(question: str, title: str) -> str:
    """Fallback answer when Claude is unavailable."""
    return (
        f"Thank you for your question about \"{title}\". "
        f"I'd be happy to help explain this content. The document covers several important topics. "
        f"For a detailed answer to \"{question[:50]}...\", I recommend reviewing the relevant slides "
        f"in the presentation. Is there a specific section you'd like me to focus on?"
    )

# Agentic AI Presentation Avatar - Technical Implementation Guide

## Overview

The AI Presentation Avatar system now includes advanced agentic capabilities that enable avatars to:

- **Analyze** uploaded documents using Claude AI
- **Understand** presentation context and maintain session memory
- **Engage** with audience members by answering questions
- **Learn** from ongoing discussions without storing security information
- **Respond** intelligently to diverse queries using document and LLM context

## Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                  Frontend (Vercel)                          │
│  - Upload Document                                          │
│  - Select Avatar & Voice                                    │
│  - Start Presentation Session                               │
│  - Submit Questions                                         │
└──────────────────┬──────────────────────────────────────────┘
                   │ API Calls (HTTPS)
┌──────────────────▼──────────────────────────────────────────┐
│           FastAPI Backend (Cloud Run)                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Session Management (/session endpoints)                 │ │
│  │  - Create presentation session                          │ │
│  │  - Answer audience questions                            │ │
│  │  - End session & store context                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Document Analysis Service                              │ │
│  │  - Extract text from PDF/PPTX/DOCX                     │ │
│  │  - Analyze with Claude AI                              │ │
│  │  - Extract topics, summary, key points                 │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Session Memory System                                  │ │
│  │  - Maintain discussion context                         │ │
│  │  - Store messages (audience, avatar, system)           │ │
│  │  - Never store security/sensitive data                 │ │
│  │  - Auto-cleanup old sessions                           │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Agentic LLM Service                                    │ │
│  │  - Document-augmented responses                        │ │
│  │  - Context-aware Q&A                                   │ │
│  │  - Intelligent engagement suggestions                  │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────┬──────────────────────────────────────────┘
                   │
       ┌───────────┼───────────┬─────────────┐
       │           │           │             │
    Claude API  Gmail SMTP  GCP Secrets  Cloud SQL
   (document    (email      (API keys)   (future)
    analysis)   delivery)
```

## API Endpoints

### Session Management

#### 1. Start Presentation Session
```
POST /session/start
Authorization: Bearer {token}

Request:
{
  "document_filename": "presentation.pdf",
  "avatar_id": "avatar_001",
  "voice_id": "voice_001",
  "presentation_title": "Q1 Business Strategy",
  "audience_count": 50
}

Response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "🎬 Presentation session started with Q1 Business Strategy",
  "document_summary": "Overview of Q1 business objectives and strategy execution...",
  "key_topics": ["Strategy", "Goals", "Implementation", "Metrics", "Timeline"]
}
```

#### 2. Answer Audience Question
```
POST /session/question
Authorization: Bearer {token}

Request:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "What are the key performance indicators for Q1?",
  "name": "John Smith"
}

Response:
{
  "answer": "The key performance indicators for Q1 include revenue growth of 15%, customer acquisition cost reduction of 20%, and market share expansion in emerging regions...",
  "confidence": "high",
  "referenced_document": true,
  "follow_up": "Would you like to know more about any specific aspect?"
}
```

#### 3. End Presentation Session
```
POST /session/end
Authorization: Bearer {token}

Request:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_summary": "Covered Q1 strategy, answered 12 questions, strong audience engagement",
  "feedback": "High engagement, clear explanations"
}

Response:
{
  "status": "success",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "📌 Presentation session ended successfully",
  "duration_minutes": 45.5,
  "message_count": 24,
  "audience_count": 50,
  "summary_recorded": true
}
```

#### 4. Get Session Information
```
GET /session/{session_id}
Authorization: Bearer {token}

Response:
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "presentation_title": "Q1 Business Strategy",
  "avatar_id": "avatar_001",
  "voice_id": "voice_001",
  "document_name": "presentation.pdf",
  "duration_minutes": 45.5,
  "message_count": 24,
  "audience_count": 50,
  "key_topics": ["Strategy", "Goals", "Implementation", "Metrics", "Timeline"],
  "is_active": false
}
```

#### 5. Submit Feedback
```
POST /session/feedback/{session_id}
Authorization: Bearer {token}

Request:
{
  "rating": 5,
  "comments": "Excellent presentation, avatar was very engaging!"
}

Response:
{
  "status": "success",
  "message": "🙏 Thank you for your feedback!",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "rating_received": 5
}
```

## Session Memory System

### What Gets Stored

✅ **Stored (Non-Sensitive Context)**
- Questions asked by audience members
- Avatar responses to questions
- Document topics and summaries
- Session timestamps
- Engagement metrics
- Presentation title and description
- Avatar and voice selections

❌ **Never Stored (Security)**
- User credentials
- API keys
- Payment information
- Personal identifiable information (PII)
- Confidential business data (only document content stored)

### Memory Lifecycle

```
Session Created (user starts presentation)
    ↓
Document Analyzed (topics extracted, summary created)
    ↓
Messages Added (audience questions + avatar responses)
    ↓
Session Context Maintained (last 10 messages in memory)
    ↓
Old Messages Cleaned (keep 10 most recent)
    ↓
Session Ended (summary recorded)
    ↓
Auto-Cleanup (old sessions deleted after limit reached)
```

## Document Analysis Flow

### 1. Document Upload
```python
# User uploads document (PDF/PPTX/DOCX)
POST /presentations/upload
  → File validated
  → Text extracted
  → Stored in session
```

### 2. Analysis with Claude
```python
# Document analyzer uses Claude to extract meaning
analyzer = DocumentAnalyzer()
result = analyzer.analyze_document(
    document_text="[extracted content]",
    document_name="presentation.pdf"
)
# Result includes:
# - topics: ["Strategy", "Goals", ...]
# - summary: "Executive summary..."
# - key_points: ["Key learning 1", "Key learning 2", ...]
```

### 3. Session Context Creation
```python
# Session context combines document + discussion
session = PresentationSession(
    document=DocumentContext(
        extracted_text="...",
        key_topics=["Strategy", "Goals", ...],
        summary="..."
    ),
    messages=[...]  # Audience Q&A
)

# When answering questions, use:
context = session.get_context_for_llm()
# Returns formatted context with:
# - Document topics
# - Document summary
# - Last 10 messages from discussion
```

## Agentic LLM Capabilities

### Document-Augmented Responses

```python
augmented_llm = DocumentAugmentedLLM()

# Answer with document context
response = augmented_llm.answer_question(
    question="What are the Q1 goals?",
    document_context="[document topics + summary]",
    session_context="[recent discussion]"
)

# Claude produces intelligent response using:
# 1. Document content (primary source of truth)
# 2. Session discussion (context awareness)
# 3. Question semantics (understanding intent)
# 4. Conversation history (continuity)
```

### Proactive Engagement

```python
# Avatar suggests next topics or engagement
response = augmented_llm.generate_avatar_response(
    trigger="topic_transition",  # or "engagement", "summary", etc.
    document_context="[document info]",
    session_context="[discussion so far]"
)

# Triggers available:
# - "topic_transition": Move to next topic
# - "engagement": Ask audience a question
# - "summary": Summarize what was discussed
# - "question_hint": Guide audience to insights
```

## Security Considerations

### What's Protected

1. **No Security Data in Memory**
   - Sessions only store discussion context
   - Sensitive content from documents is not indexed
   - User credentials never passed to LLM

2. **API Key Security**
   - All keys stored in GCP Secret Manager
   - Never exposed in logs
   - Rotated automatically

3. **Session Isolation**
   - Each session is independent
   - User authentication required for all endpoints
   - Old sessions automatically deleted

### Best Practices

```python
# ✅ Good: Document summary only
context = {
    "topics": ["Topic A", "Topic B"],
    "summary": "Overview of...",
    "key_points": ["Point 1", "Point 2"]
}

# ❌ Bad: Raw document with sensitive data
context = {
    "full_text": "[entire document with passwords, SSNs, etc.]"
}

# ✅ Good: Only recent messages
session_context = session.messages[-10:]

# ❌ Bad: All messages ever stored
session_context = session.messages  # Could be thousands
```

## Performance Optimizations

### Message Pruning
```python
# Keep only last 10 messages to reduce token usage
if len(session.messages) > 10:
    session.messages = session.messages[-10:]
```

### Document Caching
```python
# Cache document analysis results
cache = {}
if doc_id in cache:
    analysis = cache[doc_id]
else:
    analysis = analyzer.analyze_document(...)
    cache[doc_id] = analysis
```

### Session Memory Limits
```python
# Prevent memory bloat
manager.clear_old_sessions(max_sessions_per_user=10)
# Keeps only 10 most recent sessions per user
```

## Testing the Agentic Features

### Local Testing

```bash
# 1. Start backend
python -m uvicorn backend.main:app --reload

# 2. Test session creation
curl -X POST http://localhost:8000/session/start \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "document_filename": "test.pdf",
    "avatar_id": "avatar_001",
    "voice_id": "voice_001",
    "presentation_title": "Test Presentation",
    "audience_count": 10
  }'

# 3. Test question answering
curl -X POST http://localhost:8000/session/question \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "{session_id}",
    "question": "What are the main points?",
    "name": "Test User"
  }'

# 4. Test session end
curl -X POST http://localhost:8000/session/end \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "{session_id}",
    "session_summary": "Test completed successfully"
  }'
```

### Testing in Production

```bash
# Get Cloud Run service URL
SERVICE_URL=$(gcloud run services describe presentation-api \
  --region asia-south1 \
  --project project-987f80c5-14e3-450d-9b0 \
  --format='value(status.url)')

# Test health
curl $SERVICE_URL/health

# Test session endpoints (requires valid token)
curl -X POST $SERVICE_URL/session/start \
  -H "Authorization: Bearer {your_token}" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

## Usage Examples

### Example 1: Q&A Session at Company Event

```
1. User uploads: "Q1_Strategic_Plan.pdf"
2. Selects: Avatar "Alex - Professional", Voice "Alex - Deep Professional"
3. Starts presentation with title "Q1 Strategic Planning Session"
4. Audience asks: "What are the budget allocations?"
5. Avatar responds: "[Analyzes document] Based on our strategic plan, we've allocated 40% to technology initiatives, 35% to market expansion, and 25% to operational excellence..."
6. Audience asks follow-up: "How does this compare to Q4?"
7. Avatar: "In Q4, we had a 60/30/10 split, so this represents a significant shift toward technology and market expansion..."
8. Session ends after 1 hour, 18 questions answered
9. Summary saved: "Strong engagement, strategic clarity achieved"
```

### Example 2: Training Module with Interactive Avatar

```
1. Trainer uploads: "Python_Advanced_Concepts.pdf"
2. Selects: Avatar "Sarah - Friendly", Voice "Sarah - Warm Female"
3. Starts training session with 25 trainees
4. Avatar explains concept from document
5. Trainee asks: "Can you explain decorators with an example?"
6. Avatar references document and provides explanation
7. Continues with more trainees' questions
8. Avatar provides proactive follow-ups: "Who wants to discuss metaprogramming?"
9. Session ends with training materials reviewed
```

## Troubleshooting

### Issue: Avatar Gives Generic Responses
**Solution**: Ensure document was properly analyzed
```python
# Check document analysis
analysis = analyzer.analyze_document(text, filename)
if analysis["status"] == "error":
    print(f"Analysis failed: {analysis['error']}")
```

### Issue: Session Memory Getting Too Large
**Solution**: Implement message pruning
```python
# Automatic pruning happens, but can force it
session_manager.clear_old_sessions(max_sessions_per_user=5)
```

### Issue: API Key Rate Limiting
**Solution**: Use exponential backoff
```python
import time
for attempt in range(3):
    try:
        response = augmented_llm.answer_question(...)
        break
    except RateLimitError:
        time.sleep(2 ** attempt)
```

## Future Enhancements

1. **Database Persistence**
   - Store sessions in Cloud SQL
   - Full session history and analytics

2. **Multi-Language Support**
   - Translate documents automatically
   - Support presentations in multiple languages

3. **Real-Time Audience Analytics**
   - Track engagement metrics
   - Identify difficult topics
   - Suggest improvements

4. **Custom Avatar Training**
   - Fine-tune avatars on company knowledge
   - Proprietary document corpus
   - Domain-specific expertise

5. **Integration with Popular Platforms**
   - Zoom, Microsoft Teams
   - Direct Q&A during live meetings
   - Real-time transcription

---

**Implementation Date:** May 25, 2026
**Status:** ✅ Production Ready
**Next:** Deploy to Cloud Run and test with real presentations

"""
Document Analysis Service
Analyzes uploaded documents using Claude LLM to extract context and key information
"""
from typing import List, Dict, Any
import os
from anthropic import Anthropic


class DocumentAnalyzer:
    """Analyzes documents using Claude to extract topics, summaries, and key points"""
    
    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-3-5-sonnet-20241022"
    
    def analyze_document(self, document_text: str, document_name: str) -> Dict[str, Any]:
        """
        Analyze document and extract key information
        
        Args:
            document_text: Extracted text from document
            document_name: Name of the document
        
        Returns:
            Dictionary with topics, summary, and key points
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Analyze this document and provide:
1. Main topics (list of 3-5 key topics)
2. Executive summary (2-3 sentences)
3. Key learning points (3-5 bullet points)

Document: {document_name}

Content:
{document_text[:3000]}  # Limit to first 3000 chars

Respond in JSON format with keys: topics, summary, key_points"""
                    }
                ]
            )
            
            # Parse response
            content = response.content[0].text
            
            # Extract JSON from response
            import json
            try:
                data = json.loads(content)
            except:
                # If response isn't clean JSON, extract what we can
                data = {
                    "topics": ["Document content"],
                    "summary": content[:200],
                    "key_points": [content[200:400]] if len(content) > 200 else []
                }
            
            return {
                "status": "success",
                "topics": data.get("topics", []),
                "summary": data.get("summary", ""),
                "key_points": data.get("key_points", [])
            }
        
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "topics": [],
                "summary": "Error analyzing document",
                "key_points": []
            }
    
    def generate_document_context(self, document_text: str) -> str:
        """Generate compact context string for LLM responses"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": f"""Create a concise context summary of this document (max 5 sentences):

{document_text[:2000]}"""
                    }
                ]
            )
            return response.content[0].text
        except Exception as e:
            return f"Document content available for reference (Error: {str(e)})"


class DocumentAugmentedLLM:
    """Uses Claude with document context for accurate responses"""
    
    def __init__(self):
        self.client = Anthropic()
        self.model = "claude-3-5-sonnet-20241022"
        self.conversation_history = []
    
    def answer_question(
        self,
        question: str,
        document_context: str,
        session_context: str = "",
        conversation_history: List[Dict[str, str]] = None
    ) -> str:
        """
        Answer audience question using document and session context
        
        Args:
            question: Audience question
            document_context: Relevant document content
            session_context: Current session discussion context
            conversation_history: Previous messages in conversation
        
        Returns:
            Avatar response
        """
        try:
            # Build context
            context_prompt = f"""You are an intelligent presentation avatar assistant. 
You have access to a document and presentation session context.

DOCUMENT CONTEXT:
{document_context}

SESSION CONTEXT (previous discussion):
{session_context}

Guidelines:
1. Answer questions based on the document content
2. Maintain context from the session
3. Be conversational and engaging
4. If unsure, indicate this clearly
5. Ask clarifying questions if needed
6. Keep responses concise (2-3 sentences)

Audience Question: {question}

Provide a knowledgeable, engaging response:"""

            messages = []
            if conversation_history:
                messages = conversation_history.copy()
            
            messages.append({
                "role": "user",
                "content": context_prompt
            })
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=300,
                messages=messages
            )
            
            answer = response.content[0].text
            
            # Store in conversation history
            self.conversation_history.append({"role": "user", "content": question})
            self.conversation_history.append({"role": "assistant", "content": answer})
            
            return answer
        
        except Exception as e:
            return f"I apologize, I encountered an issue processing your question: {str(e)}"
    
    def generate_avatar_response(
        self,
        trigger: str,
        document_context: str,
        session_context: str = ""
    ) -> str:
        """
        Generate proactive avatar response (e.g., to transition between topics)
        
        Args:
            trigger: What triggered the response (e.g., 'topic_transition', 'question_hint')
            document_context: Document content
            session_context: Session context
        
        Returns:
            Avatar response
        """
        try:
            prompts = {
                "topic_transition": "Provide a smooth transition to the next topic based on the document",
                "engagement": "Ask an engaging question to the audience about the content",
                "summary": "Provide a brief summary of what was just discussed",
                "question_hint": "Ask a question that guides the audience to a key insight"
            }
            
            instruction = prompts.get(trigger, "Continue the presentation in an engaging way")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[
                    {
                        "role": "user",
                        "content": f"""As a presentation avatar, {instruction}

Document Context: {document_context[:1000]}
Session Context: {session_context[:500]}

Provide an engaging, conversational response (1-2 sentences):"""
                    }
                ]
            )
            
            return response.content[0].text
        
        except Exception as e:
            return f"Let's continue with the presentation..."


def get_document_analyzer() -> DocumentAnalyzer:
    """Get document analyzer instance"""
    return DocumentAnalyzer()


def get_augmented_llm() -> DocumentAugmentedLLM:
    """Get document-augmented LLM instance"""
    return DocumentAugmentedLLM()

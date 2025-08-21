#!/usr/bin/env python3
"""
Groq AI Client for SMS conversation assistance
"""
import os
from typing import List, Dict, Any, Optional
import logging
from groq import Groq

logger = logging.getLogger(__name__)

class GroqAIClient:
    """Client for Groq AI API integration"""
    
    def __init__(self, api_key: str, model: str = "llama3-8b-8192"):
        """
        Initialize Groq client
        Args:
            api_key: Groq API key
            model: Model to use (default: llama3-8b-8192)
        """
        self.client = Groq(api_key=api_key)
        self.model = model
        
    async def suggest_sms_response(self, conversation_history: List[Dict[str, str]], context: Optional[str] = None) -> str:
        """
        Suggest a response for SMS conversation
        Args:
            conversation_history: List of messages with 'role' and 'content'
            context: Additional context about the conversation
        Returns:
            Suggested response text
        """
        try:
            # Build the conversation prompt
            system_prompt = self._build_sms_system_prompt(context)
            
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": "Please suggest a helpful and appropriate response to the last message."})
            
            # Get response from Groq
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            suggestion = response.choices[0].message.content.strip()
            logger.info(f"Generated SMS response suggestion: {len(suggestion)} characters")
            return suggestion
            
        except Exception as e:
            logger.error(f"Failed to generate SMS response suggestion: {e}")
            return "I'd be happy to help with that."
    
    async def analyze_message_intent(self, message: str) -> Dict[str, Any]:
        """
        Analyze the intent and sentiment of an incoming message
        Args:
            message: The message to analyze
        Returns:
            Dictionary with intent, sentiment, and confidence scores
        """
        try:
            prompt = f"""
            Analyze this SMS message and provide:
            1. Intent (question, request, complaint, compliment, urgent, casual, etc.)
            2. Sentiment (positive, negative, neutral)
            3. Urgency level (low, medium, high)
            4. Suggested response tone (formal, casual, empathetic, etc.)
            
            Message: "{message}"
            
            Respond in JSON format:
            {{
                "intent": "intent_category",
                "sentiment": "sentiment_value",
                "urgency": "urgency_level",
                "suggested_tone": "response_tone",
                "confidence": 0.95
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.3
            )
            
            # Parse the JSON response
            import json
            analysis = json.loads(response.choices[0].message.content.strip())
            logger.info(f"Analyzed message intent: {analysis.get('intent', 'unknown')}")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze message intent: {e}")
            return {
                "intent": "unknown",
                "sentiment": "neutral", 
                "urgency": "medium",
                "suggested_tone": "casual",
                "confidence": 0.0
            }
    
    async def generate_verification_message(self, service_name: str, verification_code: str) -> str:
        """
        Generate a user-friendly message about a received verification code
        Args:
            service_name: Name of the service (e.g., 'WhatsApp', 'Google')
            verification_code: The verification code received
        Returns:
            Formatted message for the user
        """
        try:
            prompt = f"""
            Create a clear, helpful message to inform a user that they received a verification code.
            
            Service: {service_name}
            Code: {verification_code}
            
            Make it:
            - Clear and concise
            - Professional but friendly
            - Include the code prominently
            - Mention the service name
            - Keep it under 100 characters
            
            Example format: "✅ Your WhatsApp verification code is: 123456. Use this code to complete your registration."
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.5
            )
            
            message = response.choices[0].message.content.strip()
            logger.info(f"Generated verification message for {service_name}")
            return message
            
        except Exception as e:
            logger.error(f"Failed to generate verification message: {e}")
            return f"✅ Your {service_name} verification code is: {verification_code}"
    
    async def help_with_service_setup(self, service_name: str, step: str = "general") -> str:
        """
        Provide contextual help for setting up services
        Args:
            service_name: Name of the service needing help
            step: Specific step or 'general' for overall help
        Returns:
            Helpful instructions
        """
        try:
            prompt = f"""
            Provide helpful, step-by-step guidance for using a verification service.
            
            Service: {service_name}
            Step: {step}
            
            Give practical, actionable advice in a friendly tone.
            Keep it concise but comprehensive.
            Focus on what the user needs to do next.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.6
            )
            
            help_text = response.choices[0].message.content.strip()
            logger.info(f"Generated help text for {service_name}")
            return help_text
            
        except Exception as e:
            logger.error(f"Failed to generate help text: {e}")
            return f"I can help you with {service_name} setup. Please check the service's official documentation for the most up-to-date instructions."
    
    def _build_sms_system_prompt(self, context: Optional[str] = None) -> str:
        """Build system prompt for SMS response suggestions"""
        base_prompt = """
        You are an AI assistant helping with SMS conversations. Your role is to suggest helpful, 
        appropriate, and contextually relevant responses. 
        
        Guidelines:
        - Keep responses concise (SMS-appropriate length)
        - Be helpful and professional
        - Match the tone of the conversation
        - Avoid overly formal language unless the context requires it
        - Consider cultural sensitivity
        - Don't make assumptions about personal information
        """
        
        if context:
            base_prompt += f"\n\nAdditional context: {context}"
            
        return base_prompt


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    # Load from environment variables
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    if not GROQ_API_KEY:
        print("Please set GROQ_API_KEY environment variable")
        exit(1)
    
    async def test_groq_client():
        client = GroqAIClient(GROQ_API_KEY)
        
        try:
            # Test response suggestion
            conversation = [
                {"role": "user", "content": "Hi, I'm interested in your services"},
                {"role": "assistant", "content": "Hello! I'd be happy to help you learn about our communication platform."},
                {"role": "user", "content": "How much does it cost to get a phone number?"}
            ]
            
            suggestion = await client.suggest_sms_response(conversation)
            print(f"Response suggestion: {suggestion}")
            
            # Test intent analysis
            analysis = await client.analyze_message_intent("I need help urgently with my verification!")
            print(f"Intent analysis: {analysis}")
            
            # Test verification message
            verification_msg = await client.generate_verification_message("WhatsApp", "123456")
            print(f"Verification message: {verification_msg}")
            
        except Exception as e:
            print(f"Error testing Groq client: {e}")
    
    # Run the test
    asyncio.run(test_groq_client())
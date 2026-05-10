"""
gemini_client.py - Google Gemini AI Integration for PaasA Numerology AI
Author: Bhavya Sharma | Enrollment: 2450850380 | MCSP-232

Handles:
  - Gemini 2.0 Flash API calls using google-genai SDK
  - Structured JSON response parsing for numerology insights
  - Context-aware chat conversations
  - Graceful fallback when API key is unavailable
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GEMINI_MODEL   = 'gemini-2.5-flash'

# Initialise the Gemini client (new google-genai SDK)
_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        _client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f'Gemini client init failed: {e}')


# ─────────────────────────────────────────────────────────────────────────────
# Insight Generation
# ─────────────────────────────────────────────────────────────────────────────

def generate_insights(user_data: dict) -> dict:
    """
    Generate structured numerology insights using Gemini AI.

    Args:
        user_data: dict with name, dob, gender, numbers, loshu_grid, planes
    Returns:
        dict with 7 insight fields
    """
    if not _client:
        return _get_fallback_insights(user_data)

    name     = user_data.get('name', 'Seeker')
    numbers  = user_data.get('numbers', {})
    planes   = user_data.get('planes', {})
    grid     = user_data.get('loshu_grid', {})
    strongest = planes.get('strongest_plane', 'emotional')
    missing   = grid.get('missing_numbers', [])

    prompt = f"""You are an expert Vedic numerologist with deep knowledge of Chaldean numerology and Lo Shu Grid analysis.

USER PROFILE:
- Name: {name}
- Date of Birth: {user_data.get('dob', '')}
- Gender: {user_data.get('gender', '')}

CORE NUMBERS:
- Name Number (Chaldean): {numbers.get('name_number')}
- Mulank (Driver/Birth): {numbers.get('mulank')}
- Bhagyank (Life Path): {numbers.get('bhagyank')}
- Kua Number (Feng Shui): {numbers.get('kua_number')}

LO SHU GRID:
- Present Numbers: {grid.get('present_numbers', [])}
- Missing Numbers: {missing}
- Strongest Plane: {strongest}

Return ONLY a valid JSON object with exactly these fields:
{{
  "personality_snapshot": "2-3 sentence mystical description of this person's cosmic blueprint",
  "strongest_plane": "{strongest}",
  "strongest_plane_meaning": "What this dominant plane reveals about the person",
  "key_strength": "Greatest natural gift based on their numbers",
  "key_challenge": "Main challenge or lesson they face this lifetime",
  "remedy_suggestion": "Specific numerological remedy for missing numbers {missing}",
  "message": "Personalized welcome message addressing {name} by first name"
}}

Return ONLY the JSON. No markdown, no extra text."""

    try:
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        text = response.text.strip()

        # Strip markdown code fences if present
        if text.startswith('```'):
            lines = text.split('\n')
            text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])

        insights = json.loads(text)
        _validate_insights(insights)
        return insights

    except json.JSONDecodeError as e:
        logger.error(f'Gemini JSON parse error: {e}')
        return _get_fallback_insights(user_data)
    except Exception as e:
        logger.error(f'Gemini API error: {e}')
        return _get_fallback_insights(user_data)


def _validate_insights(insights: dict) -> None:
    required = [
        'personality_snapshot', 'strongest_plane', 'strongest_plane_meaning',
        'key_strength', 'key_challenge', 'remedy_suggestion', 'message',
    ]
    for field in required:
        if field not in insights:
            raise ValueError(f'Missing insight field: {field}')


def _get_fallback_insights(user_data: dict) -> dict:
    """Static fallback when Gemini is unavailable."""
    name     = user_data.get('name', 'Seeker')
    numbers  = user_data.get('numbers', {})
    planes   = user_data.get('planes', {})
    grid     = user_data.get('loshu_grid', {})
    strongest = planes.get('strongest_plane', 'emotional')
    missing   = grid.get('missing_numbers', [])

    plane_meanings = {
        'mental':    'exceptional intellectual capacity and analytical thinking',
        'emotional': 'deep emotional intelligence and spiritual sensitivity',
        'practical': 'strong practical abilities and material manifestation skills',
        'thought':   'visionary planning and innovative ideation',
        'will':      'extraordinary willpower and determination',
        'action':    'efficient execution and result-oriented thinking',
    }

    return {
        'personality_snapshot': (
            f'{name} carries a unique cosmic blueprint shaped by numbers '
            f'{numbers.get("name_number")}, {numbers.get("mulank")}, and '
            f'{numbers.get("bhagyank")}. This combination reveals a soul on a '
            f'meaningful journey of self-discovery and spiritual growth.'
        ),
        'strongest_plane': strongest,
        'strongest_plane_meaning': plane_meanings.get(strongest, 'balanced life energy'),
        'key_strength': (
            f'Your Life Path number {numbers.get("bhagyank")} grants you natural '
            f'wisdom and the ability to inspire others on their journey.'
        ),
        'key_challenge': (
            'Learning to balance material and spiritual pursuits while staying '
            'grounded in your core values and authentic self.'
        ),
        'remedy_suggestion': (
            f'To strengthen missing numbers {missing}, incorporate their colours '
            'and vibrations into daily life through meditation and mindful practices.'
        ),
        'message': (
            f'Welcome, {name}! Your cosmic journey begins here. The universe has '
            'crafted you with purpose and unique gifts. Trust your numbers and embrace '
            'the wisdom they reveal about your divine path.'
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Chat Conversation
# ─────────────────────────────────────────────────────────────────────────────

def chat_with_numerologist(
    user_question: str,
    session_data: dict,
    chat_history: List[Dict[str, str]],
) -> str:
    """
    Generate a context-aware numerology consultation response.

    Args:
        user_question: The user's chat message
        session_data:  Complete numerology data for this session
        chat_history:  Previous messages [{role, message}, ...]
    Returns:
        AI response string
    """
    if not _client:
        return _fallback_chat()

    numbers  = session_data.get('numbers', {})
    insights = session_data.get('insights', {})
    grid     = session_data.get('loshu_grid', {})

    context = f"""You are PaasA — an expert AI numerologist specializing in Chaldean numerology, Lo Shu Grid analysis, and Vedic spiritual guidance. Speak with wisdom, warmth, and mystical authority.

CONSULTING WITH: {session_data.get('full_name', 'Seeker')}
Mulank: {numbers.get('mulank')} | Bhagyank: {numbers.get('bhagyank')} | Name Number: {numbers.get('name_number')} | Kua: {numbers.get('kua_number')}
Strongest Plane: {insights.get('strongest_plane', '')} | Missing Numbers: {grid.get('missing_numbers', [])}
Personality: {insights.get('personality_snapshot', '')}

RULES: Address by first name. Reference specific numbers. Keep response to 150-200 words. End with encouragement."""

    # Build conversation history (last 10 exchanges)
    contents = []
    for msg in chat_history[-10:]:
        role = 'user' if msg['role'] == 'user' else 'model'
        contents.append({'role': role, 'parts': [{'text': msg['message']}]})

    # Append the new user question with context prepended
    contents.append({'role': 'user', 'parts': [{'text': f'{context}\n\nQuestion: {user_question}'}]})

    try:
        response = _client.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f'Gemini chat error: {e}')
        return _fallback_chat()


def _fallback_chat() -> str:
    return (
        'The cosmic energies are momentarily still, dear seeker. '
        'The AI oracle is resting — please add your GEMINI_API_KEY to the .env file '
        'and restart the server to enable AI consultation. '
        'Your numerological blueprint has been calculated and is visible in the Core Numbers tab.'
    )

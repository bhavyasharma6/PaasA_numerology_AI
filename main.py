"""
main.py - FastAPI Application Entry Point for PaasA Numerology AI
Author: Bhavya Sharma | Enrollment: 2450850380 | MCSP-232

RESTful API endpoints:
  POST /api/setup          - Create user profile and calculate numerology
  GET  /api/session/{id}   - Retrieve session data
  POST /api/chat           - Send message to AI numerologist
  GET  /api/history        - Search session history
  GET  /api/history/{id}   - Get full history for session
  DELETE /api/session/{id} - Delete a session
  GET  /health             - Health check endpoint

Run with: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uuid
from datetime import datetime
import logging

from models import UserInput, ChatMessage
from numerology import get_full_numerology
from database import (
    init_db, create_or_get_user, create_session,
    get_session, close_session, delete_session,
    save_numerology_data, get_numerology_data,
    update_insights, save_chat_message, get_chat_history,
    get_chat_message_count, search_sessions_by_name, get_all_sessions
)
from gemini_client import generate_insights, chat_with_numerologist

# ─────────────────────────────────────────────────────────────────────────────
# Application Setup
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title='PaasA Numerology AI',
    description='AI-Powered Cosmic Insights via Chaldean Numerology & Lo Shu Grid',
    version='1.0.0',
    docs_url='/docs',
    redoc_url='/redoc',
)

# CORS Configuration
# Development: allow all origins
# Production: restrict to specific domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],          # Change to specific domain in production
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'DELETE'],
    allow_headers=['*'],
)

# Serve static frontend files
try:
    app.mount('/static', StaticFiles(directory='../frontend'), name='static')
except Exception:
    logger.warning('Frontend static files directory not found')

# Initialize database on startup
@app.on_event('startup')
async def startup_event():
    init_db()
    logger.info('PaasA Numerology AI started. Database initialized.')


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────

@app.get('/health', tags=['System'])
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        'status': 'healthy',
        'service': 'PaasA Numerology AI',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat()
    }


# ─────────────────────────────────────────────────────────────────────────────
# Frontend Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get('/', include_in_schema=False)
async def serve_home():
    """Serve the main landing page."""
    return FileResponse('../frontend/index.html')

@app.get('/input', include_in_schema=False)
async def serve_input():
    """Serve the user input form page."""
    return FileResponse('../frontend/input.html')

@app.get('/dashboard', include_in_schema=False)
async def serve_dashboard():
    """Serve the results dashboard page."""
    return FileResponse('../frontend/dashboard.html')

@app.get('/history', include_in_schema=False)
async def serve_history():
    """Serve the session history page."""
    return FileResponse('../frontend/history.html')


# ─────────────────────────────────────────────────────────────────────────────
# Core API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.post('/api/setup', tags=['Numerology'])
async def setup_numerology(user_input: UserInput):
    """
    Create a new numerology reading for a user.

    Accepts user's name, DOB, and gender.
    Calculates all core numbers, generates Lo Shu Grid,
    performs plane analysis, and calls Gemini AI for insights.

    Returns the complete numerology profile with a session ID.
    """
    try:
        # Step 1: Calculate full numerology profile
        logger.info(f'Processing numerology for: {user_input.full_name}')
        profile = get_full_numerology(
            name=user_input.full_name,
            dob=user_input.dob,
            gender=user_input.gender
        )

        # Step 2: Create/get user and session
        user_id = create_or_get_user(
            user_input.full_name,
            user_input.dob,
            user_input.gender
        )
        session_id = f"{user_input.full_name.replace(' ', '_')}_{int(datetime.now().timestamp())}"
        create_session(user_id, session_id)

        # Step 3: Save numerology data to database
        save_numerology_data(
            session_id=session_id,
            numbers=profile['numbers'],
            loshu_grid=profile['loshu_grid'],
            planes=profile['planes']
        )

        # Step 4: Generate AI insights
        insight_data = {
            'name': user_input.full_name,
            'dob': user_input.dob,
            'gender': user_input.gender,
            'numbers': profile['numbers'],
            'loshu_grid': profile['loshu_grid'],
            'planes': profile['planes'],
        }
        insights = generate_insights(insight_data)
        update_insights(session_id, insights)

        logger.info(f'Session created: {session_id}')

        return {
            'success': True,
            'session_id': session_id,
            'user_name': user_input.full_name,
            'dob': user_input.dob,
            'gender': user_input.gender,
            'numbers': profile['numbers'],
            'name_breakdown': profile['name_breakdown'],
            'loshu_grid': profile['loshu_grid'],
            'planes': profile['planes'],
            'insights': insights,
        }

    except ValueError as e:
        logger.warning(f'Validation error: {e}')
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f'Setup error: {e}', exc_info=True)
        raise HTTPException(status_code=500, detail='Failed to process numerology data')


@app.get('/api/session/{session_id}', tags=['Session'])
async def get_session_data(session_id: str):
    """
    Retrieve complete numerology data for an existing session.

    Returns all calculated numbers, grid data, and insights.
    Used to reload a previous reading.
    """
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')

    num_data = get_numerology_data(session_id)
    if not num_data:
        raise HTTPException(status_code=404, detail='Numerology data not found')

    history = get_chat_history(session_id)

    return {
        'session_id': session_id,
        'user_name': session['full_name'],
        'dob': session['dob'],
        'gender': session['gender'],
        'created_at': session['created_at'],
        'numbers': {
            'name_number': num_data['name_number'],
            'mulank': num_data['mulank'],
            'bhagyank': num_data['bhagyank'],
            'kua_number': num_data['kua_number'],
        },
        'loshu_grid': num_data['loshu_grid'],
        'planes': num_data['planes'],
        'insights': num_data.get('insights'),
        'chat_history': history,
    }


@app.post('/api/chat', tags=['Chat'])
async def chat_endpoint(chat_msg: ChatMessage):
    """
    Send a message to the AI numerologist.

    Uses the session's numerology data as context for
    personalized, relevant responses about destiny,
    relationships, career, and spiritual guidance.
    """
    # Validate session exists
    session = get_session(chat_msg.session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Session not found')

    # Rate limiting: max 50 messages per session per day
    msg_count = get_chat_message_count(chat_msg.session_id)
    if msg_count >= 50:
        raise HTTPException(
            status_code=429,
            detail='Daily message limit reached (50 messages/day per session)'
        )

    # Get numerology context
    num_data = get_numerology_data(chat_msg.session_id)
    if not num_data:
        raise HTTPException(status_code=404, detail='Numerology data not found')

    # Get chat history for context
    history = get_chat_history(chat_msg.session_id, limit=20)

    # Build session context for AI
    session_context = {
        'full_name': session['full_name'],
        'dob': session['dob'],
        'gender': session['gender'],
        'numbers': {
            'name_number': num_data['name_number'],
            'mulank': num_data['mulank'],
            'bhagyank': num_data['bhagyank'],
            'kua_number': num_data['kua_number'],
        },
        'loshu_grid': num_data['loshu_grid'],
        'planes': num_data['planes'],
        'insights': num_data.get('insights', {}),
    }

    # Save user message
    save_chat_message(chat_msg.session_id, 'user', chat_msg.message)

    # Get AI response
    ai_response = chat_with_numerologist(
        user_question=chat_msg.message,
        session_data=session_context,
        chat_history=history
    )

    # Save AI response
    save_chat_message(chat_msg.session_id, 'assistant', ai_response)

    logger.info(f'Chat message processed for session: {chat_msg.session_id}')

    return {
        'response': ai_response,
        'session_id': chat_msg.session_id,
        'timestamp': datetime.utcnow().isoformat()
    }


@app.get('/api/history', tags=['History'])
async def get_history(
    name: str = Query(default='', description='Search by name'),
    limit: int = Query(default=50, ge=1, le=100)
):
    """
    Search and retrieve session history.

    Supports filtering by name with partial match.
    Returns up to 100 records per request.
    """
    if name:
        sessions = search_sessions_by_name(name, limit)
    else:
        sessions = get_all_sessions(limit)

    return {
        'sessions': sessions,
        'total': len(sessions),
        'query': name
    }


@app.delete('/api/session/{session_id}', tags=['Session'])
async def delete_session_endpoint(session_id: str):
    """
    Permanently delete a session and all its associated data.

    Cascades deletion to numerology_data and chat_history tables.
    This action is irreversible.
    """
    success = delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail='Session not found')

    logger.info(f'Session deleted: {session_id}')
    return {'success': True, 'message': f'Session {session_id} deleted successfully'}


# ─────────────────────────────────────────────────────────────────────────────
# Application Entry Point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
        log_level='info'
    )

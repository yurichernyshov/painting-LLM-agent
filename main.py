from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import socketio
import asyncio
from typing import Optional
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

from config import settings
from database import Database
from shapes_manager import ShapesManager
from agent import LLMAgent

app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
socket_app = socketio.ASGIApp(sio, app)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize components
db = Database(settings.DATABASE_URL)
shapes_manager = ShapesManager()
agent = LLMAgent()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# Active user sessions (user_id -> session info)
active_sessions = {}

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except:
        return None

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        return None
    user = db.get_user_by_id(payload.get("sub"))
    return user

@app.get("/", response_class=HTMLResponse)
async def get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")
    # Clean up session
    if sid in active_sessions:
        del active_sessions[sid]

@sio.event
async def register_user(sid, data):
    """Handle user registration"""
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        await sio.emit('auth_response', {
            'success': False,
            'message': 'Username and password are required'
        }, room=sid)
        return
    
    if len(username) < 3:
        await sio.emit('auth_response', {
            'success': False,
            'message': 'Username must be at least 3 characters'
        }, room=sid)
        return
    
    if len(password) < 6:
        await sio.emit('auth_response', {
            'success': False,
            'message': 'Password must be at least 6 characters'
        }, room=sid)
        return
    
    password_hash = get_password_hash(password)
    
    if db.create_user(username, password_hash):
        # Create token
        user = db.get_user(username)
        access_token = create_access_token(data={"sub": user['id'], "username": username})
        
        # Initialize shapes for new user
        preferences = db.get_user_preferences(user['id'])
        shapes = shapes_manager.initialize_for_user(user['id'], preferences)
        
        # Store session
        active_sessions[sid] = {
            'user_id': user['id'],
            'username': username
        }
        
        
        await sio.emit('auth_response', {
            'success': True,
            'message': 'Registration successful!',
            'token': access_token,
            'username': username,
            'user_id': user['id']
        }, room=sid)
        
        await sio.emit('shapes_updated', shapes, room=sid)
 
        # Send welcome message
        welcome_msg = agent.generate_welcome_message(username, preferences)
        await sio.emit('agent_response', {
            'message': welcome_msg,
            'success': True,
            'action': 'welcome'
        }, room=sid)
    else:
        await sio.emit('auth_response', {
            'success': False,
            'message': 'Username already exists'
        }, room=sid)

@sio.event
async def login_user(sid, data):
    """Handle user login"""
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        await sio.emit('auth_response', {
            'success': False,
            'message': 'Username and password are required'
        }, room=sid)
        return
    
    user = db.get_user(username)
    if not user or not verify_password(password, user['password_hash']):
        await sio.emit('auth_response', {
            'success': False,
            'message': 'Invalid username or password'
        }, room=sid)
        return
    
    # Update last login
    db.update_last_login(user['id'])
    
    # Create token
    access_token = create_access_token(data={"sub": user['id'], "username": username})
    
    # Initialize shapes for user
    preferences = db.get_user_preferences(user['id'])
    shapes = shapes_manager.initialize_for_user(user['id'], preferences)
    
    # Store session
    active_sessions[sid] = {
        'user_id': user['id'],
        'username': username
    }
       
    await sio.emit('auth_response', {
        'success': True,
        'message': 'Login successful!',
        'token': access_token,
        'username': username,
        'user_id': user['id']
    }, room=sid)
    
    import pickle
    await sio.emit('shapes_updated', pickle.dumps(shapes), room=sid)

    # Send welcome message
    welcome_msg = agent.generate_welcome_message(username, preferences)
    await sio.emit('agent_response', {
        'message': welcome_msg,
        'success': True,
        'action': 'welcome'
    }, room=sid)

@sio.event
async def chat_message(sid, data):
    """Handle chat messages from authenticated users"""
    # Check if user is authenticated
    if sid not in active_sessions:
        await sio.emit('agent_response', {
            'message': 'Please login first',
            'success': False,
            'action': 'auth_required'
        }, room=sid)
        return
    
    session = active_sessions[sid]
    user_id = session['user_id']
    username = session['username']
    
    user_message = data.get('message', '')
    
    # Get user preferences for context
    preferences = db.get_user_preferences(user_id)
    user_context = {
        'user_id': user_id,
        'username': username,
        'preferences': preferences
    }
    
    # Process command through LLM agent
    result = agent.parse_command(user_message, user_context)
    
    # Handle user identification
    if result['action'] == 'identify_user' and result['username']:
        # User is already identified through login
        await sio.emit('agent_response', {
            'message': f'You are already logged in as {username}!',
            'success': True,
            'action': 'identify_user'
        }, room=sid)
        return
    
    # Execute action on shapes
    shapes_changed = False
    if result['action'] == 'add' and result['shape_type'] and result['color']:
        if shapes_manager.add_shape(user_id, result['shape_type'], result['color']):
            shapes_changed = True
            db.update_shape_count(user_id, result['shape_type'], result['color'], increment=1)
            db.log_shape_action(user_id, result['shape_type'], result['color'], 'add')
    
    elif result['action'] == 'remove' and result['shape_type'] and result['color']:
        if shapes_manager.remove_shape(user_id, result['shape_type'], result['color']):
            shapes_changed = True
            db.update_shape_count(user_id, result['shape_type'], result['color'], increment=-1)
            db.log_shape_action(user_id, result['shape_type'], result['color'], 'remove')
    
    elif result['action'] == 'resize' and result['shape_type'] and result['color']:
        if shapes_manager.resize_shape(user_id, result['shape_type'], result['color'], result['size_change']):
            shapes_changed = True
            db.log_shape_action(user_id, result['shape_type'], result['color'], 'resize')
    
    elif result['action'] == 'clear':
        shapes_manager.clear_shapes(user_id)
        shapes_changed = True
        db.log_shape_action(user_id, 'all', 'all', 'clear')
    
    elif result['action'] == 'help':
        result['message'] = """Available commands:
- Add shape: 'add red circle', 'create blue triangle', 'draw green rectangle'
- Remove shape: 'remove yellow circle', 'delete red rectangle'
- Resize shape: 'make blue triangle bigger', 'make green circle smaller'
- Clear canvas: 'clear', 'reset'
- Show help: 'help'
- Show stats: 'my stats', 'show my shapes'

Allowed shapes: triangle, circle, rectangle
Allowed colors: red, blue, yellow, green"""
    
    # Send updated shapes if changed
    if shapes_changed:
        shapes = shapes_manager.get_shapes(user_id)
        await sio.emit('shapes_updated', shapes, room=sid)
        
        # Update statistics
        stats = db.get_shape_statistics(user_id)
        await sio.emit('stats_updated', stats, room=sid)
    
    # Send agent response
    await sio.emit('agent_response', {
        'message': result['message'],
        'success': result['success'],
        'action': result['action']
    }, room=sid)

@sio.event
async def get_stats(sid):
    """Get user statistics"""
    if sid not in active_sessions:
        await sio.emit('stats_updated', {'error': 'Not authenticated'}, room=sid)
        return
    
    user_id = active_sessions[sid]['user_id']
    stats = db.get_shape_statistics(user_id)
    await sio.emit('stats_updated', stats, room=sid)

@sio.event
async def get_suggestions(sid):
    """Get personalized shape suggestions"""
    if sid not in active_sessions:
        await sio.emit('suggestions_updated', {'error': 'Not authenticated'}, room=sid)
        return
    
    user_id = active_sessions[sid]['user_id']
    username = active_sessions[sid]['username']
    preferences = db.get_user_preferences(user_id)
    
    suggestions = agent.generate_shape_suggestions(username, preferences)
    await sio.emit('suggestions_updated', {'suggestions': suggestions}, room=sid)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)

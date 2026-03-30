# painting-LLM-agent
LLM agent project for testing purposes


# Key Features Implemented
- LLM Processing - Uses Ollama with qwen3:4b model instead of regex
- User Authentication - Login/Register system with JWT tokens
- SQLite Database - Stores user data, preferences, and shape history
- Personalized Experience - Canvas initializes with user's favorite shapes
- Shape Statistics - Track and display number of shapes drawn per user
- Auto-refresh - Canvas updates automatically after each command
- Session Management - Per-user shape canvases
- Welcome Messages - LLM-generated personalized greetings
- Shape Suggestions - AI-powered recommendations based on history

Example User Flow
- User registers/logs in
- System asks "Who are you?" (through login)
- Canvas loads with user's favorite shapes from history
- User says "add red circle"
- LLM processes command, updates database
- Canvas refreshes automatically
- User can view stats showing total shapes drawn
- On next login, canvas shows accumulated shapes


# Setup instructions

1. Install Ollama
# Linux/Mac
curl -fsSL https://ollama.com/install.sh | sh

2. Pull the model
ollama pull qwen3:4b

3. Start Ollama server
ollama server

4. Run a virtual envoronment
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt

5. Start the project
python main.py

6. Run a browser
http://localhost:8000


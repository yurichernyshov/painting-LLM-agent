import ollama
from typing import Optional, Dict, Any
from config import settings

class LLMAgent:
    def __init__(self):
        self.model = settings.OLLAMA_MODEL
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        return """You are a helpful assistant that helps users draw geometric shapes. 
You need to understand user commands and extract the following information:
- Action: add, remove, resize, clear, help, or identify_user
- Shape type: triangle, circle, or rectangle (if mentioned)
- Color: red, blue, yellow, or green (if mentioned)
- Size change: bigger, smaller (if mentioned)
- User identification: extract username if user introduces themselves

Allowed shapes: triangle, circle, rectangle
Allowed colors: red, blue, yellow, green

Respond in JSON format with these fields:
{
    "action": "add/remove/resize/clear/help/identify_user",
    "shape_type": "triangle/circle/rectangle or null",
    "color": "red/blue/yellow/green or null",
    "size_change": 0 (positive for bigger, negative for smaller),
    "username": "extracted username or null",
    "success": true/false,
    "message": "response message for user"
}

Examples:
- "add red circle" -> {"action": "add", "shape_type": "circle", "color": "red", "size_change": 0, "username": null, "success": true, "message": "Added red circle"}
- "make blue triangle bigger" -> {"action": "resize", "shape_type": "triangle", "color": "blue", "size_change": 20, "username": null, "success": true, "message": "Made blue triangle bigger"}
- "I am John" -> {"action": "identify_user", "shape_type": null, "color": null, "size_change": 0, "username": "John", "success": true, "message": "Hello John!"}
- "remove green rectangle" -> {"action": "remove", "shape_type": "rectangle", "color": "green", "size_change": 0, "username": null, "success": true, "message": "Removed green rectangle"}
"""
    
    def parse_command(self, command: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Parse user command using LLM"""
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"User command: {command}"}
                ],
                format='json'
            )
            
            result = response['message']['content']
            import json
            parsed = json.loads(result)
            
            # Validate the response
            required_fields = ['action', 'shape_type', 'color', 'size_change', 'username', 'success', 'message']
            for field in required_fields:
                if field not in parsed:
                    parsed[field] = None
            
            # Validate action
            valid_actions = ['add', 'remove', 'resize', 'clear', 'help', 'identify_user']
            if parsed['action'] not in valid_actions:
                parsed['action'] = None
                parsed['success'] = False
                parsed['message'] = "I didn't understand that command. Try: 'add red circle', 'remove blue triangle', 'make green rectangle bigger', 'clear', or 'help'"
            
            # Validate shape type
            valid_shapes = ['triangle', 'circle', 'rectangle', None]
            if parsed['shape_type'] not in valid_shapes:
                parsed['shape_type'] = None
            
            # Validate color
            valid_colors = ['red', 'blue', 'yellow', 'green', None]
            if parsed['color'] not in valid_colors:
                parsed['color'] = None
            
            return parsed
            
        except Exception as e:
            return {
                'action': None,
                'shape_type': None,
                'color': None,
                'size_change': 0,
                'username': None,
                'success': False,
                'message': f"Error processing command: {str(e)}. Please try again."
            }
    
    def generate_welcome_message(self, username: str, preferences: list) -> str:
        """Generate personalized welcome message based on user preferences"""
        try:
            prefs_text = ""
            if preferences:
                prefs_text = "Based on your history, you've drawn:\n"
                for pref in preferences[:5]:  # Show top 5
                    prefs_text += f"- {pref['count']} {pref['color']} {pref['shape_type']}(s)\n"
                
                if any(p['is_favorite'] for p in preferences):
                    favorites = [p for p in preferences if p['is_favorite']]
                    prefs_text += "\nYour favorites: "
                    prefs_text += ", ".join([f"{f['color']} {f['shape_type']}" for f in favorites])
            else:
                prefs_text = "This is your first time! Let's start drawing."
            
            prompt = f"""Generate a friendly welcome message for user {username}. 
            User preferences history:
            {prefs_text}
            
            Keep it concise (2-3 sentences), friendly, and encouraging."""
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response['message']['content']
            
        except Exception as e:
            return f"Welcome {username}! Let's start drawing shapes."
    
    def generate_shape_suggestions(self, username: str, preferences: list) -> str:
        """Generate personalized shape suggestions based on user history"""
        try:
            if not preferences:
                return "Try: 'add red circle', 'draw blue triangle', or 'create green rectangle'"
            
            # Get most drawn shape
            most_drawn = max(preferences, key=lambda x: x['count'])
            
            prompt = f"""User {username} has drawn {most_drawn['count']} {most_drawn['color']} {most_drawn['shape_type']}(s).
            Suggest 3 new shape combinations they might like to try.
            Keep it brief and friendly."""
            
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response['message']['content']
            
        except Exception as e:
            return "Try adding different colored shapes!"

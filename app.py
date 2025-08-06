from flask import Flask, render_template, request, jsonify
from google import genai
from pydantic import BaseModel, Field
#from langchain_google_genai import ChatGoogleGenerativeAI
import os
from datetime import datetime
import uuid
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class WebGame(BaseModel):
    "The simple web game with HTML code and short explanation."
    html_code : str 
    explanation : str

# gemini_api = "AIzaSyBtw-Ks9__zOwgnEZhOWR59ZN_ckuj58DA"

# llm = ChatGoogleGenerativeAI(
#     model="gemini-2.5-flash-lite",
#     api_key=gemini_api,
#     temperature=0
# )

# structured_llm = llm.with_structured_output(WebGame)


client_thinker = genai.Client()
client_coder = genai.Client()

app = Flask(__name__)

@app.route('/')
def index():
    """Main page where user enters the game prompt"""
    return render_template('index.html')

@app.route('/generate_game', methods=['POST'])
def generate_game():
    """Generate HTML game code using AI"""
    try:
        user_prompt = request.json.get('prompt', '')
        print(f"User prompt is: {user_prompt}")
        game_id = str(uuid.uuid4())
        
        # # Store the generated HTML (in a real app, you might use a database)
        # # For now, we'll store it in memory (this will reset when server restarts)
        if not hasattr(app, 'generated_games'):
            app.generated_games = {}
        
        # ai_msg = structured_llm.invoke("can you create a simple game.")
        # print(ai_msg)


        thinker_prompt1 = """You are a prompt generator for a game-creation AI. You will be given simple problems from subjects like math, physics, or other school topics, typically at the elementary or secondary school level.
            Your task is to design a simple educational game that helps students understand or practice the given concept. The game must be simple enough to be implemented by an AI in a single HTML file with basic JavaScript.
            Then, generate a clear and detailed prompt that will instruct the game-creation AI to build that game.
            Return only the prompt for the game-creation AI — do not include any extra explanations or commentary."""


        response_prompt = client_thinker.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=thinker_prompt1),
            contents=user_prompt
        )

        print(response_prompt.text)

        response = client_coder.models.generate_content(
            model="gemini-2.5-flash",
            contents=response_prompt.text,
            config={
                "response_mime_type": "application/json",
                "response_schema": WebGame,
            },
        )
        
        print(response.parsed.html_code)

        app.generated_games[game_id] = {
            'html': response.parsed.html_code,
            'prompt': user_prompt,
            "Explanation": response.parsed.explanation,
            'created_at': datetime.now()
        }
        
        html_code = response.parsed.html_code

        return jsonify({
            'success': True,
            'game_id': game_id,
            'explanation': response.parsed.explanation,
            'preview': html_code[:200] + '...' if len(html_code) > 200 else html_code
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to generate game: {str(e)}'}), 500

@app.route('/play/<game_id>')
def play_game(game_id):
    """Serve the generated game HTML"""
    if not hasattr(app, 'generated_games'):
        app.generated_games = {}
    
    if game_id not in app.generated_games:
        return "Game not found", 404
    
    game_data = app.generated_games[game_id]
    return game_data['html']

@app.route('/games')
def list_games():
    """List all generated games (optional feature)"""
    if not hasattr(app, 'generated_games'):
        app.generated_games = {}
    
    games = []
    for game_id, data in app.generated_games.items():
        games.append({
            'id': game_id,
            'prompt': data['prompt'],
            'created_at': data['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return render_template('games_list.html', games=games)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
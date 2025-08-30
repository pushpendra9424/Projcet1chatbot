# app.py
from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS chats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_input TEXT,
                  bot_response TEXT,
                  timestamp DATETIME)''')
    conn.commit()
    conn.close()

init_db()

# Simple responses
responses = {
    "नमस्ते": "नमस्ते! मैं कैसे मदद कर सकता हूँ?",
    "तुम्हारा नाम क्या है?": "मैं एक सरलyash hu  चैटबॉट हूँ!", 
    "अलविदा": "ठीक है, बाद में मिलते हैं!"
}

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '').strip()
    response = responses.get(user_input, "मैं इस सवाल का जवाब नहीं जानता")
    
    # Save to DB
    conn = sqlite3.connect('chatbot.db')
    c = conn.cursor()
    c.execute("INSERT INTO chats (user_input, bot_response, timestamp) VALUES (?, ?, ?)",
              (user_input, response, datetime.now()))
    conn.commit()
    conn.close()
    
    return jsonify({"response": response})

if __name__ == '__main__':
    app.run(debug=True)



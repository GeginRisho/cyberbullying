from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import re
import os
import uvicorn
import secrets
from typing import Dict, Any
import json
from deep_translator import GoogleTranslator

app = FastAPI(
    title="Cyberbullying Detection API",
    description="Test your Scikit-learn Multi-Layer Perceptron (MLP) model interactively with WebSockets.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

model = None
vectorizer = None

def clean_text(text):
    text = text.lower()
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'\@\w+|\#', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text

@app.on_event("startup")
def load_model():
    global model, vectorizer
    model_path = "models/mlp_model.pkl"
    vec_path = "models/vectorizer.pkl"
    if os.path.exists(model_path) and os.path.exists(vec_path):
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        with open(vec_path, "rb") as f:
            vectorizer = pickle.load(f)
        print("Successfully loaded MLP Model and Vectorizer!")

@app.get("/")
def home():
    return {"message": "Cyberbullying Detection API Running Successfully"}

# --- ROOM MANAGEMENT ---
# rooms structure: { "room_id": {"password": "pass", "connections": [WebSocket, ...], "history": []} }
rooms: Dict[str, Any] = {}

class CreateRoomRequest(BaseModel):
    password: str

class JoinRoomRequest(BaseModel):
    room_id: str
    password: str

@app.post("/create-room")
def create_room(req: CreateRoomRequest):
    room_id = secrets.token_hex(4) # e.g. 'f9a2b1c4'
    rooms[room_id] = {
        "password": req.password,
        "connections": [],
        "history": []
    }
    return {"room_id": room_id, "message": "Room created successfully"}

@app.post("/verify-room")
def verify_room(req: JoinRoomRequest):
    if req.room_id not in rooms:
        raise HTTPException(status_code=404, detail="Room not found")
    if rooms[req.room_id]["password"] != req.password:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"success": True, "history": rooms[req.room_id]["history"]}

# Global translator instance
translator = GoogleTranslator(source='auto', target='en')

# Helper to check for cyberbullying
def is_message_toxic(original_text: str) -> tuple[bool, str, str, str]:
    if model is None or vectorizer is None:
        return False, "0%", "Safe", original_text
        
    try:
        # Translate to English for the model
        text = translator.translate(original_text)
        # If translation fails or returns none, fallback to original
        if not text:
            text = original_text
    except Exception:
        text = original_text
        
    cleaned = clean_text(text).strip()
    
    # Add a strict heuristic whitelist for common safe greetings 
    # to override the ML bias from the Twitter dataset
    safelist = {"hi", "hii", "hiii", "hello", "hey", "heya", "ok", "okay", "yes", "no", "good", "nice", "cool","are you ok","the", "morning", "how are you"}
    if cleaned in safelist:
        return False, "0.00%", "Safe", text
    
    # If it's empty after cleaning, it's safe
    if not cleaned:
        return False, "0.00%", "Safe", text
        
    # Add a hardcoded blacklist for extremely common severe profanities to bypass ML dilution
    blacklist = {"fuck", "shit", "bitch", "cunt", "nigger", "faggot", "whore", "slut", "asshole", "motherfucker", "bastard","thevidiya","punda","thayoli","kunna","soma"}
    for word in cleaned.split():
        if word in blacklist:
            return True, "100.00%", "100.00%", text
            
    features = vectorizer.transform([cleaned])
    
    # If none of the words in the message are in our trained vocabulary, 
    # the model has no positive evidence, so default to safe instead of relying on bias.
    if features.nnz == 0:
        return False, "0.00%", "Safe", text
        
    probabilities = model.predict_proba(features)[0]
    prob_cyberbullying = probabilities[1]
    
    # Lower the strictness threshold from 0.85 back to 0.55 to catch more cyberbullying words
    is_toxic = bool(prob_cyberbullying > 0.55)
    
    return is_toxic, f"{prob_cyberbullying * 100:.2f}%", f"{max(probabilities) * 100:.2f}%", text

# --- WEBSOCKET FOR CHAT ---
@app.websocket("/ws/{room_id}/{username}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, username: str):
    await websocket.accept()
    if room_id not in rooms:
        await websocket.send_json({"type": "system", "content": "Error: Room does not exist.", "sender": "System"})
        await websocket.close()
        return

    if websocket not in rooms[room_id]["connections"]:
        rooms[room_id]["connections"].append(websocket)
    
    # Announce user joined
    join_msg = {"type": "system", "content": f"{username} joined the chat.", "sender": "System"}
    rooms[room_id]["history"].append(join_msg)
    for conn in rooms[room_id]["connections"]:
        await conn.send_json(join_msg)

    try:
        while True:
            data = await websocket.receive_text()
            # The client sends JSON string: {"content": "hello"}
            try:
                payload = json.loads(data)
                text_content = payload.get("content", "")
            except:
                text_content = data
            
            # Moderate the message
            is_toxic, probability, confidence, translated_text = is_message_toxic(text_content)
            
            if is_toxic:
                # Intercept and block!
                warning_msg = {
                    "type": "error", 
                    "content": f"Message blocked: System detected cyberbullying/toxic language.\n(Translated as: '{translated_text}')", 
                    "sender": "System Administrator",
                    "original_text": text_content,
                    "probability": probability,
                    "confidence": confidence
                }
                # Send ONLY to the sender
                await websocket.send_json(warning_msg)
            else:
                # Safe message - Broadcast to everyone
                chat_msg = {
                    "id": secrets.token_hex(4),
                    "type": "chat",
                    "content": text_content,
                    "sender": username
                }
                rooms[room_id]["history"].append(chat_msg)
                for conn in rooms[room_id]["connections"]:
                    await conn.send_json(chat_msg)

    except WebSocketDisconnect:
        rooms[room_id]["connections"].remove(websocket)
        leave_msg = {"type": "system", "content": f"{username} left the chat.", "sender": "System"}
        rooms[room_id]["history"].append(leave_msg)
        for conn in rooms[room_id]["connections"]:
            await conn.send_json(leave_msg)

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

import { useState, useEffect, useRef } from 'react'
import './App.css'

const API_BASE = "https://cyberbullying-a2nu.onrender.com"
const WS_BASE = "wss://cyberbullying-a2nu.onrender.com/ws"

function App() {
  const [inRoom, setInRoom] = useState(false)
  const [roomId, setRoomId] = useState("")
  const [username, setUsername] = useState("")
  const [chatHistory, setChatHistory] = useState([])
  
  // Lobby State
  const [view, setView] = useState('join') // 'join' or 'create'
  const [joinRoomId, setJoinRoomId] = useState("")
  const [password, setPassword] = useState("")
  const [lobbyError, setLobbyError] = useState("")
  const [loading, setLoading] = useState(false)

  // Chat State
  const [message, setMessage] = useState("")
  const wsRef = useRef(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [chatHistory])

  useEffect(() => {
    // Cleanup simple
    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  const connectWebSocket = (rId, user) => {
   setTimeout(() => {
  const ws = new WebSocket(`${WS_BASE}/${rId}/${user}`)

  ws.onopen = () => {
    setInRoom(true)
    setRoomId(rId)
    setUsername(user)
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    setChatHistory(prev => [...prev, data])
  }

  ws.onclose = () => {
    setInRoom(false)
    setChatHistory(prev => [
      ...prev,
      { type: 'system', content: 'Connection lost to server.' }
    ])
  }

  wsRef.current = ws
}, 8000)
   }

  const handleCreateRoom = async (e) => {
    e.preventDefault()
    if (!password || !username) {
      setLobbyError("Username and password required")
      return
    }
    setLoading(true)
    setLobbyError("")
    try {
      const res = await fetch(`${API_BASE}/create-room`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password })
      })
      if (!res.ok) throw new Error("Failed to create room")
      const data = await res.json()
      connectWebSocket(data.room_id, username)
    } catch (err) {
      setLobbyError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleJoinRoom = async (e) => {
    e.preventDefault()
    if (!joinRoomId || !password || !username) {
      setLobbyError("Room ID, password, and username required")
      return
    }
    setLoading(true)
    setLobbyError("")
    try {
      const res = await fetch(`${API_BASE}/verify-room`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_id: joinRoomId, password })
      })
      
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.detail || "Verification failed")
      }
      
      // Verification successful, sync history and connect
      setChatHistory(data.history)
      connectWebSocket(joinRoomId, username)
      
    } catch (err) {
      setLobbyError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const sendMessage = (e) => {
    e.preventDefault()
    if (!message.trim() || !wsRef.current) return
    
    const payload = { content: message }
    wsRef.current.send(JSON.stringify(payload))
    setMessage("")
  }

  const leaveRoom = () => {
    if (wsRef.current) wsRef.current.close()
    setInRoom(false)
    setRoomId("")
    setChatHistory([])
  }

  if (inRoom) {
    return (
      <div className="app-container">
        <div className="chat-container glass">
          <div className="chat-header">
            <div className="room-info">
              <h2>Secure Room</h2>
              <p>ID: {roomId} | User: {username}</p>
            </div>
            <button className="btn-leave" onClick={leaveRoom}>Leave Room</button>
          </div>
          
          <div className="chat-messages">
            {chatHistory.map((msg, idx) => {
              
              if (msg.type === 'system') {
                return (
                  <div key={idx} className="message-wrapper system">
                    <div className="message-bubble">{msg.content}</div>
                  </div>
                )
              }
              
              if (msg.type === 'error') {
                return (
                  <div key={idx} className="message-wrapper error">
                    <div className="message-bubble">
                      <div className="error-header">
                         🚫 System Alert
                      </div>
                      <div>{msg.content}</div>
                      <div className="error-details">
                        Blocked Content: "{msg.original_text}" <br/>
                        Toxicity Prob: {msg.probability}
                      </div>
                    </div>
                  </div>
                )
              }

              const isMe = msg.sender === username
              return (
                <div key={idx} className={`message-wrapper ${isMe ? 'sent' : 'received'}`}>
                  {!isMe && <div className="sender-name">{msg.sender}</div>}
                  <div className="message-bubble">{msg.content}</div>
                </div>
              )
            })}
            <div ref={messagesEndRef} />
          </div>
          
          <form className="chat-input-area" onSubmit={sendMessage}>
            <input 
              type="text" 
              placeholder="Type a message..." 
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              autoFocus
            />
            <button type="submit" className="btn-send" disabled={!message.trim()}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <div className="app-container">
      <div className="lobby-container glass">
        <h1>CyberSafe Chat</h1>
        
        {lobbyError && <div className="api-error">{lobbyError}</div>}
        
        <div style={{display: 'flex', gap: '10px', marginBottom: '10px'}}>
          <button 
            className="btn" 
            style={{flex: 1, background: view === 'join' ? 'var(--primary)' : 'rgba(255,255,255,0.1)'}}
            onClick={() => setView('join')}
          >
            Join Room
          </button>
          <button 
            className="btn" 
            style={{flex: 1, background: view === 'create' ? 'var(--primary)' : 'rgba(255,255,255,0.1)'}}
            onClick={() => setView('create')}
          >
            Create Room
          </button>
        </div>

        {view === 'join' ? (
          <form className="lobby-section" onSubmit={handleJoinRoom}>
            <h2>Connect to a Room</h2>
            <div className="input-group">
              <input type="text" placeholder="Your Username" value={username} onChange={e => setUsername(e.target.value)} required />
            </div>
            <div className="input-group">
              <input type="text" placeholder="Room ID" value={joinRoomId} onChange={e => setJoinRoomId(e.target.value)} required />
            </div>
            <div className="input-group">
              <input type="password" placeholder="Room Password" value={password} onChange={e => setPassword(e.target.value)} required />
            </div>
            <button type="submit" className="btn" disabled={loading}>
              {loading ? 'Connecting...' : 'Join Room'}
            </button>
          </form>
        ) : (
          <form className="lobby-section" onSubmit={handleCreateRoom}>
            <h2>Start a New Room</h2>
            <div className="input-group">
              <input type="text" placeholder="Your Username" value={username} onChange={e => setUsername(e.target.value)} required />
            </div>
            <div className="input-group">
              <input type="password" placeholder="Create Room Password" value={password} onChange={e => setPassword(e.target.value)} required />
            </div>
            <button type="submit" className="btn" disabled={loading}>
              {loading ? 'Creating...' : 'Create Room'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}

export default App

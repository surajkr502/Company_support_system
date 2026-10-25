import styles from '../styles/chat.module.css'
import { useState } from 'react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const REQUEST_TIMEOUT_MS = 90000 // 90 seconds

// Reads the error message the backend sends, e.g. {"detail": "..."}
async function readErrorDetail(res) {
  try {
    const err = await res.json()
    if (typeof err.detail === 'string') return err.detail
  } catch (_) {
    // response was not JSON, fall through
  }
  return `Server error (${res.status}). Please try again.`
}

export default function Chat() {
  const [messages, setMessages] = useState([])   // conversation history
  const [input, setInput] = useState('')          // current input text
  const [loading, setLoading] = useState(false)   // true while waiting for answer

  async function askQuestion(question) {
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setLoading(true)

    const controller = new AbortController()
    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS)

    let reply
    try {
      const res = await fetch(`${API_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
        signal: controller.signal,
      })

      if (res.ok) {
        const data = await res.json()
        reply = data.answer
      } else {
        reply = await readErrorDetail(res)
      }
    } catch (error) {
      reply = error.name === 'AbortError'
        ? 'The request took too long. Please try again.'
        : 'Could not connect to the server. Make sure the backend is running.'
    } finally {
      clearTimeout(timer)
    }

    setMessages(prev => [...prev, { role: 'assistant', content: reply }])
    setLoading(false)
  }

  function handleInputChange(e) {
    setInput(e.target.value)
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter') {
      handleSubmit()
    }
  }

  function handleSubmit() {
    if (input.trim().length > 0 && !loading) {
      askQuestion(input.trim())
      setInput('')
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.messagesArea}>
        {messages.length === 0 && (
          <div className={styles.emptyState}>
            Ask a question to get started!
          </div>
        )}
        {messages.map((msg, index) => (
          <div
            key={index}
            className={msg.role === 'user' ? styles.userMessage : styles.assistantMessage}
          >
            <div className={styles.messageLabel}>
              {msg.role === 'user' ? 'You' : 'Assistant'}
            </div>
            <div className={styles.messageContent}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className={styles.assistantMessage}>
            <div className={styles.messageLabel}>Assistant</div>
            <div className={styles.thinking}>Thinking...</div>
          </div>
        )}
      </div>

      <div className={styles.inputArea}>
        <input
          className={styles.input}
          placeholder="Ask a question about BigCompany..."
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          disabled={loading}
        />
        <button
          className={styles.askButton}
          onClick={handleSubmit}
          disabled={loading || input.trim().length === 0}
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
      </div>
    </div>
  )
}
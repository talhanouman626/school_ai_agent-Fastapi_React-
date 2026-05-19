import { useState, useRef, useEffect, useCallback } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import MicButton from './MicButton'

const API = 'http://localhost:8000'

const SUGGESTED_TOPICS = [
  { icon: '📋', label: 'Fee details?' },
  { icon: '🎓', label: 'Admission process?' },
  { icon: '⏰', label: 'School timings?' },
  { icon: '📍', label: 'School location?' },
  { icon: '🏫', label: 'Tell me about MGS' },
  { icon: '📜', label: 'School policy?' },
  { icon: '🎨', label: 'What is life like at MGS?' },
  { icon: '📞', label: 'Contact?' },
]

const STORAGE_KEY = 'mgs_chat_messages'
const SESSION_KEY = 'mgs_session_id'

// ── Typing animation ──────────────────────────────────────────
function useTypingEffect(text, speed = 6) {
  const [displayed, setDisplayed] = useState('')
  const [done, setDone] = useState(false)

  useEffect(() => {
    setDisplayed('')
    setDone(false)
    if (!text) return
    let i = 0
    const timer = setInterval(() => {
      i++
      setDisplayed(text.slice(0, i))
      if (i >= text.length) { clearInterval(timer); setDone(true) }
    }, speed)
    return () => clearInterval(timer)
  }, [text, speed])

  return { displayed, done }
}

// ── Follow-up suggestion chips ────────────────────────────────
function FollowUpSuggestions({ suggestions, onSelect }) {
  if (!suggestions || suggestions.length === 0) return null
  return (
    <div className="ml-11 mt-2 flex flex-col gap-1.5">
      <p className="text-white/30 text-xs mb-1">📌 You might also want to know:</p>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((s, i) => (
          <button
            key={i}
            onClick={() => onSelect(s)}
            className="text-xs bg-[#1c2333] border border-blue-500/30 hover:border-blue-400/60
                       hover:bg-[#1e2a3a] text-blue-300 hover:text-blue-200
                       rounded-xl px-3 py-1.5 transition-all duration-150 text-left"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  )
}

// ── User message bubble ───────────────────────────────────────
function UserMessage({ displayContent, originalContent, source }) {
  const isVoice = source === 'voice'
  const hasTranslation = originalContent && originalContent !== displayContent

  return (
    <div className="flex gap-3 justify-end">
      <div className="flex flex-col items-end gap-1 max-w-[75%]">
        <div className="flex items-center gap-1.5">
          {isVoice
            ? <span className="text-xs text-white/30 flex items-center gap-1">
                <span className="inline-block w-1.5 h-1.5 bg-red-400 rounded-full animate-pulse" />
                Voice
              </span>
            : <span className="text-xs text-white/20">Text</span>
          }
        </div>
        <div className="bg-[#2d333b] border border-white/5 text-white
                        rounded-2xl rounded-br-none px-4 py-3 text-sm leading-relaxed shadow-sm">
          {displayContent}
        </div>
        {isVoice && hasTranslation && (
          <div className="text-xs text-white/25 px-1 text-right" dir="rtl">
            {originalContent}
          </div>
        )}
      </div>
      <div className="w-8 h-8 rounded-full flex items-center justify-center
                      shrink-0 mt-1 text-sm shadow-md"
           style={{ background: isVoice ? '#ef4444' : '#dc2626' }}>
        {isVoice ? '🎤' : '👤'}
      </div>
    </div>
  )
}

// ── Bot message bubble ────────────────────────────────────────
function BotMessage({ content, isLatest, suggestions, onSuggestionSelect }) {
  const { displayed, done } = useTypingEffect(isLatest ? content : null, 6)
  const shown = isLatest ? displayed : content
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex flex-col gap-0">
      <div className="group flex gap-3 justify-start">
        <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center
                        justify-center shrink-0 mt-1 text-sm shadow-md">
          🤖
        </div>
        <div className="flex flex-col gap-1 max-w-[75%]">
          <div className="bg-[#1c2128] border border-white/5 text-gray-200
                          rounded-2xl rounded-bl-none px-4 py-3 text-sm leading-relaxed shadow-sm">
            <ReactMarkdown
              components={{
                a: ({ node, ...props }) => (
                  <a {...props} target="_blank" rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 underline underline-offset-2" />
                ),
                table: ({ node, ...props }) => (
                  <div className="overflow-x-auto mt-3 mb-1">
                    <table {...props} className="border-collapse w-full text-xs" />
                  </div>
                ),
                th: ({ node, ...props }) => (
                  <th {...props} className="border border-white/15 px-3 py-2 bg-white/8 text-left font-medium" />
                ),
                td: ({ node, ...props }) => (
                  <td {...props} className="border border-white/10 px-3 py-2" />
                ),
                p:      ({ node, ...props }) => <p      {...props} className="mb-2 last:mb-0" />,
                ul:     ({ node, ...props }) => <ul     {...props} className="list-disc list-inside space-y-1 mb-2 text-gray-300" />,
                ol:     ({ node, ...props }) => <ol     {...props} className="list-decimal list-inside space-y-1 mb-2 text-gray-300" />,
                li:     ({ node, ...props }) => <li     {...props} className="leading-relaxed" />,
                strong: ({ node, ...props }) => <strong {...props} className="text-white font-medium" />,
                h1:     ({ node, ...props }) => <h1     {...props} className="text-base font-semibold mb-2 text-white" />,
                h2:     ({ node, ...props }) => <h2     {...props} className="text-sm font-semibold mb-2 text-white" />,
                h3:     ({ node, ...props }) => <h3     {...props} className="text-sm font-medium mb-1 text-white/90" />,
                code: ({ node, inline, ...props }) => inline
                  ? <code {...props} className="bg-white/10 px-1.5 py-0.5 rounded text-xs font-mono text-blue-300" />
                  : <code {...props} className="block bg-black/30 rounded-lg p-3 text-xs font-mono text-green-300 mt-2 overflow-x-auto" />,
              }}
            >
              {shown}
            </ReactMarkdown>
            {isLatest && !done && (
              <span className="inline-block w-0.5 h-4 bg-blue-400 ml-0.5 animate-pulse align-middle" />
            )}
          </div>
          <button
            onClick={handleCopy}
            className="self-start flex items-center gap-1.5 text-xs text-white/30
                       hover:text-white/70 transition-colors px-1 py-0.5 rounded
                       opacity-0 group-hover:opacity-100"
          >
            {copied
              ? <><span className="text-green-400">✓</span> Copied!</>
              : <><span>📋</span> Copy</>
            }
          </button>
        </div>
      </div>

      {/* Follow-up suggestions — sirf last bot message ke neeche */}
      {(!isLatest || done) && suggestions && suggestions.length > 0 && (
        <FollowUpSuggestions suggestions={suggestions} onSelect={onSuggestionSelect} />
      )}
    </div>
  )
}

// ── Main ChatWindow ───────────────────────────────────────────
export default function ChatWindow({ clearTrigger, onSidebarToggle }) {
  // Priority 2: localStorage se restore karo
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      return saved ? JSON.parse(saved) : []
    } catch { return [] }
  })
  const [input, setInput]             = useState('')
  const [loading, setLoading]         = useState(false)
  const [sessionId, setSessionId]     = useState(() => localStorage.getItem(SESSION_KEY) || null)
  const [chatStarted, setChatStarted] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      const msgs = saved ? JSON.parse(saved) : []
      return msgs.length > 0
    } catch { return false }
  })
  const bottomRef   = useRef(null)
  const textareaRef = useRef(null)

  // localStorage mein save karo jab messages change hon
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
    } catch {}
  }, [messages])

  useEffect(() => {
    if (sessionId) localStorage.setItem(SESSION_KEY, sessionId)
  }, [sessionId])

  useEffect(() => {
    if (clearTrigger > 0) handleClear()
  }, [clearTrigger])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Follow-up suggestions generate karo
  const generateSuggestions = async (userQuery, botReply, llm_hint) => {
    try {
      const res = await axios.post(`${API}/suggestions`, {
        user_query: userQuery,
        bot_reply:  botReply,
      })
      return res.data.suggestions || []
    } catch {
      return []
    }
  }

  const sendMessage = useCallback(async (text, source = 'text') => {
    const msg = (text || input).trim()
    if (!msg || loading) return

    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setChatStarted(true)
    setLoading(true)

    const userMsg = { role: 'user', original: msg, display: msg, source }
    setMessages(prev => [...prev, userMsg])

    try {
      const res = await axios.post(`${API}/chat`, {
        message:    msg,
        session_id: sessionId,
      })

      setSessionId(res.data.session_id)

      // Translated query se display update karo
      const translated = res.data.translated_query
      if (translated && translated !== msg) {
        setMessages(prev => {
          const updated = [...prev]
          const lastUserIdx = updated.map(m => m.role).lastIndexOf('user')
          if (lastUserIdx !== -1) updated[lastUserIdx] = { ...updated[lastUserIdx], display: translated }
          return updated
        })
      }

      // Follow-up suggestions fetch karo
      const suggestions = await generateSuggestions(msg, res.data.reply)

      setMessages(prev => [...prev, {
        role:        'bot',
        content:     res.data.reply,
        suggestions: suggestions,
      }])

    } catch (err) {
      const detail = err.response?.data?.detail || 'Something went wrong. Please try again.'
      setMessages(prev => [...prev, { role: 'bot', content: `⚠️ ${detail}`, suggestions: [] }])
    } finally {
      setLoading(false)
    }
  }, [input, loading, sessionId])

  const handleClear = async () => {
    if (sessionId) {
      await axios.post(`${API}/chat/clear`, { session_id: sessionId }).catch(() => {})
    }
    setMessages([])
    setSessionId(null)
    setChatStarted(false)
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(SESSION_KEY)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input, 'text')
    }
  }

  const handleTextareaInput = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px'
  }

  const lastBotIndex = messages.map(m => m.role).lastIndexOf('bot')

  return (
    <div className="flex flex-col flex-1 min-w-0 h-screen bg-[#0e1117]">

      {/* Header */}
      <div className="shrink-0 px-4 md:px-8 pt-4 pb-3 border-b border-white/8 flex items-center gap-3">
        {/* Hamburger — mobile only */}
        <button
          onClick={onSidebarToggle}
          className="md:hidden w-9 h-9 flex items-center justify-center rounded-lg
                     hover:bg-white/8 text-white/60 hover:text-white transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
            strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
          </svg>
        </button>
        <div className="flex items-center justify-between flex-1">
          <h1 className="text-lg md:text-xl font-semibold text-white tracking-tight">
            🤖 Campus Companion AI
          </h1>
          <span className="hidden md:block text-xs text-white/30 bg-white/5 px-2 py-1 rounded-full border border-white/8">
            MGS Lahore
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-4 scroll-smooth">

        {!chatStarted && (
          <div>
            <p className="text-white/40 text-xs font-medium mb-3 tracking-wide uppercase">
              💡 What would you like to know?
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
              {SUGGESTED_TOPICS.map((t) => (
                <button
                  key={t.label}
                  onClick={() => sendMessage(t.label, 'text')}
                  className="bg-[#161b22] border border-[#30363d] hover:border-blue-500/60
                             hover:bg-[#1c2333] rounded-xl p-3 md:p-3.5 text-left transition-all
                             duration-200 group cursor-pointer"
                >
                  <span className="text-xl block mb-1.5 group-hover:scale-110 transition-transform duration-200">
                    {t.icon}
                  </span>
                  <span className="text-gray-400 group-hover:text-gray-200 text-xs leading-snug transition-colors">
                    {t.label}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) =>
          msg.role === 'user' ? (
            <UserMessage
              key={i}
              displayContent={msg.display}
              originalContent={msg.original}
              source={msg.source}
            />
          ) : (
            <BotMessage
              key={i}
              content={msg.content}
              isLatest={i === lastBotIndex}
              suggestions={msg.suggestions}
              onSuggestionSelect={(s) => sendMessage(s, 'text')}
            />
          )
        )}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center
                            justify-center shrink-0 text-sm shadow-md">🤖</div>
            <div className="bg-[#1c2128] border border-white/5 rounded-2xl
                            rounded-bl-none px-5 py-4 shadow-sm">
              <div className="flex gap-1.5 items-center">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="shrink-0 px-4 md:px-8 py-4 border-t border-white/8 bg-[#0e1117]">
        <div className="flex gap-2.5 items-end bg-[#1c2128] border border-white/8
                        hover:border-white/15 focus-within:border-blue-500/40
                        rounded-2xl px-4 py-3 transition-all duration-200">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            onChange={handleTextareaInput}
            onKeyDown={handleKey}
            placeholder="How can I help you today?"
            className="flex-1 bg-transparent resize-none outline-none text-sm
                       text-white placeholder-white/25 max-h-32 leading-relaxed"
          />
          <div className="flex items-center gap-2 shrink-0">
            <MicButton onTranscript={(text) => sendMessage(text, 'voice')} />
            <button
              onClick={() => sendMessage(input, 'text')}
              disabled={!input.trim() || loading}
              className="w-9 h-9 rounded-full bg-blue-600 hover:bg-blue-500 active:scale-95
                         disabled:opacity-25 disabled:cursor-not-allowed
                         flex items-center justify-center transition-all duration-150 shadow-md"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"
                fill="currentColor" className="w-4 h-4">
                <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0
                         010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519
                         0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
              </svg>
            </button>
          </div>
        </div>
        <p className="text-white/15 text-xs text-center mt-2 hidden md:block">
          Press <kbd className="px-1.5 py-0.5 bg-white/8 rounded text-white/30">Enter</kbd> to send
          &nbsp;·&nbsp;
          <kbd className="px-1.5 py-0.5 bg-white/8 rounded text-white/30">Shift+Enter</kbd> for new line
          &nbsp;·&nbsp; 🎤 for voice
        </p>
      </div>
    </div>
  )
}

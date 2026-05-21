import { useState, useRef, useEffect, useCallback } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import MicButton from './MicButton'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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

// ── Typing animation hook ─────────────────────────────────────
function useTypingEffect(text, speed = 8) {
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
      if (i >= text.length) {
        clearInterval(timer)
        setDone(true)
      }
    }, speed)
    return () => clearInterval(timer)
  }, [text, speed])

  return { displayed, done }
}

// ── Bot message bubble ────────────────────────────────────────
function BotMessage({ content, isLatest }) {
  const { displayed, done } = useTypingEffect(isLatest ? content : null, 6)
  const shown = isLatest ? displayed : content
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="group flex gap-3 justify-start">
      <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center justify-center shrink-0 mt-1 text-sm shadow-md">
        🤖
      </div>
      <div className="flex flex-col gap-1 max-w-[75%]">
        <div className="bg-[#1c2128] border border-white/5 text-gray-200 rounded-2xl rounded-bl-none px-4 py-3 text-sm leading-relaxed shadow-sm">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ node, ...props }) => (
                <a {...props} target="_blank" rel="noopener noreferrer"
                  className="text-blue-400 hover:text-blue-300 underline underline-offset-2" />
              ),
              table: ({ node, ...props }) => (
                <div className="overflow-x-auto my-3 rounded-lg border border-white/10">
                  <table {...props} className="w-full text-xs border-collapse" />
                </div>
              ),
              thead: ({ node, ...props }) => (
                <thead {...props} className="bg-white/8" />
              ),
              th: ({ node, ...props }) => (
                <th {...props} className="px-4 py-2.5 text-left text-white/80 font-medium border-b border-white/10 whitespace-nowrap" />
              ),
              td: ({ node, ...props }) => (
                <td {...props} className="px-4 py-2 text-gray-300 border-b border-white/5" />
              ),
              tr: ({ node, ...props }) => (
                <tr {...props} className="hover:bg-white/3 transition-colors" />
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
          className="self-start flex items-center gap-1.5 text-xs text-white/30 hover:text-white/70 transition-colors px-1 py-0.5 rounded"
        >
          {copied
            ? <><span className="text-green-400">✓</span> Copied!</>
            : <><span>📋</span> Copy</>
          }
        </button>
      </div>
    </div>
  )
}

// ── Backend loading overlay ───────────────────────────────────
function BackendLoader({ step }) {
  const steps = [
    { key: 'embeddings', label: 'Loading AI model...',       icon: '🧠' },
    { key: 'faiss',      label: 'Loading knowledge base...', icon: '📚' },
    { key: 'keys',       label: 'Loading API keys...',       icon: '🔑' },
    { key: 'ready',      label: 'Almost ready...',           icon: '✅' },
  ]
  const currentIdx = steps.findIndex(s => s.key === step)

  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-[#0e1117] gap-6">
      <div className="text-4xl animate-pulse">🤖</div>
      <div className="text-white font-semibold text-lg">AskMGS Assitant Bot</div>
      <div className="text-white/40 text-sm">Starting up, please wait...</div>

      {/* Progress steps */}
      <div className="flex flex-col gap-3 mt-2 w-64">
        {steps.map((s, i) => {
          const done    = i < currentIdx
          const active  = i === currentIdx
          const pending = i > currentIdx
          return (
            <div key={s.key} className={`flex items-center gap-3 text-sm transition-all duration-300
              ${done    ? 'text-green-400'  : ''}
              ${active  ? 'text-white'      : ''}
              ${pending ? 'text-white/20'   : ''}
            `}>
              <span className="text-base w-6 text-center">
                {done ? '✅' : active ? <span className="inline-block animate-spin">⏳</span> : s.icon}
              </span>
              <span>{s.label}</span>
            </div>
          )
        })}
      </div>

      {/* Pulsing bar */}
      <div className="w-64 h-1 bg-white/5 rounded-full overflow-hidden mt-2">
        <div
          className="h-full bg-blue-500 rounded-full transition-all duration-700"
          style={{ width: `${((currentIdx + 1) / steps.length) * 100}%` }}
        />
      </div>
    </div>
  )
}

// ── Main ChatWindow ───────────────────────────────────────────
export default function ChatWindow({ onClear, clearTrigger }) {
  const [messages, setMessages]         = useState([])
  const [input, setInput]               = useState('')
  const [loading, setLoading]           = useState(false)
  const [sessionId, setSessionId]       = useState(null)
  const [chatStarted, setChatStarted]   = useState(false)
  const [backendReady, setBackendReady] = useState(false)
  const [loadStep, setLoadStep]         = useState('embeddings')
  const bottomRef   = useRef(null)
  const textareaRef = useRef(null)
  const pollRef     = useRef(null)

  // ── Backend ready hone tak /health poll karo ───────────────
  useEffect(() => {
    const STEPS = ['embeddings', 'faiss', 'keys', 'ready']
    let stepIdx = 0

    const advance = () => {
      stepIdx = Math.min(stepIdx + 1, STEPS.length - 1)
      setLoadStep(STEPS[stepIdx])
    }

    // Har 1.5s step advance karo (visual progress)
    const stepTimer = setInterval(advance, 1500)

    // Har 2s backend ping karo
    pollRef.current = setInterval(async () => {
      try {
        await axios.get(`${API}/health`, { timeout: 2000 })
        clearInterval(pollRef.current)
        clearInterval(stepTimer)
        setLoadStep('ready')
        setTimeout(() => setBackendReady(true), 600)
      } catch {
        // still loading — keep polling
      }
    }, 2000)

    return () => {
      clearInterval(pollRef.current)
      clearInterval(stepTimer)
    }
  }, [])

  useEffect(() => {
    if (clearTrigger > 0) handleClear()
  }, [clearTrigger])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const sendMessage = useCallback(async (text, isVoice = false) => {
    const msg = (text || input).trim()
    if (!msg || loading || !backendReady) return

    setInput('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
    setChatStarted(true)
    setLoading(true)

    // Voice → English translate for display
    let displayMsg = msg
    if (isVoice) {
      try {
        const t = await axios.post(`${API}/translate`, { text: msg })
        displayMsg = t.data.translated || msg
      } catch {
        displayMsg = msg
      }
    }

    setMessages(prev => [...prev, { role: 'user', content: displayMsg, source: isVoice ? 'voice' : 'text' }])

    try {
      const res = await axios.post(`${API}/chat`, {
        message:    msg,
        session_id: sessionId,
      })
      setSessionId(res.data.session_id)
      setMessages(prev => [...prev, { role: 'bot', content: res.data.reply }])
    } catch (err) {
      const detail = err.response?.data?.detail || 'Something went wrong. Please try again.'
      setMessages(prev => [...prev, { role: 'bot', content: `⚠️ ${detail}` }])
    } finally {
      setLoading(false)
    }
  }, [input, loading, sessionId, backendReady])

  const handleClear = async () => {
    if (sessionId) {
      await axios.post(`${API}/chat/clear`, { session_id: sessionId }).catch(() => {})
    }
    setMessages([])
    setSessionId(null)
    setChatStarted(false)
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleTextareaInput = (e) => {
    setInput(e.target.value)
    e.target.style.height = 'auto'
    e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px'
  }

  const lastBotIndex = messages.map(m => m.role).lastIndexOf('bot')

  // ── Backend loading screen ─────────────────────────────────
  if (!backendReady) return <BackendLoader step={loadStep} />

  // ── Normal chat UI ─────────────────────────────────────────
  return (
    <div className="flex flex-col flex-1 min-w-0 h-screen bg-[#0e1117]">

      {/* Header */}
      <div className="shrink-0 px-8 pt-5 pb-4 border-b border-white/8">
        <div className="flex items-center justify-between">
          <h1 className="text-xl font-semibold text-white tracking-tight">
            🤖 AskMGS Bot
          </h1>
          <span className="text-xs text-white/30 bg-white/5 px-2 py-1 rounded-full border border-white/8">
            MGS Lahore
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-8 py-6 space-y-4 scroll-smooth">

        {/* Suggested topics */}
        {!chatStarted && (
          <div className="animate-fadeIn">
            <p className="text-white/40 text-xs font-medium mb-3 tracking-wide uppercase">
              💡 What would you like to know?
            </p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2.5">
              {SUGGESTED_TOPICS.map((t) => (
                <button
                  key={t.label}
                  onClick={() => sendMessage(t.label)}
                  className="bg-[#161b22] border border-[#30363d] hover:border-blue-500/60
                             hover:bg-[#1c2333] rounded-xl p-3.5 text-left transition-all
                             duration-200 group cursor-pointer"
                >
                  <span className="text-xl block mb-2 group-hover:scale-110 transition-transform duration-200">
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

        {/* Chat messages */}
        {messages.map((msg, i) =>
          msg.role === 'bot' ? (
            <BotMessage key={i} content={msg.content} isLatest={i === lastBotIndex} />
          ) : (
            <div key={i} className="flex gap-3 justify-end">
              <div className="flex flex-col items-end gap-1 max-w-[75%]">
                <div className="bg-[#2d333b] border border-white/5 text-white rounded-2xl rounded-br-none px-4 py-3 text-sm leading-relaxed shadow-sm">
                  {msg.content}
                </div>
                <span className="text-xs text-white/25 flex items-center gap-1 pr-1">
                  {msg.source === 'voice'
                    ? <><span>🎤</span> Voice message</>
                    : <><span>⌨️</span> Text message</>
                  }
                </span>
              </div>
              <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center shrink-0 mt-1 text-sm shadow-md">
                👤
              </div>
            </div>
          )
        )}

        {/* Typing indicator */}
        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center
                            justify-center shrink-0 text-sm shadow-md">🤖</div>
            <div className="bg-[#1c2128] border border-white/5 rounded-2xl rounded-bl-none px-5 py-4 shadow-sm">
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
      <div className="shrink-0 px-8 py-4 border-t border-white/8 bg-[#0e1117]">
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
            <MicButton onTranscript={(text) => sendMessage(text, true)} />
            <button
              onClick={() => sendMessage()}
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
        <p className="text-white/15 text-xs text-center mt-2">
          Press <kbd className="px-1.5 py-0.5 bg-white/8 rounded text-white/30">Enter</kbd> to send
          &nbsp;·&nbsp;
          <kbd className="px-1.5 py-0.5 bg-white/8 rounded text-white/30">Shift+Enter</kbd> for new line
          &nbsp;·&nbsp; 🎤 for voice
        </p>
      </div>
    </div>
  )
}
import { useState, useRef } from 'react'

export default function MicButton({ onTranscript }) {
  const [listening, setListening] = useState(false)
  const [status, setStatus]       = useState('')
  const recRef = useRef(null)

  const toggle = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) {
      alert('Voice input is only supported in Chrome.')
      return
    }

    if (listening) {
      recRef.current?.stop()
      return
    }

    const rec = new SR()
    recRef.current  = rec
    rec.lang           = 'ur-PK'
    rec.interimResults = true
    rec.continuous     = false

    rec.onstart = () => {
      setListening(true)
      setStatus('Listening...')
    }

    rec.onresult = (e) => {
      let interim = ''
      let final   = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) final  += e.results[i][0].transcript
        else                      interim += e.results[i][0].transcript
      }
      setStatus(final || interim)
    }

    rec.onend = () => {
      setListening(false)
      setStatus('')
      const last = recRef.current?._lastFinal
      if (last) onTranscript(last)
    }

    rec.onerror = (e) => {
      setListening(false)
      const msgs = {
        'not-allowed': 'Mic permission denied',
        'no-speech':   'No speech detected',
        'network':     'Network error',
      }
      setStatus(msgs[e.error] || 'Error: ' + e.error)
      setTimeout(() => setStatus(''), 3000)
    }

    // Final transcript track karo
    rec.onresult = (e) => {
      let interim = ''
      let final   = ''
      for (let i = e.resultIndex; i < e.results.length; i++) {
        if (e.results[i].isFinal) final  += e.results[i][0].transcript
        else                      interim += e.results[i][0].transcript
      }
      if (final) rec._lastFinal = final
      setStatus(final || interim || 'Listening...')
    }

    rec.onend = () => {
      setListening(false)
      const transcript = rec._lastFinal || ''
      setStatus('')
      if (transcript.trim()) onTranscript(transcript.trim())
    }

    rec.start()
  }

  return (
    <div className="relative flex items-center">
      {/* Status tooltip */}
      {status && (
        <div className="absolute bottom-12 right-0 bg-[#1e1e2e] border border-white/15
                        rounded-xl px-3 py-2 text-xs text-gray-300 whitespace-nowrap
                        shadow-lg z-50 max-w-[200px] truncate">
          {listening && (
            <span className="inline-block w-2 h-2 bg-red-500 rounded-full mr-2
                             animate-pulse align-middle" />
          )}
          {status}
        </div>
      )}

      <button
        onClick={toggle}
        title={listening ? 'Stop recording' : 'Voice input (Urdu / English)'}
        className={`
          w-9 h-9 rounded-full border flex items-center justify-center
          text-base shrink-0 transition-all duration-200 relative
          ${listening
            ? 'border-red-500 bg-red-500/20 text-red-400 shadow-red'
            : 'border-white/15 bg-white/5 hover:border-white/30 hover:bg-white/10 text-white/60 hover:text-white'
          }
        `}
        style={listening ? {
          boxShadow: '0 0 0 0 rgba(239,68,68,0.4)',
          animation: 'micPulse 1.2s ease-out infinite'
        } : {}}
      >
        {listening ? '⏹️' : '🎤'}
      </button>

      <style>{`
        @keyframes micPulse {
          0%   { box-shadow: 0 0 0 0   rgba(239,68,68,0.5); }
          70%  { box-shadow: 0 0 0 10px rgba(239,68,68,0);   }
          100% { box-shadow: 0 0 0 0   rgba(239,68,68,0);   }
        }
      `}</style>
    </div>
  )
}

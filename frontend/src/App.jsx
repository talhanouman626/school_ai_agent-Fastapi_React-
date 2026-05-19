import { useState, useCallback } from 'react'
import ChatWindow from './components/ChatWindow'
import Sidebar from './components/Sidebar'

export default function App() {
  const [clearTrigger, setClearTrigger]   = useState(0)
  const [sidebarOpen, setSidebarOpen]     = useState(false)

  const handleClear = useCallback(() => {
    setClearTrigger(t => t + 1)
    setSidebarOpen(false)
  }, [])

  return (
    <div className="flex h-screen bg-[#0e1117] text-white overflow-hidden relative">

      {/* Mobile overlay — sidebar ke peeche */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div className={`
        fixed md:relative z-30 h-full
        transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <Sidebar
          onClear={handleClear}
          onClose={() => setSidebarOpen(false)}
        />
      </div>

      {/* Main chat */}
      <ChatWindow
        clearTrigger={clearTrigger}
        onSidebarToggle={() => setSidebarOpen(o => !o)}
      />
    </div>
  )
}

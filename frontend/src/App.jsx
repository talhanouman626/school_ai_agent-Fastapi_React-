import { useState, useCallback } from 'react'
import ChatWindow from './components/ChatWindow'
import Sidebar from './components/Sidebar'

export default function App() {
  const [clearTrigger, setClearTrigger] = useState(0)

  const handleClear = useCallback(() => {
    setClearTrigger(t => t + 1)
  }, [])

  return (
    <div style={{ display: 'flex', height: '100vh', background: '#0e1117', color: 'white', overflow: 'hidden' }}>
      <Sidebar onClear={handleClear} />
      <ChatWindow clearTrigger={clearTrigger} />
    </div>
  )
}

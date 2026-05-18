import { useState } from 'react'

const QUICK_LINKS = [
  { label: 'Official Website', url: 'https://www.mgs.edu.pk/' },
  { label: 'Location Map', url: 'https://www.mgs.edu.pk/contact-us.html' },
  { label: 'WhatsApp Support', url: 'https://wa.me/923041111647' },
]

export default function Sidebar({ onClear }) {
  const today = new Date().toLocaleDateString('en-GB', {
    day: '2-digit', month: 'long', year: 'numeric'
  })

  return (
    <div className="w-64 shrink-0 bg-[#111111] flex flex-col p-4 gap-4 border-r border-white/10">

      {/* Logo + Title */}
      <div className="flex flex-col items-start gap-2 pt-2">
        <img
          src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png"
          alt="logo"
          className="w-14 h-14"
        />
        <span className="text-white font-semibold text-base">Campus Dashboard</span>
      </div>

      <hr className="border-white/10" />

      {/* Status */}
      <div>
        <p className="text-gray-400 text-xs font-semibold mb-2">📣 CURRENT STATUS</p>
        <div className="bg-green-900/40 border border-green-600 rounded-lg px-3 py-2 text-green-400 text-sm mb-2">
          🟢 Campus is Open
        </div>
        <div className="bg-blue-900/40 border border-blue-600 rounded-lg px-3 py-2 text-blue-300 text-sm">
          🕒 08:00 AM – 01:45 PM
        </div>
      </div>

      <hr className="border-white/10" />

      {/* Quick Links */}
      <div>
        <p className="text-gray-400 text-xs font-semibold mb-2">🔗 QUICK ACCESS</p>
        <div className="flex flex-col gap-1">
          {QUICK_LINKS.map(link => (
            <a
              key={link.url}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 text-sm py-1 transition-colors"
            >
              {link.label}
            </a>
          ))}
        </div>
      </div>

      <hr className="border-white/10" />

      {/* Clear button */}
      <button
        onClick={onClear}
        className="w-full border border-red-500 text-red-500 hover:bg-red-500/10 rounded-lg py-2 text-sm font-semibold transition-colors"
      >
        🗑️ Clear Chat History
      </button>

      {/* Footer */}
      <div className="mt-auto text-gray-500 text-xs">
        <p>Sync Date: {today}</p>
      </div>
    </div>
  )
}

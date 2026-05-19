const QUICK_LINKS = [
  { label: '🌐 Official Website', url: 'https://www.mgs.edu.pk/' },
  { label: '📍 Location Map',     url: 'https://www.mgs.edu.pk/contact-us.html' },
  { label: '💬 WhatsApp Support', url: 'https://wa.me/923041111647' },
]

export default function Sidebar({ onClear, onClose }) {
  const today = new Date().toLocaleDateString('en-GB', {
    day: '2-digit', month: 'long', year: 'numeric'
  })

  return (
    <div className="w-64 h-full bg-[#111111] flex flex-col p-4 gap-4 border-r border-white/10">

      {/* Header row — logo + close (mobile only) */}
      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center gap-2.5">
          <img
            src="https://cdn-icons-png.flaticon.com/512/4712/4712035.png"
            alt="logo" className="w-10 h-10"
          />
          <span className="text-white font-semibold text-sm">Campus Dashboard</span>
        </div>
        {/* Close button — sirf mobile pe */}
        <button
          onClick={onClose}
          className="md:hidden w-8 h-8 flex items-center justify-center
                     rounded-lg hover:bg-white/10 text-white/50 hover:text-white transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
            strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <hr className="border-white/10" />

      {/* Status */}
      <div>
        <p className="text-gray-500 text-xs font-semibold mb-2 tracking-wider">📣 CURRENT STATUS</p>
        <div className="bg-green-900/30 border border-green-700/50 rounded-lg px-3 py-2 text-green-400 text-sm mb-2">
          🟢 Campus is Open
        </div>
        <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg px-3 py-2 text-blue-300 text-sm">
          🕒 08:00 AM – 01:45 PM
        </div>
      </div>

      <hr className="border-white/10" />

      {/* Quick Links */}
      <div>
        <p className="text-gray-500 text-xs font-semibold mb-2 tracking-wider">🔗 QUICK ACCESS</p>
        <div className="flex flex-col gap-0.5">
          {QUICK_LINKS.map(link => (
            <a
              key={link.url}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-400 hover:text-blue-300 hover:bg-white/5
                         text-sm py-1.5 px-2 rounded-lg transition-all"
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
        className="w-full border border-red-500/60 text-red-400 hover:bg-red-500/10
                   hover:border-red-400 rounded-lg py-2 text-sm font-medium
                   transition-all duration-150"
      >
        🗑️ Go To DashBoard
      </button>

      {/* Footer */}
      <div className="mt-auto text-gray-600 text-xs">
        <p>Sync Date: {today}</p>
        <p className="mt-1 text-gray-700">MGS Campus Companion AI</p>
      </div>
    </div>
  )
}

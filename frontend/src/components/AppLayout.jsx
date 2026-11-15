import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import Header from './Header.jsx'
import AssistantModal from './AssistantModal.jsx'
import OfflineBanner from './OfflineBanner.jsx'

export default function AppLayout() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false)

  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen">
      <Sidebar isOpen={mobileNavOpen} onClose={() => setMobileNavOpen(false)} />
      <div className="pl-0 lg:pl-72 flex flex-col min-h-screen transition-all duration-200">
        <Header onToggleMobileNav={() => setMobileNavOpen(prev => !prev)} />
        <main className="relative pt-20 pb-8 px-4 sm:px-6 bg-surface min-h-[calc(100vh-4rem)] w-full">
          <OfflineBanner />
          <Outlet />
        </main>
      </div>
      <AssistantModal />
    </div>
  )
}


import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar.jsx'
import Header from './Header.jsx'
import AssistantModal from './AssistantModal.jsx'

export default function AppLayout() {
  return (
    <div className="bg-surface font-body-md text-body-md text-on-surface min-h-screen">
      <Sidebar />
      <div className="pl-72 flex flex-col min-h-screen">
        <Header />
        <main className="relative pt-16 bg-surface min-h-[calc(100vh-4rem)] w-full px-6 py-3">
          <Outlet />
        </main>
      </div>
      <AssistantModal />
    </div>
  )
}


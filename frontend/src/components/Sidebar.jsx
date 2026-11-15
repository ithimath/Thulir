import { NavLink, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext.jsx'
import ThulirLogo from './ThulirLogo.jsx'

const NAV_ITEMS = [
  { key: 'overview',      path: '/overview',       icon: 'dashboard' },
  { key: 'students',      path: '/students',       icon: 'group' },
  { key: 'early_warnings',path: '/early-warnings', icon: 'notification_important' },
  { key: 'support_cases', path: '/support-cases',  icon: 'support_agent' },
  { key: 'reports',       path: '/reports',        icon: 'bar_chart' },
]

const SYSTEM_ITEMS = [
  { key: 'data_import',  path: '/data-import', icon: 'upload_file' },
  { key: 'rules_config', path: '/rules',       icon: 'tune' },
]

export default function Sidebar({ isOpen = false, onClose = () => {} }) {
  const { t } = useTranslation()
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    onClose()
    await logout()
    navigate('/login', { replace: true })
  }

  const navCls = ({ isActive }) =>
    `flex items-center gap-2.5 px-3 py-2 rounded-lg font-label-md text-label-md transition-all duration-150 ${
      isActive
        ? 'bg-gradient-to-r from-teal-600 to-teal-700 text-white font-semibold shadow-sm shadow-teal-950/40 ring-1 ring-teal-400/40'
        : 'text-slate-200 hover:bg-slate-800/70 hover:text-white hover:translate-x-0.5'
    }`

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          role="presentation"
          onClick={onClose}
          className="fixed inset-0 bg-black/60 z-40 lg:hidden backdrop-blur-xs animate-in fade-in duration-200"
        />
      )}

      <aside
        className={`fixed left-0 top-0 h-full w-72 bg-gradient-to-b from-[#0F172A] via-[#131E35] to-[#0A101D] z-50 flex flex-col justify-between shadow-[0_4px_24px_rgba(0,0,0,0.25)] border-r border-slate-800/60 transition-transform duration-200 ${
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Brand Header with Original Logo & Modern Typography */}
          <div className="p-4 flex items-center justify-between bg-gradient-to-r from-slate-900 via-slate-900 to-teal-950/70 border-b border-teal-900/30">
            <div className="flex items-center gap-3">
              <div className="relative p-1.5 rounded-xl bg-slate-950/80 ring-1 ring-teal-500/30 shadow-inner flex items-center justify-center">
                <ThulirLogo size={36} />
              </div>
              <div className="flex flex-col min-w-0">
                <div className="flex items-center gap-1.5">
                  <span className="font-brand font-extrabold text-[21px] text-white tracking-wider leading-none">
                    {t('app.name')}
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-teal-500/20 text-teal-300 ring-1 ring-teal-400/30 font-sans">
                    துளிர்
                  </span>
                </div>
                <span className="text-[11px] font-medium text-slate-300/90 tracking-tight truncate mt-1">
                  {t('app.subtitle')}
                </span>
              </div>
            </div>

            {/* Mobile close button */}
            <button
              onClick={onClose}
              className="lg:hidden text-slate-400 hover:text-white p-1 rounded-lg transition-colors"
              aria-label="Close menu"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>

        {/* Dept. banner */}
        <div className="px-4 py-2 bg-slate-950/60 border-b border-slate-800/40 flex items-center gap-1.5">
          <span className="material-symbols-outlined text-[14px] text-teal-400 flex-shrink-0">verified</span>
          <span className="text-[10.5px] font-medium text-slate-300 block truncate">
            {t('app.department')}
          </span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-4">
          <div className="space-y-1">
            <div className="px-2 py-1 text-[10.5px] font-bold text-slate-400 uppercase tracking-wider">
              {t('nav.navigation_group')}
            </div>
            {NAV_ITEMS.map(({ key, path, icon }) => (
              <NavLink key={key} to={path} onClick={onClose} className={navCls}>
                <span className="material-symbols-outlined text-[19px]">{icon}</span>
                <span className="truncate">{t(`nav.${key}`)}</span>
              </NavLink>
            ))}
          </div>
          <div className="space-y-1">
            <div className="px-2 py-1 text-[10.5px] font-bold text-slate-400 uppercase tracking-wider">
              {t('nav.system_group')}
            </div>
            {SYSTEM_ITEMS.map(({ key, path, icon }) => (
              <NavLink key={key} to={path} onClick={onClose} className={navCls}>
                <span className="material-symbols-outlined text-[19px]">{icon}</span>
                <span className="truncate">{t(`nav.${key}`)}</span>
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Sign out at bottom */}
        <div className="p-3 border-t border-slate-800/60 bg-slate-950/40">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg font-label-md text-label-md text-slate-300 hover:bg-rose-950/40 hover:text-rose-200 hover:ring-1 hover:ring-rose-500/30 transition-all duration-150"
          >
            <span className="material-symbols-outlined text-[18px]">logout</span>
            <span>{t('header.sign_out')}</span>
          </button>
        </div>
      </div>
    </aside>
    </>
  )
}


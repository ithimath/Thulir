import { NavLink, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext.jsx'

const NAV_ITEMS = [
  { key: 'overview',      path: '/overview',       icon: 'dashboard' },
  { key: 'students',      path: '/students',       icon: 'group' },
  { key: 'early_warnings',path: '/early-warnings', icon: 'notification_important' },
  { key: 'support_cases', path: '/support-cases',  icon: 'support_agent' },
  { key: 'reports',       path: '/reports',        icon: 'bar_chart' },
]

const SYSTEM_ITEMS = [
  { key: 'data_import', path: '/data-import', icon: 'upload_file' },
]

export default function Sidebar() {
  const { t } = useTranslation()
  const { logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const navCls = ({ isActive }) =>
    `flex items-center gap-2 px-3 py-2 rounded font-label-md text-label-md transition-colors ${
      isActive
        ? 'bg-secondary text-on-secondary'
        : 'text-primary-fixed hover:bg-surface-tint hover:text-on-primary'
    }`

  return (
    <aside className="fixed left-0 top-0 h-full w-72 bg-primary-container z-50 flex flex-col justify-between shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
      <div className="flex flex-col h-full">
        {/* Logo / App Name */}
        <div className="p-4 flex items-center gap-2 bg-tertiary-container">
          <div className="flex flex-col min-w-0">
            <span className="font-headline-sm text-headline-sm text-on-primary tracking-tight truncate">
              {t('app.name')}
            </span>
            <span className="font-label-sm text-label-sm text-on-primary-container truncate">
              {t('app.subtitle')}
            </span>
          </div>
        </div>

        {/* Dept. banner */}
        <div className="px-4 py-1 bg-inverse-surface">
          <span className="font-label-sm text-label-sm text-inverse-on-surface block truncate">
            {t('app.department')}
          </span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
          <div className="space-y-1">
            <div className="px-2 py-1 font-label-sm text-label-sm text-on-primary-container uppercase tracking-wider">
              {t('nav.navigation_group')}
            </div>
            {NAV_ITEMS.map(({ key, path, icon }) => (
              <NavLink key={key} to={path} className={navCls}>
                <span className="material-symbols-outlined text-[18px]">{icon}</span>
                {t(`nav.${key}`)}
              </NavLink>
            ))}
          </div>
          <div className="space-y-1">
            <div className="px-2 py-1 font-label-sm text-label-sm text-on-primary-container uppercase tracking-wider">
              {t('nav.system_group')}
            </div>
            {SYSTEM_ITEMS.map(({ key, path, icon }) => (
              <NavLink key={key} to={path} className={navCls}>
                <span className="material-symbols-outlined text-[18px]">{icon}</span>
                {t(`nav.${key}`)}
              </NavLink>
            ))}
          </div>
        </nav>

        {/* Sign out at bottom */}
        <div className="p-3 border-t border-on-primary-container/20">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-2 px-3 py-2 rounded font-label-md text-label-md text-primary-fixed hover:bg-surface-tint hover:text-on-primary transition-colors"
          >
            <span className="material-symbols-outlined text-[18px]">logout</span>
            {t('header.sign_out')}
          </button>
        </div>
      </div>
    </aside>
  )
}


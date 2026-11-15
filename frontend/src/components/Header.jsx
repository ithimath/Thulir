import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext.jsx'
import { useTheme } from '../context/ThemeContext.jsx'
import { apiGet } from '../api/client.js'

export default function Header({ onToggleMobileNav }) {
  const { t, i18n } = useTranslation()
  const { user, role } = useAuth()
  const { theme, isDark, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [academicYear, setAcademicYear] = useState(null)
  const [pendingReviewsCount, setPendingReviewsCount] = useState(0)

  useEffect(() => {
    apiGet('/api/academic-year/current')
      .then(data => setAcademicYear(data))
      .catch(() => setAcademicYear(null))

    apiGet('/api/indicators?page_size=1&status=Needs+Review')
      .then(data => setPendingReviewsCount(data?.total || 0))
      .catch(() => setPendingReviewsCount(0))
  }, [])

  const academicLabel = academicYear
    ? `${academicYear.year_name}${academicYear.term_name ? ` • ${academicYear.term_name}` : ''}`
    : (t('header.term') || '2025-26 • Term II')

  const handleSearch = (e) => {
    e.preventDefault()
    if (search.trim()) {
      navigate(`/students?search=${encodeURIComponent(search.trim())}`)
    }
  }

  const toggleLang = () => {
    i18n.changeLanguage(i18n.language === 'ta' ? 'en' : 'ta')
  }

  const roleLabel = role?.role_name === 'admin'
    ? t('header.role_admin')
    : role?.role_name === 'teacher'
      ? t('header.role_teacher')
      : t('header.role_counsellor')

  return (
    <header className="fixed top-0 left-0 lg:left-72 right-0 h-16 bg-surface-container-lowest border-b border-outline-variant/30 shadow-sm z-40 flex items-center justify-between px-4 sm:px-6 transition-colors">
      {/* Left: Hamburger menu + school name + term */}
      <div className="flex items-center gap-2 sm:gap-3 min-w-0 flex-shrink">
        {/* Mobile Hamburger Drawer Button */}
        <button
          type="button"
          onClick={onToggleMobileNav}
          aria-label="Toggle navigation drawer"
          className="lg:hidden p-1.5 -ml-1 rounded-lg text-on-surface-variant hover:text-on-surface hover:bg-surface-container flex items-center justify-center transition-colors flex-shrink-0"
        >
          <span className="material-symbols-outlined text-[24px]">menu</span>
        </button>

        <div className="flex items-center gap-2 font-body-sm text-body-sm text-on-surface-variant min-w-0">
          <span className="material-symbols-outlined text-[20px] text-secondary flex-shrink-0">account_balance</span>
          <span className="font-label-md text-label-md text-on-surface font-semibold tracking-tight truncate max-w-[140px] sm:max-w-xs md:max-w-sm xl:max-w-md" title={role?.school_name || 'Government Higher Secondary School Kovilpatti'}>
            {role?.school_name || 'Government Higher Secondary School Kovilpatti'}
          </span>
          <span className="hidden md:inline-flex text-xs px-2 py-0.5 rounded bg-surface-container text-on-surface-variant font-mono flex-shrink-0">
            UDISE: 33280100412
          </span>
        </div>
        <div className="hidden xl:inline-flex items-center px-2 py-0.5 bg-surface-container rounded text-xs font-medium text-on-surface flex-shrink-0">
          <span>{academicLabel}</span>
        </div>
      </div>

      {/* Right: search, quick actions, theme toggle, lang toggle, user */}
      <div className="flex items-center gap-2 sm:gap-3 flex-shrink-0">
        {/* Search */}
        <form onSubmit={handleSearch} className="relative w-36 sm:w-48 md:w-56 lg:w-64 xl:w-72">
          <span className="material-symbols-outlined absolute left-2.5 top-1/2 -translate-y-1/2 text-[18px] text-outline">search</span>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full h-9 pl-9 pr-3 bg-surface-container-low text-on-surface font-body-sm text-body-sm rounded-lg border border-outline-variant/20 placeholder:text-outline focus:outline-none focus:bg-surface-container-lowest focus:ring-1 focus:ring-secondary transition-all"
            placeholder={t('header.search_placeholder') || 'Search student, EMIS, class...'}
            type="text"
          />
        </form>

        {/* Quick Log Review / Case Action */}
        <button
          onClick={() => navigate('/early-warnings')}
          className="hidden lg:inline-flex items-center gap-1.5 h-9 px-3 bg-secondary/10 hover:bg-secondary/20 text-secondary border border-secondary/30 font-label-md text-xs font-semibold rounded-lg transition-colors flex-shrink-0"
          title="Review Early Warnings / Log Case"
        >
          <span className="material-symbols-outlined text-[16px]">add</span>
          <span>Log Review / Case</span>
        </button>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          aria-label={isDark ? 'Switch to Light Theme' : 'Switch to Dark Theme'}
          className="h-9 px-2.5 rounded-lg border border-outline-variant/30 text-on-surface hover:bg-surface-container flex items-center gap-1.5 font-label-sm text-xs font-medium transition-colors flex-shrink-0"
          title={isDark ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
        >
          <span className="material-symbols-outlined text-[18px] text-secondary">
            {isDark ? 'light_mode' : 'dark_mode'}
          </span>
          <span className="hidden sm:inline">{isDark ? 'Light' : 'Dark'}</span>
        </button>

        {/* Language toggle */}
        <button
          onClick={toggleLang}
          className="h-9 px-2.5 font-label-md text-xs font-semibold text-on-surface-variant hover:text-on-surface rounded-lg border border-outline-variant/30 hover:bg-surface-container transition-colors flex-shrink-0"
          title={t('app.language_switch') || 'Switch Language (EN / தமிழ்)'}
        >
          {i18n.language === 'ta' ? 'English' : 'தமிழ்'}
        </button>

        {/* Notifications */}
        <button
          onClick={() => navigate('/early-warnings')}
          className="relative w-9 h-9 flex items-center justify-center rounded-lg border border-outline-variant/30 text-on-surface-variant hover:bg-surface-container transition-colors flex-shrink-0"
          title={`${pendingReviewsCount} Early Warning Indicators Require Review`}
        >
          <span className="material-symbols-outlined text-[20px]">notifications</span>
          {pendingReviewsCount > 0 && (
            <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-error text-white text-[10px] font-bold flex items-center justify-center shadow-sm">
              {pendingReviewsCount > 99 ? '99+' : pendingReviewsCount}
            </span>
          )}
        </button>

        {/* User info */}
        <div className="flex items-center gap-2 pl-2 border-l border-outline-variant/30 flex-shrink-0">
          <div className="flex flex-col text-right hidden xl:block max-w-[150px]">
            <span className="font-label-md text-sm text-on-surface font-semibold leading-tight truncate block">
              {user?.full_name || 'R. Meenakshi'}
            </span>
            <span className="font-label-sm text-[11px] text-on-surface-variant leading-tight truncate block">
              {roleLabel || 'Head Counselor (M.S.W.)'}
            </span>
          </div>
          <div className="w-8 h-8 rounded-full bg-secondary/15 border border-secondary/30 flex items-center justify-center text-secondary font-bold text-xs flex-shrink-0">
            <span className="material-symbols-outlined text-secondary text-[18px]">person</span>
          </div>
        </div>
      </div>
    </header>
  )
}

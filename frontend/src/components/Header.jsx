import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext.jsx'

export default function Header() {
  const { t, i18n } = useTranslation()
  const { user, role } = useAuth()
  const navigate = useNavigate()
  const [search, setSearch] = useState('')

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
    <header className="fixed top-0 left-72 right-0 h-16 bg-surface-container-lowest shadow-[0_1px_8px_rgba(0,0,0,0.04)] z-40 flex items-center justify-between px-6">
      {/* Left: school name + term */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1 font-body-sm text-body-sm text-on-surface-variant">
          <span className="material-symbols-outlined text-[18px] text-secondary">account_balance</span>
          <span className="font-label-md text-label-md text-on-surface font-semibold">
            {role?.school_name || 'THULIR'}
          </span>
        </div>
        <div className="hidden xl:inline-flex items-center px-2 py-0.5 bg-surface-container rounded">
          <span className="font-label-sm text-label-sm text-on-surface">{t('header.term')}</span>
        </div>
      </div>

      {/* Right: search, lang toggle, user */}
      <div className="flex items-center gap-3">
        {/* Search */}
        <form onSubmit={handleSearch} className="relative w-72">
          <span className="material-symbols-outlined absolute left-2 top-1/2 -translate-y-1/2 text-[18px] text-outline">search</span>
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full h-9 pl-8 pr-3 bg-surface-container-low text-on-surface font-body-sm text-body-sm rounded placeholder-outline focus:outline-none focus:bg-surface-container-lowest focus:ring-1 focus:ring-secondary"
            placeholder={t('header.search_placeholder')}
            type="text"
          />
        </form>

        {/* Language toggle */}
        <button
          onClick={toggleLang}
          className="h-9 px-2 font-label-md text-label-md text-on-surface-variant hover:text-on-surface rounded hover:bg-surface-container transition-colors"
          title={t('app.language_switch')}
        >
          {i18n.language === 'ta' ? 'EN' : 'த'}
        </button>

        {/* User info */}
        <div className="flex items-center gap-2 pl-2">
          <div className="flex flex-col text-right hidden lg:block">
            <span className="font-label-md text-label-md text-on-surface font-medium leading-tight">
              {user?.full_name}
            </span>
            <span className="font-label-sm text-label-sm text-on-surface-variant leading-tight">
              {roleLabel}
            </span>
          </div>
          <div className="w-8 h-8 rounded-full bg-primary-container border border-on-primary-container/20 flex items-center justify-center">
            <span className="material-symbols-outlined text-on-primary text-[18px]">person</span>
          </div>
        </div>
      </div>
    </header>
  )
}


import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import '../i18n/config.js'
import DataImportPage from '../pages/DataImportPage.jsx'
import Header from '../components/Header.jsx'
import AppLayout from '../components/AppLayout.jsx'
import { AuthProvider } from '../context/AuthContext.jsx'
import { ThemeProvider } from '../context/ThemeContext.jsx'
import { NetworkProvider } from '../context/NetworkContext.jsx'
import { NotificationProvider } from '../context/NotificationContext.jsx'

// Mock API client
vi.mock('../api/client.js', () => ({
  apiGet: vi.fn((url) => {
    if (url.includes('/api/import/history')) return Promise.resolve([])
    if (url.includes('/api/data-quality/summary')) {
      return Promise.resolve({
        profile_completeness_pct: 95.0,
        attendance_completeness_pct: 88.0,
        total_issues_count: 2,
        total_students: 1522,
        complete_profiles_count: 1445,
      })
    }
    if (url.includes('/api/data-quality/issues')) {
      return Promise.resolve({ items: [] })
    }
    return Promise.resolve({})
  }),
  apiPost: vi.fn(() => Promise.resolve({ success: true })),
  apiUpload: vi.fn(() => Promise.resolve({
    batch_id: 101,
    file_name: 'test.csv',
    total_rows: 5,
    valid_count: 5,
    warnings_count: 0,
    rejected_count: 0,
    duplicates_count: 0,
    row_issues: [],
    sample_preview: [],
  })),
}))

// Mock Auth Context
vi.mock('../context/AuthContext.jsx', () => ({
  AuthProvider: ({ children }) => children,
  useAuth: () => ({
    user: { full_name: 'Administrator' },
    role: { role_name: 'admin', school_name: 'Government Higher Secondary School Kovilpatti' },
    isAuthenticated: true,
  }),
}))

describe('Data Import Page & Layout Integration', () => {
  it('renders DataImportPage without crashing or ReferenceErrors', async () => {
    render(
      <MemoryRouter initialEntries={['/data-import']}>
        <ThemeProvider>
          <NotificationProvider>
            <DataImportPage />
          </NotificationProvider>
        </ThemeProvider>
      </MemoryRouter>
    )

    // Verify main headings and upload elements exist
    expect(screen.getByText(/Upload & Validate/i)).toBeInTheDocument()
    expect(screen.getByText(/Recent Import History/i)).toBeInTheDocument()
    expect(screen.getByText(/Import Data Domain/i)).toBeInTheDocument()
  })

  it('switches between Data Import and Data Quality tabs smoothly', async () => {
    render(
      <MemoryRouter initialEntries={['/data-import']}>
        <ThemeProvider>
          <NotificationProvider>
            <DataImportPage />
          </NotificationProvider>
        </ThemeProvider>
      </MemoryRouter>
    )

    // Find and click the Data Quality Monitor tab
    const qualityTabButton = screen.getByRole('button', { name: /Quality/i })
    fireEvent.click(qualityTabButton)

    // Verify quality monitor elements appear
    expect(await screen.findByText(/Audit Findings/i)).toBeInTheDocument()
    expect(screen.getByText(/Data Trust Principle/i)).toBeInTheDocument()
  })

  it('renders Header with responsive layout and theme toggle', () => {
    render(
      <MemoryRouter>
        <ThemeProvider>
          <Header />
        </ThemeProvider>
      </MemoryRouter>
    )

    // Verify school name, search input, and theme buttons exist
    expect(screen.getByText(/Government Higher Secondary School Kovilpatti/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Search student/i)).toBeInTheDocument()
    expect(screen.getByTitle(/Switch to Dark Mode|Switch to Light Mode/i)).toBeInTheDocument()
  })

  it('AppLayout contains top padding to avoid header overlapping', () => {
    const { container } = render(
      <MemoryRouter>
        <ThemeProvider>
          <NetworkProvider>
            <AppLayout />
          </NetworkProvider>
        </ThemeProvider>
      </MemoryRouter>
    )

    const mainElement = container.querySelector('main')
    expect(mainElement).not.toBeNull()
    // Verify pt-20 exists in main classes
    expect(mainElement.className).toContain('pt-20')
  })
})

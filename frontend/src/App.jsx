import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext.jsx'
import AppLayout from './components/AppLayout.jsx'
import LoginPage from './pages/LoginPage.jsx'
import OverviewPage from './pages/OverviewPage.jsx'
import StudentDirectoryPage from './pages/StudentDirectoryPage.jsx'
import StudentProfilePage from './pages/StudentProfilePage.jsx'
import WarningReviewPage from './pages/WarningReviewPage.jsx'
import SupportCasesPage from './pages/SupportCasesPage.jsx'
import ReportsPage from './pages/ReportsPage.jsx'
import DataImportPage from './pages/DataImportPage.jsx'

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen bg-surface flex items-center justify-center">
        <span className="material-symbols-outlined text-[32px] text-secondary animate-spin">progress_activity</span>
      </div>
    )
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return children
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Navigate to="/overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="students" element={<StudentDirectoryPage />} />
          <Route path="students/:studentId" element={<StudentProfilePage />} />
          <Route path="early-warnings" element={<WarningReviewPage />} />
          <Route path="support-cases" element={<SupportCasesPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="data-import" element={<DataImportPage />} />
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

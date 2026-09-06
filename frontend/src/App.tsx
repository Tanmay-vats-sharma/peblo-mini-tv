import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthProvider'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { CmsLayout } from './components/CmsLayout'
import { CmsHomePage } from './pages/CmsHomePage'
import { EpisodeManagementPage } from './pages/EpisodeManagementPage'
import { LoginPage } from './pages/LoginPage'
import { PermissionDeniedPage } from './pages/PermissionDeniedPage'
import { PublicHomePage } from './pages/PublicHomePage'
import { SeasonManagementPage } from './pages/SeasonManagementPage'
import { ShowEditorPage } from './pages/ShowEditorPage'
import { ShowsPage } from './pages/ShowsPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route path="/" element={<PublicHomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/forbidden" element={<PermissionDeniedPage />} />
            <Route element={<ProtectedRoute allowedRoles={['admin', 'editor']} />}>
              <Route path="/admin" element={<CmsLayout />}>
                <Route index element={<CmsHomePage />} />
                <Route path="shows" element={<ShowsPage />} />
                <Route path="shows/new" element={<ShowEditorPage />} />
                <Route path="shows/:showId/edit" element={<ShowEditorPage />} />
                <Route path="shows/:showId/seasons" element={<SeasonManagementPage />} />
                <Route path="seasons/:seasonId/episodes" element={<EpisodeManagementPage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App

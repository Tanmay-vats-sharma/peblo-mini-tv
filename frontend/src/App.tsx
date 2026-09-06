import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './auth/AuthProvider'
import { ProtectedRoute } from './auth/ProtectedRoute'
import { CmsLayout } from './components/CmsLayout'
import { PublicLayout } from './components/PublicLayout'
import { CataloguePage } from './pages/CataloguePage'
import { CmsHomePage } from './pages/CmsHomePage'
import { EpisodeManagementPage } from './pages/EpisodeManagementPage'
import { LoginPage } from './pages/LoginPage'
import { PermissionDeniedPage } from './pages/PermissionDeniedPage'
import { PublishHistoryPage } from './pages/PublishHistoryPage'
import { PublicHomePage } from './pages/PublicHomePage'
import { ShowDetailsPage } from './pages/ShowDetailsPage'
import { SeasonManagementPage } from './pages/SeasonManagementPage'
import { ShowEditorPage } from './pages/ShowEditorPage'
import { ShowsPage } from './pages/ShowsPage'
import { ValidationPage } from './pages/ValidationPage'

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false, refetchOnWindowFocus: false } },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route element={<PublicLayout />}>
              <Route path="/" element={<PublicHomePage />} />
              <Route path="/catalog" element={<CataloguePage />} />
              <Route path="/catalog/search" element={<CataloguePage searchOnly />} />
              <Route path="/catalog/shows/:slug" element={<ShowDetailsPage />} />
            </Route>
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
                <Route path="validation" element={<ValidationPage />} />
                <Route path="publish-history" element={<PublishHistoryPage />} />
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

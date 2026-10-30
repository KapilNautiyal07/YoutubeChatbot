import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { ProviderProvider } from './context/ProviderContext'
import { HomePage } from './pages/HomePage'
import { NotFoundPage } from './pages/NotFoundPage'
import { VideoPage } from './pages/VideoPage'

export default function App() {
  return (
    <ProviderProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/videos/:id" element={<VideoPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </BrowserRouter>
    </ProviderProvider>
  )
}

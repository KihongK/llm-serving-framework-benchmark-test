import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import DashboardPage from './pages/DashboardPage'
import ResultsPage from './pages/ResultsPage'
import BenchmarkPage from './pages/BenchmarkPage'
import HypothesisPage from './pages/HypothesisPage'
import { BenchmarkProvider } from './hooks/useBenchmarkContext'

export default function App() {
  return (
    <BrowserRouter>
      <BenchmarkProvider>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/results" element={<ResultsPage />} />
            <Route path="/benchmark" element={<BenchmarkPage />} />
            <Route path="/hypotheses" element={<HypothesisPage />} />
          </Route>
        </Routes>
      </BenchmarkProvider>
    </BrowserRouter>
  )
}

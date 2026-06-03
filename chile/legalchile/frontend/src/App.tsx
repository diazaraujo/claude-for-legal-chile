import { Routes, Route } from 'react-router-dom'
import Home from '@/pages/Home'
import Analisis from '@/pages/Analisis'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/analisis" element={<Analisis />} />
    </Routes>
  )
}

import { Routes, Route } from 'react-router-dom'
import Home from '@/pages/Home'
import Analisis from '@/pages/Analisis'
import Buscar from '@/pages/Buscar'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/buscar" element={<Buscar />} />
      <Route path="/analisis" element={<Analisis />} />
    </Routes>
  )
}

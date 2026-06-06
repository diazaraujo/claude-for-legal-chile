import { Routes, Route } from 'react-router-dom'
import Home from '@/pages/Home'
import Analisis from '@/pages/Analisis'
import Buscar from '@/pages/Buscar'
import Entidad from '@/pages/Entidad'
import Sobre from '@/pages/Sobre'
import Login from '@/pages/Login'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/buscar" element={<Buscar />} />
      <Route path="/analisis" element={<Analisis />} />
      <Route path="/sobre" element={<Sobre />} />
      <Route path="/jueces" element={<Entidad tipo="jueces" />} />
      <Route path="/abogados" element={<Entidad tipo="abogados" />} />
      <Route path="/fiscales" element={<Entidad tipo="fiscales" />} />
      <Route path="/tribunales" element={<Entidad tipo="tribunales" />} />
      <Route path="/empresas" element={<Entidad tipo="empresas" />} />
    </Routes>
  )
}

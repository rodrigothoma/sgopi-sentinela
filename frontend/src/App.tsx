import { Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import './i18n';
import './styles.css';
import { AppShell } from './components/layout/AppShell';
import { RequireRole, rotaInicial } from './components/RequireRole';
import { AuthProvider, useAuth } from './hooks/useAuth';
import { ToastProvider } from './hooks/useToast';
import { FilaDelegadoPage } from './pages/FilaDelegadoPage';
import { FrotaPage } from './pages/FrotaPage';
import { LoginPage } from './pages/LoginPage';
import { MinhasOcorrenciasPage } from './pages/MinhasOcorrenciasPage';
import { PainelTaticoPage } from './pages/PainelTaticoPage';
import { RegistrarOcorrenciaPage } from './pages/RegistrarOcorrenciaPage';

const Inicio = () => {
  const { usuario } = useAuth();
  return <Navigate to={usuario ? rotaInicial(usuario.papel) : '/login'} replace />;
};

const Carregando = () => {
  const { t } = useTranslation();
  return <div style={{ padding: 24 }}>{t('actions.loading')}</div>;
};

export default function App() {
  return (
    <Suspense fallback={<Carregando />}>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<RequireRole><AppShell /></RequireRole>}>
                <Route path="/" element={<Inicio />} />
                <Route path="/registrar" element={<RequireRole papeis={['AGENTE']}><RegistrarOcorrenciaPage /></RequireRole>} />
                <Route path="/minhas" element={<RequireRole papeis={['AGENTE']}><MinhasOcorrenciasPage /></RequireRole>} />
                <Route path="/fila" element={<RequireRole papeis={['DELEGADO', 'SUPERVISOR']}><FilaDelegadoPage /></RequireRole>} />
                <Route path="/painel" element={<RequireRole papeis={['OPERADOR_CENTRAL', 'SUPERVISOR', 'DELEGADO']}><PainelTaticoPage /></RequireRole>} />
                <Route path="/frota" element={<RequireRole papeis={['OPERADOR_CENTRAL', 'SUPERVISOR']}><FrotaPage /></RequireRole>} />
              </Route>
              <Route path="*" element={<Inicio />} />
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </Suspense>
  );
}

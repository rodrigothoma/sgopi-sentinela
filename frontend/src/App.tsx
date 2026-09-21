import { Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import './i18n';
import './styles.css';
import { AppShell } from './components/layout/AppShell';
import { RequireRole } from './components/RequireRole';
import { AuthProvider } from './hooks/useAuth';
import { ThemeProvider } from './hooks/useTheme';
import { ToastProvider } from './hooks/useToast';
import { LandingPage } from './pages/LandingPage';
import { RegistroCidadaoPage } from './pages/RegistroCidadaoPage';
import { ConsultaPublicaPage } from './pages/ConsultaPublicaPage';
import { LoginPage } from './pages/LoginPage';
import { FilaDelegadoPage } from './pages/FilaDelegadoPage';
import { FrotaPage } from './pages/FrotaPage';
import { MinhasOcorrenciasPage } from './pages/MinhasOcorrenciasPage';
import { PainelTaticoPage } from './pages/PainelTaticoPage';
import { RegistrarOcorrenciaPage } from './pages/RegistrarOcorrenciaPage';
import { TrilhaAuditoriaPage } from './pages/TrilhaAuditoriaPage';

const Carregando = () => {
  const { t } = useTranslation();
  return <div style={{ padding: 24 }}>{t('actions.loading')}</div>;
};

export default function App() {
  return (
    <Suspense fallback={<Carregando />}>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>
            <BrowserRouter>
              <Routes>
                {/* Rotas Públicas do Portal Cidadão */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/registrar-cidadao" element={<RegistroCidadaoPage />} />
                <Route path="/login" element={<LoginPage />} />

                {/* Consulta pública unificada: protocolo (acompanhamento) e chave de autenticidade (RF08).
                    Fora do RequireRole por definição (UC08 regra 1); /autenticar/:chave é o deep-link do QR Code. */}
                <Route path="/consulta" element={<ConsultaPublicaPage />} />
                <Route path="/autenticar" element={<Navigate to="/consulta?modo=chave" replace />} />
                <Route path="/autenticar/:chave" element={<ConsultaPublicaPage />} />

                {/* Rotas Restritas Protegidas (RBAC Policial) */}
                <Route element={<RequireRole><AppShell /></RequireRole>}>
                  <Route path="/registrar" element={<RequireRole papeis={['AGENTE']}><RegistrarOcorrenciaPage /></RequireRole>} />
                  <Route path="/minhas" element={<RequireRole papeis={['AGENTE']}><MinhasOcorrenciasPage /></RequireRole>} />
                  <Route path="/fila" element={<RequireRole papeis={['DELEGADO', 'SUPERVISOR']}><FilaDelegadoPage /></RequireRole>} />
                  <Route path="/painel" element={<RequireRole papeis={['OPERADOR_CENTRAL', 'SUPERVISOR', 'DELEGADO']}><PainelTaticoPage /></RequireRole>} />
                  <Route path="/frota" element={<RequireRole papeis={['OPERADOR_CENTRAL', 'SUPERVISOR']}><FrotaPage /></RequireRole>} />
                  <Route path="/auditoria" element={<RequireRole papeis={['DELEGADO', 'SUPERVISOR']}><TrilhaAuditoriaPage /></RequireRole>} />
                </Route>

                {/* Redirecionamento padrão */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </BrowserRouter>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </Suspense>
  );
}

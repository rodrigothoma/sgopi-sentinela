import { lazy, Suspense } from 'react';
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

// Divisão de código por rota (N6): o cidadão em /registrar-cidadao ou /autenticar não baixa Leaflet nem as
// páginas internas; cada página vira um chunk carregado sob demanda.
const AutenticarDocumentoPage = lazy(() => import('./pages/AutenticarDocumentoPage').then((m) => ({ default: m.AutenticarDocumentoPage })));
const ConsultaProtocoloPage = lazy(() => import('./pages/ConsultaProtocoloPage').then((m) => ({ default: m.ConsultaProtocoloPage })));
const FilaDelegadoPage = lazy(() => import('./pages/FilaDelegadoPage').then((m) => ({ default: m.FilaDelegadoPage })));
const FrotaPage = lazy(() => import('./pages/FrotaPage').then((m) => ({ default: m.FrotaPage })));
const InicioPage = lazy(() => import('./pages/InicioPage').then((m) => ({ default: m.InicioPage })));
const InqueritosPage = lazy(() => import('./pages/InqueritosPage').then((m) => ({ default: m.InqueritosPage })));
const LaudosPage = lazy(() => import('./pages/LaudosPage').then((m) => ({ default: m.LaudosPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then((m) => ({ default: m.LoginPage })));
const MedidasProtetivasPage = lazy(() => import('./pages/MedidasProtetivasPage').then((m) => ({ default: m.MedidasProtetivasPage })));
const MinhasOcorrenciasPage = lazy(() => import('./pages/MinhasOcorrenciasPage').then((m) => ({ default: m.MinhasOcorrenciasPage })));
const PainelTaticoPage = lazy(() => import('./pages/PainelTaticoPage').then((m) => ({ default: m.PainelTaticoPage })));
const RegistrarOcorrenciaPage = lazy(() => import('./pages/RegistrarOcorrenciaPage').then((m) => ({ default: m.RegistrarOcorrenciaPage })));
const RegistroCidadaoPage = lazy(() => import('./pages/RegistroCidadaoPage').then((m) => ({ default: m.RegistroCidadaoPage })));
const ComunicacaoInteragenciasPage = lazy(() => import('./pages/ComunicacaoInteragenciasPage').then((m) => ({ default: m.ComunicacaoInteragenciasPage })));
const IndicadoresPage = lazy(() => import('./pages/IndicadoresPage').then((m) => ({ default: m.IndicadoresPage })));
const EfetivoPage = lazy(() => import('./pages/EfetivoPage').then((m) => ({ default: m.EfetivoPage })));
const TrilhaAuditoriaPage = lazy(() => import('./pages/TrilhaAuditoriaPage').then((m) => ({ default: m.TrilhaAuditoriaPage })));

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
              <Suspense fallback={<Carregando />}>
              <Routes>
                {/* Rotas Públicas do Portal Cidadão */}
                <Route path="/" element={<LandingPage />} />
                <Route path="/registrar-cidadao" element={<RegistroCidadaoPage />} />
                <Route path="/consulta" element={<ConsultaProtocoloPage />} />
                {/* RF08 / UC08: portal público de autenticação — fora do RequireRole por definição (UC08 regra 1) */}
                <Route path="/autenticar" element={<AutenticarDocumentoPage />} />
                <Route path="/autenticar/:codigo" element={<AutenticarDocumentoPage />} />
                <Route path="/login" element={<LoginPage />} />

                {/* Rotas Restritas Protegidas (RBAC Policial) */}
                <Route element={<RequireRole><AppShell /></RequireRole>}>
                  <Route path="/inicio" element={<InicioPage />} />
                  <Route path="/registrar" element={<RequireRole papeis={['AGENTE']}><RegistrarOcorrenciaPage /></RequireRole>} />
                  <Route path="/minhas" element={<RequireRole papeis={['AGENTE']}><MinhasOcorrenciasPage /></RequireRole>} />
                  <Route path="/fila" element={<RequireRole papeis={['DELEGADO', 'SUPERVISOR']}><FilaDelegadoPage /></RequireRole>} />
                  <Route path="/inqueritos" element={<RequireRole papeis={['DELEGADO', 'SUPERVISOR']}><InqueritosPage /></RequireRole>} />
                  <Route path="/laudos" element={<RequireRole papeis={['DELEGADO', 'PERITO', 'SUPERVISOR']}><LaudosPage /></RequireRole>} />
                  <Route path="/medidas" element={<RequireRole papeis={['DELEGADO', 'SUPERVISOR', 'AGENTE']}><MedidasProtetivasPage /></RequireRole>} />
                  <Route path="/painel" element={<RequireRole papeis={['OPERADOR_CENTRAL', 'SUPERVISOR', 'DELEGADO']}><PainelTaticoPage /></RequireRole>} />
                  <Route path="/interagencias" element={<RequireRole papeis={['DELEGADO', 'SUPERVISOR', 'AGENTE', 'OPERADOR_CENTRAL', 'PERITO']}><ComunicacaoInteragenciasPage /></RequireRole>} />
                  <Route path="/frota" element={<RequireRole papeis={['OPERADOR_CENTRAL', 'SUPERVISOR']}><FrotaPage /></RequireRole>} />
                  <Route path="/auditoria" element={<RequireRole papeis={['DELEGADO', 'SUPERVISOR']}><TrilhaAuditoriaPage /></RequireRole>} />
                  <Route path="/indicadores" element={<RequireRole papeis={['DELEGADO', 'SUPERVISOR', 'OPERADOR_CENTRAL']}><IndicadoresPage /></RequireRole>} />
                  <Route path="/efetivo" element={<RequireRole papeis={['SUPERVISOR', 'OPERADOR_CENTRAL']}><EfetivoPage /></RequireRole>} />
                </Route>

                {/* Redirecionamentos de aliases amigáveis */}
                <Route path="/consultar" element={<Navigate to="/consulta" replace />} />
                <Route path="/fila-delegado" element={<Navigate to="/fila" replace />} />
                <Route path="/painel-tatico" element={<Navigate to="/painel" replace />} />

                {/* Redirecionamento padrão */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
              </Suspense>
            </BrowserRouter>
          </ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </Suspense>
  );
}

import { Suspense } from 'react';
import './i18n';
import { RegistrarOcorrenciaPage } from './pages/RegistrarOcorrenciaPage';

export default function App() {
  return (
    <Suspense fallback={<div style={{ padding: '24px' }}>Carregando...</div>}>
      <RegistrarOcorrenciaPage />
    </Suspense>
  );
}

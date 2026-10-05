import React from 'react';
import { useTranslation } from 'react-i18next';
import { Button } from './common/Button';

/** Exibido dentro do AppShell quando o papel do usuário não alcança a rota (em vez de expulsá-lo para o portal público). */
export const AcessoNegado: React.FC = () => {
  const { t } = useTranslation('common');
  return (
    <div className="pagina">
      <div className="card" data-cy="acesso-negado" style={{ maxWidth: 560, margin: '48px auto', padding: 32, textAlign: 'center' }}>
        <h2>{t('acesso_negado.titulo')}</h2>
        <p className="muted">{t('acesso_negado.descricao')}</p>
        <Button to="/inicio" variant="primary">{t('acesso_negado.voltar')}</Button>
      </div>
    </div>
  );
};

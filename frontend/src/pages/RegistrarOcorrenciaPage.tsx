import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { EnvolvidoForm } from '../components/ocorrencias/EnvolvidoForm';
import { TipificacaoForm } from '../components/ocorrencias/TipificacaoForm';
import { ocorrenciasService } from '../services/ocorrenciasService';
import { toastOcorrenciaError, toastOcorrenciaSuccess } from '../utils/toasts/ocorrencia';
import type { EnvolvidoDTO, TipificacaoDTO } from '../types/ocorrencia';

export const RegistrarOcorrenciaPage: React.FC = () => {
  const { t } = useTranslation(['ocorrencias', 'common']);

  const [natureza, setNatureza] = useState('');
  const [descricao, setDescricao] = useState('');
  const [localizacao, setLocalizacao] = useState('');
  const [envolvidos, setEnvolvidos] = useState<EnvolvidoDTO[]>([]);
  const [tipificacoes, setTipificacoes] = useState<TipificacaoDTO[]>([]);
  const [loading, setLoading] = useState(false);
  const [protocoloCriado, setProtocoloCriado] = useState<string | null>(null);

  const handleAddEnvolvido = (envolvido: EnvolvidoDTO) => {
    setEnvolvidos((prev) => [...prev, envolvido]);
  };

  const handleRemoveEnvolvido = (index: number) => {
    setEnvolvidos((prev) => prev.filter((_, i) => i !== index));
  };

  const handleAddTipificacao = (tipificacao: TipificacaoDTO) => {
    setTipificacoes((prev) => [...prev, tipificacao]);
  };

  const handleRemoveTipificacao = (index: number) => {
    setTipificacoes((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!natureza.trim() || !descricao.trim() || !localizacao.trim()) {
      toastOcorrenciaError('validation');
      return;
    }

    setLoading(true);
    try {
      const response = await ocorrenciasService.registrar({
        agente_policial_id: '00000000-0000-0000-0000-000000000001',
        natureza: natureza.trim(),
        descricao: descricao.trim(),
        localizacao: localizacao.trim(),
        envolvidos,
        tipificacoes,
      });

      setProtocoloCriado(response.numero_protocolo);
      toastOcorrenciaSuccess(response.numero_protocolo);

      setNatureza('');
      setDescricao('');
      setLocalizacao('');
      setEnvolvidos([]);
      setTipificacoes([]);
    } catch {
      toastOcorrenciaError('server');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '24px', fontFamily: 'sans-serif' }}>
      <h1>{t('ocorrencias:page_title')}</h1>

      {protocoloCriado && (
        <div style={{ padding: '12px', background: '#dcfce7', color: '#166534', borderRadius: '6px', marginBottom: '16px' }}>
          <strong>{t('ocorrencias:toast.success', { protocolo: protocoloCriado })}</strong>
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '4px' }}>
            {t('ocorrencias:form.natureza_label')}
          </label>
          <input
            type="text"
            placeholder={t('ocorrencias:form.natureza_placeholder')}
            value={natureza}
            onChange={(e) => setNatureza(e.target.value)}
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '4px' }}>
            {t('ocorrencias:form.localizacao_label')}
          </label>
          <input
            type="text"
            placeholder={t('ocorrencias:form.localizacao_placeholder')}
            value={localizacao}
            onChange={(e) => setLocalizacao(e.target.value)}
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '4px' }}>
            {t('ocorrencias:form.descricao_label')}
          </label>
          <textarea
            rows={4}
            placeholder={t('ocorrencias:form.descricao_placeholder')}
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          />
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
            {t('ocorrencias:form.tipificacoes_label')}
          </label>
          <TipificacaoForm onAdd={handleAddTipificacao} />
          {tipificacoes.length > 0 && (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {tipificacoes.map((item, idx) => (
                <li key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 12px', background: '#f3f4f6', marginBottom: '4px', borderRadius: '4px' }}>
                  <span><strong>{item.artigo}:</strong> {item.descricao}</span>
                  <button type="button" onClick={() => handleRemoveTipificacao(idx)} style={{ color: '#dc2626', border: 'none', background: 'transparent', cursor: 'pointer' }}>
                    Remover
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px' }}>
            {t('ocorrencias:form.envolvidos_label')}
          </label>
          <EnvolvidoForm onAdd={handleAddEnvolvido} />
          {envolvidos.length > 0 && (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {envolvidos.map((item, idx) => (
                <li key={idx} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 12px', background: '#f3f4f6', marginBottom: '4px', borderRadius: '4px' }}>
                  <span><strong>{item.nome}</strong> ({item.tipo}){item.documento ? ` - ${item.documento}` : ''}</span>
                  <button type="button" onClick={() => handleRemoveEnvolvido(idx)} style={{ color: '#dc2626', border: 'none', background: 'transparent', cursor: 'pointer' }}>
                    Remover
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{ padding: '10px 20px', background: '#16a34a', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '16px', cursor: 'pointer' }}
        >
          {loading ? t('common:actions.loading') : t('common:actions.submit')}
        </button>
      </form>
    </div>
  );
};

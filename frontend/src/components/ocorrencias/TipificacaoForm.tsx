import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { TipificacaoDTO } from '../../types/api';

interface Props {
  onAdd: (tipificacao: TipificacaoDTO) => void;
}

export const TipificacaoForm: React.FC<Props> = ({ onAdd }) => {
  const { t } = useTranslation('ocorrencias');
  const [artigo, setArtigo] = useState('');
  const [descricao, setDescricao] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!artigo.trim() || !descricao.trim()) return;
    onAdd({
      artigo: artigo.trim(),
      descricao: descricao.trim(),
    });
    setArtigo('');
    setDescricao('');
  };

  return (
    <div style={{ border: '1px solid #ddd', padding: '12px', borderRadius: '6px', marginBottom: '12px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr auto', gap: '8px', alignItems: 'flex-end' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px' }}>
            {t('tipificacao.artigo_label')}
          </label>
          <input
            type="text"
            placeholder={t('tipificacao.artigo_placeholder')}
            value={artigo}
            onChange={(e) => setArtigo(e.target.value)}
            style={{ width: '100%', padding: '6px' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px' }}>
            {t('tipificacao.descricao_label')}
          </label>
          <input
            type="text"
            placeholder={t('tipificacao.descricao_placeholder')}
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
            style={{ width: '100%', padding: '6px' }}
          />
        </div>
        <button
          type="button"
          onClick={handleSubmit}
          style={{ padding: '6px 12px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          {t('form.add_tipificacao')}
        </button>
      </div>
    </div>
  );
};

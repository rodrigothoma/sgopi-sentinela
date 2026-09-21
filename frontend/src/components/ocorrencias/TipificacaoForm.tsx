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
    <div className="subform">
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr auto', gap: '8px', alignItems: 'flex-end' }}>
        <div>
          <label>
            {t('tipificacao.artigo_label')}
          </label>
          <input
            type="text"
            maxLength={50}
            placeholder={t('tipificacao.artigo_placeholder')}
            value={artigo}
            onChange={(e) => setArtigo(e.target.value)}
          />
        </div>
        <div>
          <label>
            {t('tipificacao.descricao_label')}
          </label>
          <input
            type="text"
            maxLength={150}
            placeholder={t('tipificacao.descricao_placeholder')}
            value={descricao}
            onChange={(e) => setDescricao(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleSubmit}
          style={{ height: 42 }}
        >
          {t('form.add_tipificacao')}
        </button>
      </div>
    </div>
  );
};

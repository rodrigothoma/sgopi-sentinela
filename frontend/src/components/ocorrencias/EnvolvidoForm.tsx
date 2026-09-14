import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { EnvolvidoDTO, TipoEnvolvido } from '../../types/api';

interface Props {
  onAdd: (envolvido: EnvolvidoDTO) => void;
}

export const EnvolvidoForm: React.FC<Props> = ({ onAdd }) => {
  const { t } = useTranslation('ocorrencias');
  const [nome, setNome] = useState('');
  const [tipo, setTipo] = useState<TipoEnvolvido>('VITIMA');
  const [documento, setDocumento] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!nome.trim()) return;
    onAdd({
      nome: nome.trim(),
      tipo,
      documento: documento.trim() ? documento.trim() : undefined,
    });
    setNome('');
    setDocumento('');
    setTipo('VITIMA');
  };

  return (
    <div className="subform">
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr auto', gap: '8px', alignItems: 'flex-end' }}>
        <div>
          <label>
            {t('envolvido.nome_label')}
          </label>
          <input
            type="text"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
          />
        </div>
        <div>
          <label>
            {t('envolvido.tipo_label')}
          </label>
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value as TipoEnvolvido)}
          >
            <option value="VITIMA">{t('envolvido.VITIMA')}</option>
            <option value="TESTEMUNHA">{t('envolvido.TESTEMUNHA')}</option>
            <option value="SUSPEITO">{t('envolvido.SUSPEITO')}</option>
          </select>
        </div>
        <div>
          <label>
            {t('envolvido.documento_label')}
          </label>
          <input
            type="text"
            value={documento}
            onChange={(e) => setDocumento(e.target.value)}
          />
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={handleSubmit}
        >
          {t('form.add_envolvido')}
        </button>
      </div>
    </div>
  );
};

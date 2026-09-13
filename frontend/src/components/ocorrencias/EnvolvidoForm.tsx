import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { EnvolvidoDTO, TipoEnvolvido } from '../../types/ocorrencia';

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
    <div style={{ border: '1px solid #ddd', padding: '12px', borderRadius: '6px', marginBottom: '12px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr auto', gap: '8px', alignItems: 'flex-end' }}>
        <div>
          <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px' }}>
            {t('envolvido.nome_label')}
          </label>
          <input
            type="text"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            style={{ width: '100%', padding: '6px' }}
          />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px' }}>
            {t('envolvido.tipo_label')}
          </label>
          <select
            value={tipo}
            onChange={(e) => setTipo(e.target.value as TipoEnvolvido)}
            style={{ width: '100%', padding: '6px' }}
          >
            <option value="VITIMA">{t('envolvido.VITIMA')}</option>
            <option value="TESTEMUNHA">{t('envolvido.TESTEMUNHA')}</option>
            <option value="SUSPEITO">{t('envolvido.SUSPEITO')}</option>
          </select>
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '12px', marginBottom: '4px' }}>
            {t('envolvido.documento_label')}
          </label>
          <input
            type="text"
            value={documento}
            onChange={(e) => setDocumento(e.target.value)}
            style={{ width: '100%', padding: '6px' }}
          />
        </div>
        <button
          type="button"
          onClick={handleSubmit}
          style={{ padding: '6px 12px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          {t('form.add_envolvido')}
        </button>
      </div>
    </div>
  );
};

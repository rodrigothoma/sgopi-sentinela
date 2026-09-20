import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { EnvolvidoDTO, TipoEnvolvido } from '../../types/api';
import { GlideSelect, GlideSelectOption } from '../common/GlideSelect';

interface Props {
  onAdd: (envolvido: EnvolvidoDTO) => void;
}

export const EnvolvidoForm: React.FC<Props> = ({ onAdd }) => {
  const { t } = useTranslation('ocorrencias');
  const [nome, setNome] = useState('');
  const [tipo, setTipo] = useState<TipoEnvolvido>('VITIMA');
  const [documento, setDocumento] = useState('');

  const opcoesTipo: GlideSelectOption[] = [
    { value: 'VITIMA', label: t('envolvido.VITIMA') },
    { value: 'TESTEMUNHA', label: t('envolvido.TESTEMUNHA') },
    { value: 'SUSPEITO', label: t('envolvido.SUSPEITO') },
  ];

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
          <label>{t('envolvido.nome_label')}</label>
          <input
            type="text"
            maxLength={50}
            value={nome}
            onChange={(e) => setNome(e.target.value)}
          />
        </div>
        <div>
          <label style={{ display: 'block', marginBottom: 4 }}>{t('envolvido.tipo_label')}</label>
          <GlideSelect
            options={opcoesTipo}
            value={tipo}
            onChange={(val) => setTipo(val as TipoEnvolvido)}
            size="sm"
            menuWidth={160}
            ariaLabel={t('envolvido.tipo_label')}
          />
        </div>
        <div>
          <label>{t('envolvido.documento_label')}</label>
          <input
            type="text"
            maxLength={20}
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

export default EnvolvidoForm;

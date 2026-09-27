import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { EnvolvidoDTO, TipoEnvolvido } from '../../types/api';
import { GlideSelect, GlideSelectOption } from '../common/GlideSelect';
import {
  formatarDocumento, semDigitos, somenteDigitos, validarDocumento, validarNome,
  type TipoDocumento,
} from '../../utils/documentos';

interface Props {
  onAdd: (envolvido: EnvolvidoDTO) => void;
}

export const EnvolvidoForm: React.FC<Props> = ({ onAdd }) => {
  const { t } = useTranslation('ocorrencias');
  const [nome, setNome] = useState('');
  const [tipo, setTipo] = useState<TipoEnvolvido>('VITIMA');
  const [documento, setDocumento] = useState('');
  const [erro, setErro] = useState<string | null>(null);

  const opcoesTipo: GlideSelectOption[] = [
    { value: 'VITIMA', label: t('envolvido.VITIMA') },
    { value: 'TESTEMUNHA', label: t('envolvido.TESTEMUNHA') },
    { value: 'SUSPEITO', label: t('envolvido.SUSPEITO') },
  ];

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const problemaNome = validarNome(nome);
    if (problemaNome) {
      setErro(t(`envolvido.erro_${problemaNome}`));
      return;
    }
    const digitos = somenteDigitos(documento);
    if (digitos) {
      const tipoDoc: TipoDocumento = digitos.length > 9 ? 'CPF' : 'RG';
      const problemaDoc = validarDocumento(tipoDoc, digitos);
      if (problemaDoc) {
        setErro(t(`envolvido.erro_${problemaDoc}`));
        return;
      }
    }
    onAdd({
      nome: nome.trim(),
      tipo,
      documento: digitos ? formatarDocumento(digitos.length > 9 ? 'CPF' : 'RG', digitos) : undefined,
    });
    setNome('');
    setDocumento('');
    setTipo('VITIMA');
    setErro(null);
  };

  return (
    <div className="subform">
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.2fr 1.2fr auto', gap: '8px', alignItems: 'flex-end' }}>
        <div>
          <label htmlFor="envolvido-nome">
            {t('envolvido.nome_label')} <span className="obrigatorio">*</span>
          </label>
          <input
            id="envolvido-nome"
            type="text"
            maxLength={60}
            value={nome}
            placeholder={t('envolvido.nome_placeholder')}
            onChange={(e) => { setNome(semDigitos(e.target.value)); setErro(null); }}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSubmit(); } }}
            style={{ height: 42 }}
          />
        </div>
        <div>
          <label>{t('envolvido.tipo_label')}</label>
          <GlideSelect
            options={opcoesTipo}
            value={tipo}
            onChange={(val) => setTipo(val as TipoEnvolvido)}
            size="md"
            fullWidth
            menuWidth={180}
            ariaLabel={t('envolvido.tipo_label')}
          />
        </div>
        <div>
          <label htmlFor="envolvido-documento">
            {t('envolvido.documento_label')}
          </label>
          <input
            id="envolvido-documento"
            type="text"
            maxLength={18}
            value={documento}
            placeholder="CPF ou RG"
            onChange={(e) => { setDocumento(e.target.value); setErro(null); }}
            onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleSubmit(); } }}
            style={{ height: 42 }}
          />
        </div>
        <button
          type="button"
          className="btn btn-primary"
          onClick={() => handleSubmit()}
          style={{ height: 42 }}
        >
          {t('form.add_envolvido')}
        </button>
      </div>
      {erro && <p className="campo-erro" style={{ marginTop: 6 }}>{erro}</p>}
    </div>
  );
};

export default EnvolvidoForm;


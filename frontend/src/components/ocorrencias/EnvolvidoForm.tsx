import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import type { EnvolvidoDTO, TipoEnvolvido } from '../../types/api';
import {
  TAMANHO_DOCUMENTO, formatarDocumento, limitarDigitos, semDigitos, somenteDigitos, validarDocumento, validarNome,
  type ProblemaDocumento, type ProblemaNome, type TipoDocumento,
} from '../../utils/documentos';

interface Props {
  onAdd: (envolvido: EnvolvidoDTO) => void;
}

/** Comprimento máximo do campo já com máscara (CPF: 000.000.000-00 = 14 caracteres para 11 dígitos). */
const MAX_LENGTH: Record<TipoDocumento, number> = { CPF: 14, RG: TAMANHO_DOCUMENTO.RG };

export const EnvolvidoForm: React.FC<Props> = ({ onAdd }) => {
  const { t } = useTranslation('ocorrencias');
  const [nome, setNome] = useState('');
  const [tipo, setTipo] = useState<TipoEnvolvido>('VITIMA');
  const [tipoDocumento, setTipoDocumento] = useState<TipoDocumento>('CPF');
  const [digitos, setDigitos] = useState('');
  const [erro, setErro] = useState<ProblemaNome | ProblemaDocumento>(null);

  const trocarTipoDocumento = (novo: TipoDocumento) => {
    setTipoDocumento(novo);
    setDigitos((d) => limitarDigitos(novo, d));
    setErro(null);
  };

  /** Só dígitos entram no estado; letras e símbolos colados são descartados. */
  const digitar = (e: React.ChangeEvent<HTMLInputElement>) => {
    setDigitos(limitarDigitos(tipoDocumento, e.target.value));
    setErro(null);
  };

  /** Documento: só dígitos. */
  const bloquearNaoNumerico = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key.length === 1 && !/\d/.test(e.key) && !e.ctrlKey && !e.metaKey) e.preventDefault();
  };

  /** Nome: nunca dígitos. */
  const bloquearDigito = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (/^\d$/.test(e.key) && !e.ctrlKey && !e.metaKey) e.preventDefault();
  };

  const handleSubmit = () => {
    const problemaNome = validarNome(nome);
    if (problemaNome) {
      setErro(problemaNome);
      return;
    }
    const problema = validarDocumento(tipoDocumento, digitos);
    if (problema) {
      setErro(problema);
      return;
    }
    onAdd({
      nome: nome.trim(),
      tipo,
      documento: digitos ? formatarDocumento(tipoDocumento, digitos) : undefined,
    });
    setNome('');
    setDigitos('');
    setTipo('VITIMA');
    setErro(null);
  };

  const mensagemErro = erro ? t(`envolvido.erro_${erro}`) : null;

  return (
    <div className="subform">
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 2fr auto', gap: '8px', alignItems: 'flex-end' }}>
        <div>
          <label htmlFor="envolvido-nome">{t('envolvido.nome_label')} <span className="obrigatorio">*</span></label>
          <input
            id="envolvido-nome"
            type="text"
            inputMode="text"
            autoComplete="off"
            required
            value={nome}
            maxLength={255}
            placeholder={t('envolvido.nome_placeholder')}
            onChange={(e) => { setNome(semDigitos(e.target.value)); if (erro === 'nome_vazio' || erro === 'nome_invalido') setErro(null); }}
            onKeyDown={(e) => { bloquearDigito(e); if (e.key === 'Enter') { e.preventDefault(); handleSubmit(); } }}
          />
        </div>
        <div>
          <label htmlFor="envolvido-tipo">{t('envolvido.tipo_label')}</label>
          <select id="envolvido-tipo" value={tipo} onChange={(e) => setTipo(e.target.value as TipoEnvolvido)}>
            <option value="VITIMA">{t('envolvido.VITIMA')}</option>
            <option value="TESTEMUNHA">{t('envolvido.TESTEMUNHA')}</option>
            <option value="SUSPEITO">{t('envolvido.SUSPEITO')}</option>
          </select>
        </div>
        <div>
          <label htmlFor="envolvido-documento">
            {t('envolvido.documento_label')} <span className="muted contador">({somenteDigitos(digitos).length}/{TAMANHO_DOCUMENTO[tipoDocumento]})</span>
          </label>
          <div className="documento-campo">
            <select aria-label={t('envolvido.tipo_documento_label')} value={tipoDocumento} onChange={(e) => trocarTipoDocumento(e.target.value as TipoDocumento)}>
              <option value="CPF">CPF</option>
              <option value="RG">RG</option>
            </select>
            <input
              id="envolvido-documento"
              type="text"
              inputMode="numeric"
              pattern="[0-9.\-]*"
              autoComplete="off"
              maxLength={MAX_LENGTH[tipoDocumento]}
              value={formatarDocumento(tipoDocumento, digitos)}
              placeholder={t(`envolvido.numero_documento_placeholder_${tipoDocumento}`)}
              title={t(`envolvido.documento_ajuda_${tipoDocumento}`)}
              onKeyDown={(e) => { bloquearNaoNumerico(e); if (e.key === 'Enter') { e.preventDefault(); handleSubmit(); } }}
              onChange={digitar}
            />
          </div>
        </div>
        <button type="button" className="btn btn-primary" disabled={!nome.trim()} onClick={handleSubmit}>
          {t('form.add_envolvido')}
        </button>
      </div>
      {mensagemErro ? <p className="campo-erro">{mensagemErro}</p> : <p className="muted small" style={{ margin: '6px 0 0' }}>{t(`envolvido.documento_ajuda_${tipoDocumento}`)}</p>}
    </div>
  );
};

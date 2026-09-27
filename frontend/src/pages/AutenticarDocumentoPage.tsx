import React, { useCallback, useEffect, useState } from 'react';
import axios from 'axios';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { NavbarPublica } from '../components/layout/NavbarPublica';
import { StatusBadge } from '../components/StatusBadge';
import { mensagemDeErro } from '../services/api';
import { documentosService } from '../services/documentosService';
import type { DocumentoAutenticado, SituacaoDocumento } from '../types/api';
import { codigoValido, formatarChave, normalizarCodigo, TAMANHO_CHAVE } from '../utils/autenticidade';
import { formatarNatureza } from '../utils/formatarNatureza';

/** Resultado exibido ao consulente: as três situações do backend + "não reconhecido" (404) e "código inválido" (422). */
type Veredito = SituacaoDocumento | 'NAO_RECONHECIDO' | 'CODIGO_INVALIDO';

const CLASSE_VEREDITO: Record<Veredito, string> = {
  AUTENTICO: 'sucesso',
  ADULTERADO: 'erro',
  INDISPONIVEL: 'aviso',
  NAO_RECONHECIDO: 'erro',
  CODIGO_INVALIDO: 'aviso',
};

/**
 * Portal público de autenticação de documentos (RF08 / UC08). Não exige login:
 * aceita a chave impressa (ou lida do QR Code, que abre /autenticar/<chave>) ou o
 * hash SHA-256 e exibe o veredito DOCUMENTO AUTÊNTICO / NÃO RECONHECIDO.
 */
export const AutenticarDocumentoPage: React.FC = () => {
  const { t, i18n } = useTranslation(['publico', 'common']);
  const navigate = useNavigate();
  const { codigo: codigoRota } = useParams<{ codigo: string }>();
  const [searchParams] = useSearchParams();
  const codigoInicial = codigoRota ?? searchParams.get('chave') ?? '';

  const [codigo, setCodigo] = useState(codigoInicial);
  const [ocupado, setOcupado] = useState(false);
  const [veredito, setVeredito] = useState<Veredito | null>(null);
  const [documento, setDocumento] = useState<DocumentoAutenticado | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const autenticar = useCallback(async (valor: string) => {
    const limpo = normalizarCodigo(valor);
    if (!limpo) return;
    setOcupado(true);
    setErro(null);
    setDocumento(null);
    if (!codigoValido(limpo)) {
      setVeredito('CODIGO_INVALIDO');
      setOcupado(false);
      return;
    }
    try {
      const resultado = await documentosService.autenticar(limpo);
      setDocumento(resultado);
      setVeredito(resultado.situacao);
    } catch (falha) {
      const status = axios.isAxiosError(falha) ? falha.response?.status : undefined;
      if (status === 404) setVeredito('NAO_RECONHECIDO');
      else if (status === 422) setVeredito('CODIGO_INVALIDO');
      else {
        setVeredito(null);
        setErro(mensagemDeErro(falha, t('publico:autenticar.erro_generico')));
      }
    } finally {
      setOcupado(false);
    }
  }, [t]);

  useEffect(() => {
    if (codigoInicial) void autenticar(codigoInicial);
  }, [codigoInicial, autenticar]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const limpo = normalizarCodigo(codigo);
    if (limpo.length === TAMANHO_CHAVE) navigate(`/autenticar/${limpo.toUpperCase()}`, { replace: true });
    void autenticar(codigo);
  };

  const localeData = i18n.language && i18n.language.startsWith('en') ? 'en-US' : 'pt-BR';
  const fmt = (iso: string) => (iso ? new Date(iso).toLocaleString(localeData) : '—');
  const mostrarEspelho = documento && veredito && veredito !== 'INDISPONIVEL';

  return (
    <div className="portal-wrap">
      <NavbarPublica />

      <main className="pagina" style={{ maxWidth: 760, padding: '40px 20px' }}>
        <div className="card" style={{ padding: '32px' }}>
          <h2>{t('publico:autenticar.titulo')}</h2>
          <p className="muted">{t('publico:autenticar.subtitulo')}</p>

          <form onSubmit={handleSubmit} className="autenticar-form" data-cy="autenticar-form">
            <input
              type="text"
              aria-label={t('publico:autenticar.campo_label')}
              placeholder={t('publico:autenticar.placeholder')}
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
              autoComplete="off"
              spellCheck={false}
              data-cy="autenticar-codigo"
            />
            <button type="submit" className="btn btn-primary" disabled={ocupado || !normalizarCodigo(codigo)} data-cy="autenticar-botao">
              {ocupado ? t('common:actions.loading') : t('publico:autenticar.botao')}
            </button>
          </form>
          <p className="small muted">{t('publico:autenticar.ajuda')}</p>

          {erro && <div className="alerta erro" style={{ marginTop: 20 }}>{erro}</div>}

          {veredito && (
            <div className={`selo-veredito selo-${CLASSE_VEREDITO[veredito]}`} role="status" data-cy="veredito" data-veredito={veredito}>
              <span className="selo-icone" aria-hidden="true">{veredito === 'AUTENTICO' ? '✔' : veredito === 'INDISPONIVEL' ? '!' : '✖'}</span>
              <div>
                <strong>{t(`publico:autenticar.veredito.${veredito}.titulo`)}</strong>
                <p>{t(`publico:autenticar.veredito.${veredito}.descricao`)}</p>
              </div>
            </div>
          )}

          {documento && veredito === 'INDISPONIVEL' && (
            <p className="muted" style={{ marginTop: 12 }}>
              {t('publico:autenticar.espelho.protocolo')} <strong>{documento.numero_protocolo}</strong>
            </p>
          )}

          {mostrarEspelho && documento && (
            <div className="espelho-documento" data-cy="espelho-documento">
              <div className="espelho-topo">
                <div>
                  <span className="small muted">{t('publico:autenticar.espelho.protocolo')}</span>
                  <div className="espelho-protocolo">{documento.numero_protocolo}</div>
                </div>
                <StatusBadge status={documento.status_ocorrencia} />
              </div>

              <dl className="grid2" style={{ marginTop: 20 }}>
                <dt>{t('publico:autenticar.espelho.chave')}</dt>
                <dd><code>{formatarChave(documento.chave_autenticidade)}</code></dd>
                <dt>{t('publico:autenticar.espelho.natureza')}</dt>
                <dd><strong>{formatarNatureza(documento.natureza, t)}</strong></dd>
                <dt>{t('publico:autenticar.espelho.data_fato')}</dt>
                <dd>{fmt(documento.data_hora_fato)}</dd>
                <dt>{t('publico:autenticar.espelho.emitido_em')}</dt>
                <dd>{fmt(documento.emitido_em)}</dd>
                <dt>{t('publico:autenticar.espelho.consultado_em')}</dt>
                <dd>{fmt(documento.consultado_em)}</dd>
                {documento.tipificacoes.length > 0 && (
                  <>
                    <dt>{t('publico:autenticar.espelho.tipificacoes')}</dt>
                    <dd>{documento.tipificacoes.map((tp) => `${tp.artigo} — ${tp.descricao}`).join('; ')}</dd>
                  </>
                )}
                <dt>{t('publico:autenticar.espelho.envolvidos')}</dt>
                <dd>
                  {Object.entries(documento.envolvidos_por_tipo)
                    .map(([tipo, total]) => `${total} × ${t(`publico:autenticar.envolvido.${tipo}`, tipo)}`)
                    .join(', ') || '—'}
                </dd>
                <dt>{t('publico:autenticar.espelho.evidencias')}</dt>
                <dd>{documento.quantidade_evidencias}</dd>
                <dt>{t('publico:autenticar.espelho.hash')}</dt>
                <dd><code className="espelho-hash">{documento.hash_integridade}</code></dd>
              </dl>
              <p className="small muted">{t('publico:autenticar.espelho.lgpd')}</p>
            </div>
          )}

          <div style={{ marginTop: 20, textAlign: 'right' }}>
            <Link to="/" className="btn btn-ghost">{t('publico:consulta.detalhes.voltar_inicio')}</Link>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AutenticarDocumentoPage;

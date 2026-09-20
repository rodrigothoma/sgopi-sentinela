import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { NavbarPublica } from '../components/layout/NavbarPublica';
import { SeletorCoordenada } from '../components/painel/SeletorCoordenada';
import { CENTRO_PADRAO } from '../components/painel/leaflet';
import { paraInputLocal } from '../components/ocorrencias/OcorrenciaForm';
import { mensagemDeErro, registrarOcorrenciaPublica } from '../services/api';
import { Button } from '../components/common/Button';
import { GlideSelect, GlideSelectOption } from '../components/common/GlideSelect';
import {
  mascararCpfInput,
  mascararTelefoneInput,
  normalizarDigitos,
  validarCpf,
  validarEmail,
} from '../utils/cpf';

const NATUREZA_CHAVES = [
  { chave: 'furto', valorPadrao: 'Furto' },
  { chave: 'perda_extravio', valorPadrao: 'Perda ou Extravio de Documento/Objeto' },
  { chave: 'acidente_sem_vitima', valorPadrao: 'Acidente de Trânsito sem Vítima' },
  { chave: 'ameaca', valorPadrao: 'Ameaça' },
  { chave: 'perturbacao_sossego', valorPadrao: 'Perturbação do Sossego' },
  { chave: 'dano_patrimonio', valorPadrao: 'Dano ao Patrimônio' },
  { chave: 'outro', valorPadrao: 'Outro Fato Circunstanciado' },
];

export const RegistroCidadaoPage: React.FC = () => {
  const { t } = useTranslation(['publico', 'common']);

  const opcoesNatureza: GlideSelectOption[] = useMemo(() => {
    return NATUREZA_CHAVES.map((n) => ({
      value: n.valorPadrao,
      label: t(`publico:registro.naturezas.${n.chave}`, n.valorPadrao),
    }));
  }, [t]);

  // Dados do Comunicante
  const [nome, setNome] = useState('');
  const [isEstrangeiro, setIsEstrangeiro] = useState(false);
  const [cpf, setCpf] = useState('');
  const [passaporte, setPassaporte] = useState('');
  const [email, setEmail] = useState('');
  const [telefone, setTelefone] = useState('');
  const [declaracaoMaioridade, setDeclaracaoMaioridade] = useState(false);

  // Dados do Fato
  const [natureza, setNatureza] = useState(NATUREZA_CHAVES[0].valorPadrao);
  const [naturezaPersonalizada, setNaturezaPersonalizada] = useState('');
  const [descricao, setDescricao] = useState('');
  const [localizacao, setLocalizacao] = useState('');
  const [latitude, setLatitude] = useState<number>(CENTRO_PADRAO[0]);
  const [longitude, setLongitude] = useState<number>(CENTRO_PADRAO[1]);
  const [dataHora, setDataHora] = useState(paraInputLocal(new Date()));

  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [protocoloGerado, setProtocoloGerado] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErro(null);

    // Validações do Comunicante
    const partesNome = nome.trim().split(/\s+/);
    if (partesNome.length < 2) {
      setErro(t('publico:registro.erros.nome_incompleto'));
      return;
    }

    if (!isEstrangeiro) {
      if (!cpf.trim()) {
        setErro(t('publico:registro.erros.cpf_obrigatorio'));
        return;
      }
      if (!validarCpf(cpf)) {
        setErro(t('publico:registro.erros.cpf_invalido'));
        return;
      }
    } else {
      if (!passaporte.trim()) {
        setErro(t('publico:registro.erros.documento_obrigatorio'));
        return;
      }
    }

    if (!email.trim()) {
      setErro(t('publico:registro.erros.email_obrigatorio'));
      return;
    }
    if (!validarEmail(email)) {
      setErro(t('publico:registro.erros.email_invalido'));
      return;
    }

    const digitosTel = normalizarDigitos(telefone);
    if (!digitosTel) {
      setErro(t('publico:registro.erros.telefone_obrigatorio'));
      return;
    }
    if (digitosTel.length < 10) {
      setErro(t('publico:registro.erros.telefone_invalido'));
      return;
    }

    if (!declaracaoMaioridade) {
      setErro(t('publico:registro.erros.declaracao_obrigatoria'));
      return;
    }

    // Validações do Fato
    if (!localizacao.trim()) {
      setErro(t('publico:registro.erros.localizacao_obrigatoria'));
      return;
    }
    if (descricao.trim().length < 20) {
      setErro(t('publico:registro.erros.descricao_curta'));
      return;
    }
    if (new Date(dataHora).getTime() > Date.now()) {
      setErro(t('publico:registro.erros.data_futura'));
      return;
    }

    const naturezaFinal =
      natureza === 'Outro Fato Circunstanciado' && naturezaPersonalizada.trim()
        ? naturezaPersonalizada.trim()
        : natureza;

    setOcupado(true);
    try {
      const res = await registrarOcorrenciaPublica({
        nome_solicitante: nome.trim(),
        documento: isEstrangeiro ? passaporte.trim() : cpf.trim(),
        email: email.trim(),
        telefone: telefone.trim(),
        declaracao_maioridade: declaracaoMaioridade,
        natureza: naturezaFinal,
        descricao: descricao.trim(),
        localizacao: localizacao.trim(),
        latitude,
        longitude,
        data_hora_fato: new Date(dataHora).toISOString(),
      });
      setProtocoloGerado(res.numero_protocolo);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setErro(mensagemDeErro(err, t('publico:registro.erros.falha_registro')));
    } finally {
      setOcupado(false);
    }
  };

  const copiarProtocolo = () => {
    if (!protocoloGerado) return;
    navigator.clipboard.writeText(protocoloGerado);
    setCopiado(true);
    setTimeout(() => setCopiado(false), 2500);
  };

  return (
    <div className="portal-wrap">
      <NavbarPublica />

      <main className="pagina" style={{ maxWidth: 860, padding: '40px 20px' }}>
        {protocoloGerado ? (
          <div className="card" style={{ textAlign: 'center', padding: '40px 24px' }}>
            <div
              style={{
                width: 56,
                height: 56,
                borderRadius: '50%',
                background: 'rgba(16, 185, 129, 0.15)',
                color: 'var(--ok)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                marginBottom: 16,
              }}
            >
              <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h2>{t('publico:registro.sucesso_titulo')}</h2>
            <p className="muted">{t('publico:registro.sucesso_mensagem')}</p>

            <div className="protocolo-banner">
              <span className="small muted">{t('publico:registro.protocolo_label')}</span>
              <span className="protocolo-codigo">{protocoloGerado}</span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={copiarProtocolo}
                style={{ marginTop: 8 }}
              >
                {copiado ? t('publico:registro.protocolo_copiado') : t('publico:registro.copiar_protocolo')}
              </Button>
            </div>

            <p className="muted small">{t('publico:registro.guardar_aviso')}</p>

            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 24, flexWrap: 'wrap' }}>
              <Button to={`/consulta?protocolo=${protocoloGerado}`} variant="primary">
                {t('publico:registro.acompanhar_status')}
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setProtocoloGerado(null);
                  setNome('');
                  setCpf('');
                  setPassaporte('');
                  setEmail('');
                  setTelefone('');
                  setDeclaracaoMaioridade(false);
                  setDescricao('');
                  setLocalizacao('');
                }}
              >
                {t('publico:registro.novo_registro')}
              </Button>
            </div>
          </div>
        ) : (
          <form className="card form" onSubmit={handleSubmit} style={{ padding: '32px' }}>
            <div style={{ marginBottom: 24 }}>
              <h2>{t('publico:registro.titulo')}</h2>
              <p className="muted">{t('publico:registro.subtitulo')}</p>
            </div>

            {/* Banner Institucional de Orientações da Delegacia Online */}
            <div
              style={{
                marginBottom: 24,
                borderLeft: '4px solid var(--primary)',
                background: 'var(--card-hover)',
                borderRadius: '6px',
                padding: '18px 20px',
              }}
            >
              <h3 style={{ fontSize: '0.95rem', margin: '0 0 6px', color: 'var(--ink)' }}>
                {t('publico:registro.instrucoes.titulo')}
              </h3>
              <p style={{ fontSize: '0.85rem', color: 'var(--muted)', margin: '0 0 12px', lineHeight: 1.5 }}>
                {t('publico:registro.instrucoes.publico_alvo')}
              </p>
              <div style={{ fontSize: '0.82rem', color: 'var(--muted)', display: 'flex', flexDirection: 'column', gap: 5 }}>
                <span>{t('publico:registro.instrucoes.etapa_1')}</span>
                <span>{t('publico:registro.instrucoes.etapa_2')}</span>
                <span>{t('publico:registro.instrucoes.etapa_3')}</span>
                <span>{t('publico:registro.instrucoes.etapa_4')}</span>
              </div>
              <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid var(--line)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--alerta, #eab308)' }}>
                  {t('publico:registro.instrucoes.urgencia_aviso')}
                </span>
                <span style={{ fontSize: '0.78rem', color: 'var(--muted)' }}>
                  {t('publico:registro.instrucoes.aviso_legal')}
                </span>
              </div>
            </div>

            {erro && <div className="alerta erro">{erro}</div>}

            {/* 1. Identificação do Comunicante */}
            <fieldset>
              <legend>{t('publico:registro.comunicante_titulo')}</legend>
              <div className="grid2">
                <label>
                  {t('publico:registro.nome_label')}
                  <input
                    type="text"
                    required
                    maxLength={100}
                    placeholder={t('publico:registro.nome_placeholder')}
                    value={nome}
                    onChange={(e) => setNome(e.target.value)}
                  />
                </label>

                {!isEstrangeiro ? (
                  <label>
                    {t('publico:registro.cpf_label')}
                    <input
                      type="text"
                      required
                      maxLength={14}
                      placeholder={t('publico:registro.cpf_placeholder')}
                      value={cpf}
                      onChange={(e) => setCpf(mascararCpfInput(e.target.value))}
                    />
                  </label>
                ) : (
                  <label>
                    {t('publico:registro.passaporte_label')}
                    <input
                      type="text"
                      required
                      maxLength={30}
                      placeholder={t('publico:registro.passaporte_placeholder')}
                      value={passaporte}
                      onChange={(e) => setPassaporte(e.target.value)}
                    />
                  </label>
                )}
              </div>

              <div style={{ marginTop: 8, marginBottom: 14 }}>
                <label style={{ display: 'inline-flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.82rem', color: 'var(--muted)' }}>
                  <input
                    type="checkbox"
                    checked={isEstrangeiro}
                    onChange={(e) => {
                      setIsEstrangeiro(e.target.checked);
                      setCpf('');
                      setPassaporte('');
                    }}
                  />
                  <span>{t('publico:registro.estrangeiro_check')}</span>
                </label>
              </div>

              <div className="grid2">
                <label>
                  {t('publico:registro.email_label')}
                  <input
                    type="email"
                    required
                    maxLength={100}
                    placeholder={t('publico:registro.email_placeholder')}
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                  <small className="muted" style={{ display: 'block', marginTop: 4 }}>
                    {t('publico:registro.email_ajuda')}
                  </small>
                </label>

                <label>
                  {t('publico:registro.telefone_label')}
                  <input
                    type="tel"
                    required
                    maxLength={15}
                    placeholder={t('publico:registro.telefone_placeholder')}
                    value={telefone}
                    onChange={(e) => setTelefone(mascararTelefoneInput(e.target.value))}
                  />
                </label>
              </div>
            </fieldset>

            {/* 2. Natureza e Circunstância do Fato */}
            <fieldset>
              <legend>{t('publico:registro.fato_titulo')}</legend>
              <div className="grid2">
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <label
                    style={{
                      fontSize: '0.82rem',
                      fontWeight: 600,
                      color: 'var(--muted)',
                      textTransform: 'uppercase',
                      letterSpacing: '0.04em',
                    }}
                  >
                    {t('publico:registro.natureza_label')}
                  </label>
                  <GlideSelect
                    options={opcoesNatureza}
                    value={natureza}
                    onChange={(val) => setNatureza(val)}
                    size="md"
                    menuWidth="100%"
                    ariaLabel={t('publico:registro.natureza_label')}
                  />
                </div>
                <label>
                  {t('publico:registro.data_hora_label')}
                  <input
                    type="datetime-local"
                    required
                    value={dataHora}
                    onChange={(e) => setDataHora(e.target.value)}
                  />
                </label>
              </div>

              {natureza === 'Outro Fato Circunstanciado' && (
                <label style={{ marginTop: 12 }}>
                  {t('publico:registro.natureza_especificar_label')}
                  <input
                    type="text"
                    maxLength={50}
                    placeholder={t('publico:registro.natureza_especificar_placeholder')}
                    value={naturezaPersonalizada}
                    onChange={(e) => setNaturezaPersonalizada(e.target.value)}
                  />
                </label>
              )}

              <label style={{ marginTop: 14 }}>
                {t('publico:registro.relato_label')}
                <textarea
                  rows={4}
                  required
                  maxLength={500}
                  placeholder={t('publico:registro.relato_placeholder')}
                  value={descricao}
                  onChange={(e) => setDescricao(e.target.value)}
                />
              </label>
              <span className="small muted">
                {t('publico:registro.caracteres_contagem', { atual: descricao.length })}{' '}
                {descricao.length < 20
                  ? t('publico:registro.caracteres_faltam', { restantes: 20 - descricao.length })
                  : '✓'}
              </span>
            </fieldset>

            {/* 3. Localização do Ocorrido */}
            <fieldset>
              <legend>{t('publico:registro.localizacao_titulo')}</legend>
              <label>
                {t('publico:registro.endereco_label')}
                <input
                  type="text"
                  required
                  maxLength={150}
                  placeholder={t('publico:registro.endereco_placeholder')}
                  value={localizacao}
                  onChange={(e) => setLocalizacao(e.target.value)}
                />
              </label>

              <label style={{ marginTop: 14 }}>{t('publico:registro.mapa_label')}</label>
              <SeletorCoordenada
                latitude={latitude}
                longitude={longitude}
                onChange={(lat, lon) => {
                  setLatitude(lat);
                  setLongitude(lon);
                }}
              />
            </fieldset>

            {/* 4. Declaração Legal e Maioridade */}
            <fieldset>
              <legend>{t('publico:registro.declaracao_titulo')}</legend>
              <label
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 12,
                  cursor: 'pointer',
                  fontSize: '0.88rem',
                  lineHeight: 1.5,
                  userSelect: 'none',
                }}
              >
                <input
                  type="checkbox"
                  required
                  checked={declaracaoMaioridade}
                  onChange={(e) => setDeclaracaoMaioridade(e.target.checked)}
                  style={{ marginTop: 3, flexShrink: 0 }}
                />
                <span>{t('publico:registro.declaracao_texto')}</span>
              </label>
            </fieldset>

            <div style={{ display: 'flex', gap: 14, justifyContent: 'flex-end', marginTop: 28 }}>
              <Button to="/" variant="ghost">
                {t('publico:registro.botao_cancelar')}
              </Button>
              <Button
                type="submit"
                variant="primary"
                loading={ocupado}
                disabled={
                  !nome.trim() ||
                  (!isEstrangeiro && !cpf.trim()) ||
                  (isEstrangeiro && !passaporte.trim()) ||
                  !email.trim() ||
                  !telefone.trim() ||
                  !declaracaoMaioridade ||
                  descricao.trim().length < 20
                }
              >
                {t('publico:registro.botao_enviar')}
              </Button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
};

export default RegistroCidadaoPage;

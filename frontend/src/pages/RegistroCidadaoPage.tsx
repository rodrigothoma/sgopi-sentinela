import React, { useState } from 'react';
import { NavbarPublica } from '../components/layout/NavbarPublica';
import { SeletorCoordenada } from '../components/painel/SeletorCoordenada';
import { CENTRO_PADRAO } from '../components/painel/leaflet';
import { paraInputLocal } from '../components/ocorrencias/OcorrenciaForm';
import { mensagemDeErro, registrarOcorrenciaPublica } from '../services/api';
import { Button } from '../components/common/Button';

const NATUREZAS_COMUNS = [
  'Furto',
  'Perda ou Extravio de Documento/Objeto',
  'Acidente de Trânsito sem Vítima',
  'Ameaça',
  'Perturbação do Sossego',
  'Dano ao Patrimônio',
  'Outro Fato Circunstanciado'
];

export const RegistroCidadaoPage: React.FC = () => {
  const [nome, setNome] = useState('');
  const [documento, setDocumento] = useState('');
  const [natureza, setNatureza] = useState(NATUREZAS_COMUNS[0]);
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

    const naturezaFinal = natureza === 'Outro Fato Circunstanciado' && naturezaPersonalizada.trim()
      ? naturezaPersonalizada.trim()
      : natureza;

    if (!nome.trim()) {
      setErro('Informe o seu nome completo.');
      return;
    }
    if (!localizacao.trim()) {
      setErro('Informe o endereço ou ponto de referência do local do fato.');
      return;
    }
    if (descricao.trim().length < 20) {
      setErro('A descrição do ocorrido deve ter pelo menos 20 caracteres.');
      return;
    }
    if (new Date(dataHora).getTime() > Date.now()) {
      setErro('A data e hora do fato não podem estar no futuro.');
      return;
    }

    setOcupado(true);
    try {
      const res = await registrarOcorrenciaPublica({
        nome_solicitante: nome.trim(),
        documento: documento.trim() || undefined,
        natureza: naturezaFinal,
        descricao: descricao.trim(),
        localizacao: localizacao.trim(),
        latitude,
        longitude,
        data_hora_fato: new Date(dataHora).toISOString()
      });
      setProtocoloGerado(res.numero_protocolo);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      setErro(mensagemDeErro(err, 'Não foi possível registrar a ocorrência. Tente novamente.'));
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
            <h2>Ocorrência Registrada com Sucesso!</h2>
            <p className="muted">
              Sua ocorrência foi enviada para a central do SGOPI Sentinela e já se encontra na fila de
              triagem da autoridade policial.
            </p>

            <div className="protocolo-banner">
              <span className="small muted">NÚMERO DO SEU PROTOCOLO:</span>
              <span className="protocolo-codigo">{protocoloGerado}</span>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={copiarProtocolo}
                style={{ marginTop: 8 }}
              >
                {copiado ? 'Protocolo Copiado!' : 'Copiar Protocolo'}
              </Button>
            </div>

            <p className="muted small">
              Guarde este número para acompanhar o andamento ou apresentar quando solicitado.
            </p>

            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', marginTop: 24, flexWrap: 'wrap' }}>
              <Button to={`/consulta?protocolo=${protocoloGerado}`} variant="primary">
                Acompanhar Status
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => {
                  setProtocoloGerado(null);
                  setNome('');
                  setDescricao('');
                  setLocalizacao('');
                }}
              >
                Novo Registro
              </Button>
            </div>
          </div>
        ) : (
          <form className="card form" onSubmit={handleSubmit} style={{ padding: '32px' }}>
            <div style={{ marginBottom: 24 }}>
              <span className="pill" style={{ marginBottom: 8, display: 'inline-block' }}>
                DELEGACIA ELETRÔNICA · SGOPI
              </span>
              <h2>Registro de Ocorrência Online</h2>
              <p className="muted">
                Preencha as informações do fato. Os dados serão encaminhados para validação da autoridade
                competente e despacho operacional.
              </p>
            </div>

            {erro && <div className="alerta erro">{erro}</div>}

            <fieldset>
              <legend>1. Dados do Comunicante / Solicitante</legend>
              <div className="grid2">
                <label>
                  Nome Completo *
                  <input
                    type="text"
                    required
                    placeholder="Ex: João da Silva"
                    value={nome}
                    onChange={(e) => setNome(e.target.value)}
                  />
                </label>
                <label>
                  Documento (CPF ou RG)
                  <input
                    type="text"
                    placeholder="Opcional (somente números)"
                    value={documento}
                    onChange={(e) => setDocumento(e.target.value)}
                  />
                </label>
              </div>
            </fieldset>

            <fieldset>
              <legend>2. Natureza e Circunstância do Fato</legend>
              <div className="grid2">
                <label>
                  Tipo da Ocorrência *
                  <select value={natureza} onChange={(e) => setNatureza(e.target.value)}>
                    {NATUREZAS_COMUNS.map((n) => (
                      <option key={n} value={n}>
                        {n}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Data e Hora do Fato *
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
                  Especifique a Natureza
                  <input
                    type="text"
                    placeholder="Ex: Extravio de placa automotiva"
                    value={naturezaPersonalizada}
                    onChange={(e) => setNaturezaPersonalizada(e.target.value)}
                  />
                </label>
              )}

              <label style={{ marginTop: 14 }}>
                Relato Detalhado do Ocorrido * (mínimo 20 caracteres)
                <textarea
                  rows={4}
                  required
                  placeholder="Descreva com detalhes o que aconteceu, características de suspeitos ou objetos envolvidos..."
                  value={descricao}
                  onChange={(e) => setDescricao(e.target.value)}
                />
              </label>
              <span className="small muted">
                {descricao.length}/20 caracteres {descricao.length < 20 ? '(faltam ' + (20 - descricao.length) + ')' : '✓'}
              </span>
            </fieldset>

            <fieldset>
              <legend>3. Localização do Ocorrido</legend>
              <label>
                Endereço Aproximado / Ponto de Referência *
                <input
                  type="text"
                  required
                  placeholder="Ex: Av. Eurípedes Brasil Milano, Centro, próximo à praça"
                  value={localizacao}
                  onChange={(e) => setLocalizacao(e.target.value)}
                />
              </label>

              <label style={{ marginTop: 14 }}>
                Posicionamento no Mapa (clique para ajustar o ponto exato)
              </label>
              <SeletorCoordenada
                latitude={latitude}
                longitude={longitude}
                onChange={(lat, lon) => {
                  setLatitude(lat);
                  setLongitude(lon);
                }}
              />
            </fieldset>

            <div style={{ display: 'flex', gap: 14, justifyContent: 'flex-end', marginTop: 28 }}>
              <Button to="/" variant="ghost">
                Cancelar
              </Button>
              <Button
                type="submit"
                variant="primary"
                loading={ocupado}
                disabled={!nome.trim() || descricao.trim().length < 20}
              >
                Confirmar e Registrar Ocorrência
              </Button>
            </div>
          </form>
        )}
      </main>
    </div>
  );
};

import React from 'react';
import { Link } from 'react-router-dom';
import { NavbarPublica } from '../components/layout/NavbarPublica';
import { SplitFlapText } from '../components/common/SplitFlapText';
import { LogoSgopi } from '../components/common/LogoSgopi';

/* Ícones SVG simples para os cards — sem emojis */
const IconDocument: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22"
    fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
    <line x1="10" y1="9" x2="8" y2="9" />
  </svg>
);

const IconSearch: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22"
    fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true">
    <circle cx="11" cy="11" r="8" />
    <line x1="21" y1="21" x2="16.65" y2="16.65" />
  </svg>
);

const IconShield: React.FC = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22"
    fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"
    aria-hidden="true">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
  </svg>
);

export const LandingPage: React.FC = () => {
  return (
    <div className="portal-wrap">
      <NavbarPublica />

      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <main className="landing-hero">
        <p className="hero-label">SISTEMA OFICIAL — UNIPAMPA / ALEGRETE</p>

        <div className="hero-flap-wrapper">
          <SplitFlapText
            words={['SENTINELA ONLINE', 'PORTAL CIDADAO', 'PRONTIDAO TOTAL', 'SISTEMA INTEGRADO']}
            padTo={16}
            fontSize={52}
            flipsPerChar={6}
            cycleDelay={2800}
            charset="alpha"
          />
        </div>

        <p className="hero-subtitle">
          Canal oficial e unificado para registro de ocorrências pelo cidadão,
          triagem técnica pela autoridade policial e monitoramento de viaturas em tempo real.
        </p>

        <div className="hero-actions">
          <Link to="/registrar-cidadao" className="btn btn-primary">
            Registrar Ocorrência
          </Link>
          <Link to="/consulta" className="btn btn-secondary">
            Consultar Protocolo
          </Link>
        </div>
      </main>

      {/* ── Como funciona ─────────────────────────────────────────────── */}
      <section className="landing-section landing-section--alt">
        <div className="section-inner">
          <h2 className="section-title">Como Funciona</h2>
          <div className="steps-grid">
            <div className="step-card">
              <span className="step-number">01</span>
              <h3>Registre sua Ocorrência</h3>
              <p>Preencha o formulário online com os detalhes do fato — sem precisar ir até a delegacia. Disponível 24 horas por dia.</p>
            </div>
            <div className="step-card">
              <span className="step-number">02</span>
              <h3>Receba seu Protocolo</h3>
              <p>Após o envio, você recebe imediatamente um número de protocolo oficial. Guarde-o para acompanhar o andamento do seu caso.</p>
            </div>
            <div className="step-card">
              <span className="step-number">03</span>
              <h3>Acompanhe o Andamento</h3>
              <p>Use o número de protocolo para consultar, a qualquer momento, em qual etapa da triagem policial sua ocorrência se encontra.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Cards de ação principais ──────────────────────────────────── */}
      <section className="landing-section">
        <div className="section-inner">
          <h2 className="section-title">Acesse os Serviços</h2>
          <div className="action-cards-grid">

            <Link to="/registrar-cidadao" className="action-card">
              <div className="action-card-icon">
                <IconDocument />
              </div>
              <h3>Registrar Ocorrência</h3>
              <p>
                Comunique furtos, extravios, ameaças e outros fatos de forma rápida,
                sem filas e com localização no mapa.
              </p>
              <div className="action-card-footer">
                Registrar agora <span aria-hidden="true">→</span>
              </div>
            </Link>

            <Link to="/consulta" className="action-card">
              <div className="action-card-icon">
                <IconSearch />
              </div>
              <h3>Consultar Protocolo</h3>
              <p>
                Acompanhe a situação e o andamento da sua ocorrência em tempo real
                utilizando o código do protocolo oficial.
              </p>
              <div className="action-card-footer">
                Verificar status <span aria-hidden="true">→</span>
              </div>
            </Link>

            <Link to="/login" className="action-card">
              <div className="action-card-icon">
                <IconShield />
              </div>
              <h3>Painel Operacional</h3>
              <p>
                Acesso restrito para Agentes de campo, Delegados de triagem
                e Operadores da Central de Despacho.
              </p>
              <div className="action-card-footer">
                Entrar no sistema <span aria-hidden="true">→</span>
              </div>
            </Link>

          </div>
        </div>
      </section>

      {/* ── O que pode ser registrado ─────────────────────────────────── */}
      <section className="landing-section landing-section--alt">
        <div className="section-inner">
          <h2 className="section-title">O que pode ser registrado online?</h2>
          <p className="section-subtitle">
            O sistema aceita registros de fatos que não configurem situação de emergência imediata.
            Para emergências, ligue <strong>190</strong>.
          </p>
          <div className="types-grid">
            {[
              { titulo: 'Furto ou Roubo', desc: 'Subtração de bens pessoais, eletrônicos, veículos ou outros objetos de valor.' },
              { titulo: 'Perda ou Extravio', desc: 'Documentos, carteiras, chaves, celulares e outros objetos pessoais extraviados.' },
              { titulo: 'Acidente de Trânsito sem Vítima', desc: 'Colisões, abalroamentos ou danos a veículos sem lesionados.' },
              { titulo: 'Ameaça', desc: 'Declarações, mensagens ou gestos que configurem ameaça à integridade física ou psicológica.' },
              { titulo: 'Perturbação do Sossego', desc: 'Som excessivo, barulho perturbador em horários inadequados.' },
              { titulo: 'Dano ao Patrimônio', desc: 'Destruição, pichação ou dano doloso a bens públicos ou privados.' },
            ].map(({ titulo, desc }) => (
              <div key={titulo} className="type-card">
                <h4>{titulo}</h4>
                <p>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Exemplos de registros ─────────────────────────────────────── */}
      <section className="landing-section">
        <div className="section-inner">
          <h2 className="section-title">Exemplos de Registros Recentes</h2>
          <p className="section-subtitle">
            Os dados abaixo são fictícios e utilizados apenas para ilustração do sistema.
          </p>
          <div className="table-wrap">
            <table className="tabela">
              <thead>
                <tr>
                  <th>Protocolo</th>
                  <th>Natureza</th>
                  <th>Local</th>
                  <th>Data</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { proto: 'SGOPI-2026-000140', nat: 'Furto', local: 'Centro, Alegrete/RS', data: '19/09/2026', status: 'Aguardando Revisão', cor: 'var(--warn)' },
                  { proto: 'SGOPI-2026-000137', nat: 'Ameaça', local: 'Bairro Piola', data: '19/09/2026', status: 'Validada', cor: 'var(--ok)' },
                  { proto: 'SGOPI-2026-000133', nat: 'Perturbação do Sossego', local: 'Av. Brasil', data: '18/09/2026', status: 'Em Atendimento', cor: 'var(--primary)' },
                  { proto: 'SGOPI-2026-000120', nat: 'Dano ao Patrimônio', local: 'Praça da República', data: '18/09/2026', status: 'Encerrada', cor: 'var(--muted)' },
                  { proto: 'SGOPI-2026-000115', nat: 'Extravio de Documento', local: 'Bairro São Roque', data: '17/09/2026', status: 'Validada', cor: 'var(--ok)' },
                ].map((row) => (
                  <tr key={row.proto}>
                    <td><code style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{row.proto}</code></td>
                    <td>{row.nat}</td>
                    <td>{row.local}</td>
                    <td>{row.data}</td>
                    <td><span style={{ color: row.cor, fontWeight: 600 }}>{row.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── Consulta integrada ───────────────────────────────────────── */}
      <section className="landing-section landing-section--alt">
        <div className="section-inner" style={{ textAlign: 'center' }}>
          <h2 className="section-title">Já registrou uma ocorrência?</h2>
          <p className="section-subtitle">
            Digite seu número de protocolo para consultar o status atual.
          </p>
          <form
            className="hero-search-form"
            onSubmit={(e) => {
              e.preventDefault();
              const input = (e.currentTarget.elements.namedItem('protocolo') as HTMLInputElement).value.trim().toUpperCase();
              if (input) window.location.href = `/consulta?protocolo=${encodeURIComponent(input)}`;
            }}
          >
            <input
              name="protocolo"
              type="text"
              placeholder="SGOPI-2026-000001"
              style={{ fontFamily: 'monospace', fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase' }}
              aria-label="Número do protocolo"
            />
            <button type="submit" className="btn btn-primary">Consultar</button>
          </form>
          <p className="muted small" style={{ marginTop: 12 }}>
            Exemplo de protocolo: SGOPI-2026-000137
          </p>
        </div>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────────────── */}
      <section className="landing-section">
        <div className="section-inner">
          <h2 className="section-title">Perguntas Frequentes</h2>
          <div className="faq-list">
            {[
              {
                q: 'Preciso ter conta para registrar uma ocorrência?',
                a: 'Não. O Portal do Cidadão é totalmente aberto. Você não precisa criar cadastro nem fazer login para registrar uma ocorrência ou consultar seu protocolo.',
              },
              {
                q: 'Qual a diferença entre este sistema e ligar para o 190?',
                a: 'O 190 é para emergências em andamento. Este sistema é para registro de fatos não emergenciais, como furtos já ocorridos, extravios e perturbações. Se houver risco imediato, ligue 190.',
              },
              {
                q: 'Quanto tempo leva para minha ocorrência ser analisada?',
                a: 'O prazo de triagem pode variar. Você pode acompanhar em tempo real pelo número de protocolo. Geralmente ocorrências de menor complexidade são analisadas em até 72 horas.',
              },
              {
                q: 'Posso registrar em nome de outra pessoa?',
                a: 'Sim, desde que você informe os dados do real solicitante. O campo de identificação do solicitante aceita o nome de quem está comunicando o fato.',
              },
              {
                q: 'O que significa "Em Correção"?',
                a: 'Significa que o Delegado solicitou ajustes na descrição ou nos dados da ocorrência. Acompanhe pelo protocolo e retorne à delegacia se necessário.',
              },
              {
                q: 'Minha ocorrência foi rejeitada. O que fazer?',
                a: 'A rejeição pode ocorrer quando o fato não configura ocorrência registrável pelo sistema ou está fora da jurisdição. Nesse caso, recomendamos ir pessoalmente à delegacia mais próxima.',
              },
            ].map(({ q, a }) => (
              <details key={q} className="faq-item">
                <summary className="faq-question">{q}</summary>
                <p className="faq-answer">{a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="footer-inner">

          <div className="footer-col">
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <LogoSgopi size={22} color="var(--primary)" />
              <strong>SGOPI SENTINELA</strong>
            </div>
            <p>Sistema de Gestão de Ocorrências Policiais Integradas</p>
            <p>Universidade Federal do Pampa — Campus Alegrete</p>
            <p className="muted small">Resolução de Problemas IV (AL0343) — 2026/1</p>
          </div>

          <div className="footer-col">
            <h4>Links Rápidos</h4>
            <ul className="footer-links">
              <li><Link to="/">Início</Link></li>
              <li><Link to="/registrar-cidadao">Registrar Ocorrência</Link></li>
              <li><Link to="/consulta">Consultar Protocolo</Link></li>
              <li><Link to="/login">Acesso Policial</Link></li>
            </ul>
          </div>

          <div className="footer-col">
            <h4>Emergências</h4>
            <ul className="footer-links footer-emergency">
              <li><strong>190</strong> — Polícia Militar</li>
              <li><strong>192</strong> — SAMU</li>
              <li><strong>193</strong> — Corpo de Bombeiros</li>
              <li><strong>156</strong> — Defesa Civil</li>
            </ul>
          </div>

          <div className="footer-col">
            <h4>Contato Institucional</h4>
            <address className="footer-address">
              <p>Delegacia de Polícia Civil — Alegrete/RS</p>
              <p>Rua Barão do Triunfo, 100 — Centro</p>
              <p>Tel: (55) 3422-0000</p>
              <p>sgopi@unipampa.edu.br</p>
              <p className="muted small">Seg a Sex, 08h–18h</p>
            </address>
          </div>

        </div>
        <div className="footer-bottom">
          SGOPI Sentinela — Desenvolvido pela Equipe de Engenharia de Software — Unipampa Alegrete — 2026
        </div>
      </footer>
    </div>
  );
};

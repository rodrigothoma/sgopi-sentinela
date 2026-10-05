import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useConfirmacao } from '../components/common/ConfirmDialog';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { usuariosService } from '../services/usuariosService';
import { PAPEIS_ATRIBUIVEIS, type CadastrarUsuarioRequest, type Papel, type UsuarioGestao } from '../types/api';

const TAMANHO_MINIMO_SENHA = 8;
const LOGIN_VALIDO = /^[a-z0-9._-]{3,50}$/;
const vazio = (): CadastrarUsuarioRequest => ({ nome: '', login: '', senha: '', papel: 'AGENTE' });

/** Sugestão #13: o Supervisor cadastra, troca o papel, desativa e reativa usuários — nunca apaga. */
export const EfetivoPage: React.FC = () => {
  const { t } = useTranslation('common');
  const { avisar } = useToast();
  const { usuario: eu } = useAuth();
  const [confirmar, dialogoConfirmacao] = useConfirmacao();
  const [usuarios, setUsuarios] = useState<UsuarioGestao[]>([]);
  const [form, setForm] = useState<CadastrarUsuarioRequest>(vazio());
  const [ocupado, setOcupado] = useState<string | null>(null);
  const [mostrarInativos, setMostrarInativos] = useState(true);

  const carregar = useCallback(async () => {
    try {
      setUsuarios(await usuariosService.listarGestao());
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [avisar]);

  useEffect(() => { void carregar(); }, [carregar]);

  const visiveis = useMemo(
    () => usuarios.filter((u) => mostrarInativos || u.ativo).sort((a, b) => Number(b.ativo) - Number(a.ativo) || a.nome.localeCompare(b.nome)),
    [usuarios, mostrarInativos],
  );

  const substituir = (atualizado: UsuarioGestao) => setUsuarios((lista) => lista.map((u) => (u.id === atualizado.id ? atualizado : u)));

  const executar = async (id: string, acao: () => Promise<UsuarioGestao>, mensagemOk: string) => {
    setOcupado(id);
    try {
      substituir(await acao());
      avisar(mensagemOk, 'sucesso');
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setOcupado(null);
    }
  };

  const erroCadastro = (): string | null => {
    if (!form.nome.trim()) return t('efetivo.erro_nome');
    if (!LOGIN_VALIDO.test(form.login.trim().toLowerCase())) return t('efetivo.erro_login');
    if (form.senha.length < TAMANHO_MINIMO_SENHA) return t('efetivo.erro_senha', { minimo: TAMANHO_MINIMO_SENHA });
    return null;
  };

  const cadastrar = async (e: React.FormEvent) => {
    e.preventDefault();
    const erro = erroCadastro();
    if (erro) {
      avisar(erro, 'erro');
      return;
    }
    setOcupado('novo');
    try {
      const novo = await usuariosService.cadastrar({ ...form, nome: form.nome.trim(), login: form.login.trim().toLowerCase() });
      setUsuarios((lista) => [...lista, novo]);
      setForm(vazio());
      avisar(t('efetivo.ok_cadastro', { login: novo.login }), 'sucesso');
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    } finally {
      setOcupado(null);
    }
  };

  const alterarPapel = async (u: UsuarioGestao, papel: Papel) => {
    if (papel === u.papel) return;
    if (!(await confirmar(t('efetivo.confirmar_papel', { nome: u.nome, papel: t(`papel.${papel}`) })))) return;
    await executar(u.id, () => usuariosService.alterarPapel(u.id, papel), t('efetivo.ok_papel'));
  };

  const alternarSituacao = async (u: UsuarioGestao) => {
    const chave = u.ativo ? 'confirmar_desativar' : 'confirmar_reativar';
    if (!(await confirmar(t(`efetivo.${chave}`, { nome: u.nome })))) return;
    await executar(
      u.id,
      () => (u.ativo ? usuariosService.desativar(u.id) : usuariosService.reativar(u.id)),
      t(u.ativo ? 'efetivo.ok_desativar' : 'efetivo.ok_reativar'),
    );
  };

  return (
    <div className="pagina efetivo">
      {dialogoConfirmacao}
      <h1>{t('efetivo.titulo')}</h1>
      <p className="muted">{t('efetivo.subtitulo')}</p>

      <section className="card">
        <h3>{t('efetivo.novo')}</h3>
        <form className="efetivo-form" onSubmit={cadastrar} noValidate>
          <label>{t('efetivo.nome')}
            <input value={form.nome} maxLength={255} onChange={(e) => setForm({ ...form, nome: e.target.value })} />
          </label>
          <label>{t('efetivo.login')}
            <input value={form.login} maxLength={50} autoComplete="off" onChange={(e) => setForm({ ...form, login: e.target.value })} />
          </label>
          <label>{t('efetivo.senha_inicial')}
            <input type="password" value={form.senha} maxLength={128} autoComplete="new-password" onChange={(e) => setForm({ ...form, senha: e.target.value })} />
          </label>
          <label>{t('efetivo.papel')}
            <select value={form.papel} onChange={(e) => setForm({ ...form, papel: e.target.value as Papel })}>
              {PAPEIS_ATRIBUIVEIS.map((p) => <option key={p} value={p}>{t(`papel.${p}`)}</option>)}
            </select>
          </label>
          <button type="submit" className="btn btn-primary" disabled={ocupado === 'novo'}>{t('efetivo.cadastrar')}</button>
        </form>
        <p className="muted small">{t('efetivo.dica_senha')}</p>
      </section>

      <section className="card">
        <div className="cabecalho-lista">
          <h3>{t('efetivo.usuarios')} <span className="muted">({usuarios.filter((u) => u.ativo).length}/{usuarios.length})</span></h3>
          <label className="efetivo-toggle">
            <input type="checkbox" checked={mostrarInativos} onChange={(e) => setMostrarInativos(e.target.checked)} />
            {t('efetivo.mostrar_inativos')}
          </label>
        </div>
        <div className="tabela-rolavel">
          <table className="tabela efetivo-tabela">
            <thead>
              <tr>
                <th scope="col">{t('efetivo.nome')}</th>
                <th scope="col">{t('efetivo.login')}</th>
                <th scope="col">{t('efetivo.papel')}</th>
                <th scope="col">{t('efetivo.situacao')}</th>
                <th scope="col"><span className="sr-only">{t('efetivo.acoes')}</span></th>
              </tr>
            </thead>
            <tbody>
              {visiveis.map((u) => {
                const proprio = u.id === eu?.id;
                return (
                  <tr key={u.id} className={u.ativo ? '' : 'inativo'}>
                    <td>{u.nome}{proprio && <span className="muted small"> · {t('efetivo.voce')}</span>}</td>
                    <td><code>{u.login}</code></td>
                    <td>
                      <select
                        aria-label={t('efetivo.papel_de', { nome: u.nome })}
                        value={u.papel}
                        disabled={proprio || ocupado === u.id}
                        title={proprio ? t('efetivo.proprio') : undefined}
                        onChange={(e) => void alterarPapel(u, e.target.value as Papel)}
                      >
                        {PAPEIS_ATRIBUIVEIS.map((p) => <option key={p} value={p}>{t(`papel.${p}`)}</option>)}
                      </select>
                    </td>
                    <td><span className={`badge ${u.ativo ? 'badge-ATIVA' : 'badge-ARQUIVADA'}`}>{t(u.ativo ? 'efetivo.ativo' : 'efetivo.inativo')}</span></td>
                    <td>
                      <button
                        className={`btn btn-sm ${u.ativo ? 'btn-danger' : ''}`}
                        disabled={proprio || ocupado === u.id}
                        title={proprio ? t('efetivo.proprio') : undefined}
                        onClick={() => void alternarSituacao(u)}
                      >
                        {t(u.ativo ? 'efetivo.desativar' : 'efetivo.reativar')}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};

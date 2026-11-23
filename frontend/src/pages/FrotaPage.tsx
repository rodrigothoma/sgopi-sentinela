import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StatusBadge } from '../components/StatusBadge';
import { useConfirmacao } from '../components/common/ConfirmDialog';
import { useTempoRealListener } from '../hooks/useTempoReal';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { viaturasService } from '../services/viaturasService';
import type { Viatura } from '../types/api';
import { formatarDataHora } from '../utils/datas';

/** Gestão do cadastro da frota; situação e telemetria permanecem independentes da edição. */
export const FrotaPage: React.FC = () => {
  const { t } = useTranslation(['painel', 'common']);
  const { avisar } = useToast();
  const [confirmar, dialogo] = useConfirmacao();
  const [viaturas, setViaturas] = useState<Viatura[]>([]);
  const [prefixo, setPrefixo] = useState('');
  const [placa, setPlaca] = useState('');
  const [responsavel, setResponsavel] = useState('');
  const [editando, setEditando] = useState<Viatura | null>(null);
  const [ocupado, setOcupado] = useState(false);

  const carregar = useCallback(async () => {
    try { setViaturas(await viaturasService.listar()); }
    catch (err) { avisar(mensagemDeErro(err), 'erro'); }
  }, [avisar]);

  useEffect(() => { void carregar(); }, [carregar]);
  useTempoRealListener({
    onReconectar: carregar,
    onEvento: (evento) => {
      if (['ViaturaCadastroAlterado', 'ViaturaExcluida', 'ViaturaSituacaoAlterada'].includes(evento.tipo)) void carregar();
    },
  });

  const limpar = () => {
    setPrefixo(''); setPlaca(''); setResponsavel(''); setEditando(null);
  };
  const editar = (v: Viatura) => {
    setEditando(v); setPrefixo(v.prefixo); setPlaca(v.placa); setResponsavel(v.responsavel ?? '');
  };
  const salvar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (ocupado) return;
    setOcupado(true);
    try {
      const nome = responsavel.trim() || null;
      if (editando) await viaturasService.editar(editando.id, { prefixo, placa, responsavel: nome, versao: editando.versao });
      else await viaturasService.cadastrar(prefixo, placa, nome);
      avisar(t(editando ? 'painel:frota.atualizada' : 'painel:frota.cadastrada'), 'sucesso');
      limpar();
      await carregar();
    } catch (err) { avisar(mensagemDeErro(err), 'erro'); }
    finally { setOcupado(false); }
  };
  const alternar = async (v: Viatura) => {
    setOcupado(true);
    try {
      const nova = v.situacao === 'INDISPONIVEL' ? 'DISPONIVEL' : 'INDISPONIVEL';
      await viaturasService.alterarSituacao(v.id, nova);
      avisar(t(nova === 'DISPONIVEL' ? 'painel:frota.marcada_disponivel' : 'painel:frota.marcada_indisponivel', { prefixo: v.prefixo }), 'sucesso');
      await carregar();
    } catch (err) { avisar(mensagemDeErro(err), 'erro'); }
    finally { setOcupado(false); }
  };
  const excluir = async (v: Viatura) => {
    if (!(await confirmar(t('painel:frota.confirmar_exclusao', { prefixo: v.prefixo })))) return;
    setOcupado(true);
    try {
      await viaturasService.excluir(v.id, v.versao);
      if (editando?.id === v.id) limpar();
      avisar(t('painel:frota.excluida'), 'sucesso');
      await carregar();
    } catch (err) { avisar(mensagemDeErro(err), 'erro'); }
    finally { setOcupado(false); }
  };

  return (
    <div className="pagina">
      <h1>{t('painel:frota.titulo')}</h1>
      <form className="card frota-formulario" onSubmit={salvar} data-cy="frota-formulario">
        {editando && <p className="frota-editando">{t('painel:frota.editando', { prefixo: editando.prefixo })}</p>}
        <label>{t('painel:frota.prefixo')}<input data-cy="frota-prefixo" value={prefixo} onChange={(e) => setPrefixo(e.target.value)} required maxLength={20} disabled={ocupado} /></label>
        <label>{t('painel:frota.placa')}<input data-cy="frota-placa" value={placa} onChange={(e) => setPlaca(e.target.value)} required maxLength={10} disabled={ocupado} /></label>
        <label>{t('painel:frota.responsavel')}<input data-cy="frota-responsavel" value={responsavel} onChange={(e) => setResponsavel(e.target.value)} maxLength={120} disabled={ocupado} /></label>
        <div className="acoes">
          <button className="btn btn-primary" disabled={ocupado} data-cy="frota-salvar">{t(editando ? 'painel:frota.salvar' : 'painel:frota.cadastrar')}</button>
          {editando && <button type="button" className="btn btn-outline" disabled={ocupado} onClick={limpar} data-cy="frota-cancelar">{t('painel:frota.cancelar')}</button>}
        </div>
      </form>
      <div className="frota-tabela">
        <table className="tabela card">
          <thead><tr><th>{t('painel:frota.prefixo')}</th><th>{t('painel:frota.placa')}</th><th>{t('painel:inspecao.responsavel')}</th><th>{t('painel:situacao')}</th><th>{t('painel:sinal')}</th><th>{t('painel:ultima_posicao')}</th><th>{t('painel:frota.acoes')}</th></tr></thead>
          <tbody>
            {!viaturas.length && <tr><td colSpan={7}>{t('painel:frota.vazio')}</td></tr>}
            {viaturas.map((v) => {
              const emAtendimento = v.situacao === 'EM_DESLOCAMENTO' || v.situacao === 'OPERANDO';
              return <tr key={v.id} data-cy="frota-viatura">
                <td><strong>{v.prefixo}</strong></td><td>{v.placa}</td><td>{v.responsavel || t('painel:frota.sem_responsavel')}</td>
                <td><StatusBadge status={v.situacao} grupo="situacao" /></td><td><StatusBadge status={v.sinal} grupo="sinal" /></td>
                <td className="muted">{v.posicao_registrada_em ? formatarDataHora(v.posicao_registrada_em) : '—'}</td>
                <td><div className="acoes frota-acoes">
                  <button type="button" className="btn btn-sm" disabled={ocupado} onClick={() => editar(v)} data-cy="frota-editar">{t('painel:frota.editar')}</button>
                  {!emAtendimento && <button type="button" className="btn btn-sm" disabled={ocupado} onClick={() => alternar(v)}>{t(v.situacao === 'INDISPONIVEL' ? 'painel:frota.disponibilizar' : 'painel:frota.indisponibilizar')}</button>}
                  <button type="button" className="btn btn-danger btn-sm" disabled={ocupado || emAtendimento} title={emAtendimento ? t('painel:frota.exclusao_bloqueada') : undefined} onClick={() => excluir(v)} data-cy="frota-excluir">{t('painel:frota.excluir')}</button>
                </div></td>
              </tr>;
            })}
          </tbody>
        </table>
      </div>
      {dialogo}
    </div>
  );
};

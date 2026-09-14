import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { StatusBadge } from '../components/StatusBadge';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { viaturasService } from '../services/viaturasService';
import type { Viatura } from '../types/api';

/** Operador: cadastro e situação manual da frota (RF15). */
export const FrotaPage: React.FC = () => {
  const { t } = useTranslation(['painel', 'common']);
  const { avisar } = useToast();
  const [viaturas, setViaturas] = useState<Viatura[]>([]);
  const [prefixo, setPrefixo] = useState('');
  const [placa, setPlaca] = useState('');

  const carregar = useCallback(async () => {
    try {
      setViaturas(await viaturasService.listar());
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  }, [avisar]);

  useEffect(() => {
    carregar();
  }, [carregar]);

  const cadastrar = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await viaturasService.cadastrar(prefixo, placa);
      setPrefixo('');
      setPlaca('');
      avisar(t('painel:frota.cadastrada'), 'sucesso');
      carregar();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  const alternar = async (v: Viatura) => {
    try {
      await viaturasService.alterarSituacao(v.id, v.situacao === 'INDISPONIVEL' ? 'DISPONIVEL' : 'INDISPONIVEL');
      carregar();
    } catch (err) {
      avisar(mensagemDeErro(err), 'erro');
    }
  };

  return (
    <div className="pagina">
      <h1>{t('painel:frota.titulo')}</h1>
      <form className="card form-inline" onSubmit={cadastrar}>
        <input placeholder={t('painel:frota.prefixo')} value={prefixo} onChange={(e) => setPrefixo(e.target.value)} required />
        <input placeholder={t('painel:frota.placa')} value={placa} onChange={(e) => setPlaca(e.target.value)} required />
        <button className="btn btn-primary">{t('painel:frota.cadastrar')}</button>
      </form>
      <table className="tabela card">
        <thead>
          <tr><th>{t('painel:frota.prefixo')}</th><th>{t('painel:frota.placa')}</th><th>{t('painel:situacao')}</th><th>{t('painel:sinal')}</th><th>{t('painel:ultima_posicao')}</th><th></th></tr>
        </thead>
        <tbody>
          {viaturas.map((v) => (
            <tr key={v.id}>
              <td><strong>{v.prefixo}</strong></td>
              <td>{v.placa}</td>
              <td><StatusBadge status={v.situacao} grupo="situacao" /></td>
              <td><StatusBadge status={v.sinal} grupo="sinal" /></td>
              <td className="muted">{v.posicao_registrada_em ? new Date(v.posicao_registrada_em).toLocaleString() : '—'}</td>
              <td>
                {(v.situacao === 'DISPONIVEL' || v.situacao === 'INDISPONIVEL') && (
                  <button className="btn btn-sm" onClick={() => alternar(v)}>
                    {v.situacao === 'INDISPONIVEL' ? t('painel:frota.disponibilizar') : t('painel:frota.indisponibilizar')}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

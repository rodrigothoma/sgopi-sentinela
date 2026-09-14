import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { OcorrenciaForm, paraRequest, valoresVazios } from '../components/ocorrencias/OcorrenciaForm';
import { useToast } from '../hooks/useToast';
import { mensagemDeErro } from '../services/api';
import { ocorrenciasService } from '../services/ocorrenciasService';

export const RegistrarOcorrenciaPage: React.FC = () => {
  const { t } = useTranslation(['ocorrencias', 'common']);
  const { avisar } = useToast();
  const [ocupado, setOcupado] = useState(false);
  const [protocolo, setProtocolo] = useState<string | null>(null);
  const [chave, setChave] = useState(0); // reinicia o formulário após sucesso

  return (
    <div className="pagina">
      <h1>{t('ocorrencias:page_title')}</h1>
      {protocolo && (
        <div className="alerta sucesso">
          {t('ocorrencias:toast.success', { protocolo })} — {t('ocorrencias:registro.aguardando')}
        </div>
      )}
      <OcorrenciaForm
        key={chave}
        inicial={valoresVazios()}
        rotuloEnviar={t('common:actions.submit')}
        ocupado={ocupado}
        permitirEvidencias
        onSubmit={async (v) => {
          setOcupado(true);
          try {
            const r = await ocorrenciasService.registrar(paraRequest(v));
            setProtocolo(r.numero_protocolo);
            try {
              for (const arquivo of v.evidencias) {
                await ocorrenciasService.anexarEvidencia(r.ocorrencia_id, arquivo);
              }
            } catch (err) {
              avisar(mensagemDeErro(err, t('ocorrencias:evidencias.erro_upload')), 'erro');
              return;
            }
            setChave((k) => k + 1);
            avisar(t('ocorrencias:toast.success', { protocolo: r.numero_protocolo }), 'sucesso');
            window.scrollTo({ top: 0, behavior: 'smooth' });
          } catch (err) {
            avisar(mensagemDeErro(err, t('ocorrencias:toast.error_server')), 'erro');
          } finally {
            setOcupado(false);
          }
        }}
      />
    </div>
  );
};

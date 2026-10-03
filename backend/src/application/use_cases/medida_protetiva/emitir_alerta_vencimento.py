"""
Caso de uso: Emitir Alerta de Vencimento de Medida Protetiva (RF09 / UC12).

Dispara alertas em lote (automático para medidas com vencimento em <= 72h) ou
manual para uma medida específica, enviando e-mail formal à vítima/delegado
e registrando notificação interna e auditoria imutável (RNF03).
"""
from __future__ import annotations

import logging
from datetime import date, datetime
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_alertas_vencimento_medida import InterfaceEmitirAlertaVencimentoMedida
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.porta_notificacao_email import PortaNotificacaoEmail
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_medida_protetiva import RepositorioMedidaProtetiva
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.medida_protetiva.entity import MedidaProtetiva, StatusMedida
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from domain.shared.eventos import EventoDominio
from domain.shared.exceptions import EntidadeNaoEncontradaError

log = logging.getLogger("sgopi.medidas.alerta")


class EmitirAlertaVencimentoMedidaUseCase(InterfaceEmitirAlertaVencimentoMedida):
    def __init__(
        self,
        repositorio_medida: RepositorioMedidaProtetiva,
        repositorio_ocorrencia: RepositorioOcorrencia,
        repositorio_notificacao: RepositorioNotificacao,
        porta_email: PortaNotificacaoEmail,
        porta_auditoria: PortaAuditoria,
        publicador_eventos: PublicadorEventos,
        relogio: Relogio,
        uow: UnidadeDeTrabalho | None = None,
    ) -> None:
        self._repo_medida = repositorio_medida
        self._repo_ocorrencia = repositorio_ocorrencia
        self._repo_notif = repositorio_notificacao
        self._porta_email = porta_email
        self._porta_auditoria = porta_auditoria
        self._publicador = publicador_eventos
        self._relogio = relogio
        self._uow = uow

    async def executar(
        self,
        ator: Ator,
        medida_id: UUID | None = None,
        email_destinatario_customizado: str | None = None,
    ) -> dict:
        agora = self._relogio.agora()
        hoje = agora.date() if isinstance(agora, datetime) else date.today()

        if medida_id is not None:
            # Modo manual: medida única
            medida = await self._repo_medida.buscar_por_id(medida_id)
            if medida is None:
                raise EntidadeNaoEncontradaError(f"Medida protetiva {medida_id} não encontrada.")
            resultado = await self._processar_alerta_medida(
                medida=medida,
                ator=ator,
                agora=agora,
                hoje=hoje,
                email_customizado=email_destinatario_customizado,
                manual=True,
            )
            return {
                "sucesso": True,
                "modo": "manual",
                "total_processadas": 1,
                "alertas_enviados": 1 if resultado["email_enviado"] or resultado["notificacao_gerada"] else 0,
                "detalhes": [resultado],
            }

        # Modo automático / Varredura em lote (UC12): todas as medidas ativas próximas do vencimento (<= 3 dias)
        medidas_ativas, _ = await self._repo_medida.listar(
            status=[StatusMedida.ATIVA, StatusMedida.RENOVADA],
            limit=500,
        )

        resultados = []
        enviados = 0
        for m in medidas_ativas:
            # Emite apenas se estiver a <= 3 dias (72h) do vencimento e ainda não tiver alerta recente enviado
            if m.esta_proxima_do_vencimento(hoje, dias_antecedencia=3):
                # Se já enviou alerta há menos de 48h, evita disparos repetidos no mesmo ciclo
                if m.alerta_vencimento_enviado_em is not None:
                    dias_desde_ultimo = (agora - m.alerta_vencimento_enviado_em).total_seconds() / 86400.0
                    if dias_desde_ultimo < 2.0:
                        continue

                res = await self._processar_alerta_medida(
                    medida=m,
                    ator=ator,
                    agora=agora,
                    hoje=hoje,
                    email_customizado=None,
                    manual=False,
                )
                resultados.append(res)
                if res["email_enviado"] or res["notificacao_gerada"]:
                    enviados += 1

        return {
            "sucesso": True,
            "modo": "automatico_lote",
            "total_processadas": len(medidas_ativas),
            "alertas_enviados": enviados,
            "detalhes": resultados,
        }

    async def _processar_alerta_medida(
        self,
        *,
        medida: MedidaProtetiva,
        ator: Ator,
        agora: datetime,
        hoje: date,
        email_customizado: str | None,
        manual: bool,
    ) -> dict:
        dias_restantes = medida.dias_restantes(hoje)
        ocorrencia = await self._repo_ocorrencia.buscar_por_id(medida.ocorrencia_id)

        nome_vitima = "Vítima Protegida"
        email_vitima: str | None = None
        nome_agressor = "Indivíduo Notificado"

        if ocorrencia is not None:
            for env in ocorrencia.envolvidos:
                if env.id == medida.vitima_id:
                    nome_vitima = env.nome
                    email_vitima = env.email
                elif env.id == medida.agressor_id:
                    nome_agressor = env.nome

        # Define destinatário de e-mail
        destinatario_final = (email_customizado or email_vitima or "").strip()
        email_sucesso = False

        if destinatario_final and "@" in destinatario_final:
            assunto = f"[SGOPI Sentinela] Alerta Oficial: Vencimento de Medida Protetiva ({medida.numero_referencia})"
            corpo_html = f"""
            <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden;">
                <div style="background-color: #0f172a; padding: 20px; color: #ffffff;">
                    <h2 style="margin: 0; font-size: 20px;">SGOPI Sentinela — Segurança Pública</h2>
                    <p style="margin: 4px 0 0 0; color: #94a3b8; font-size: 13px;">Comunicação Oficial de Proteção à Vítima</p>
                </div>
                <div style="padding: 24px;">
                    <p>Prezada(o) <strong>{nome_vitima}</strong>,</p>
                    <p>Informamos que a Medida Protetiva de Urgência sob o número de referência <strong>{medida.numero_referencia}</strong> atingiu a janela de acompanhamento de vigência.</p>
                    <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; margin: 16px 0;">
                        <p style="margin: 0; font-weight: bold; color: #991b1b;">Situação do Prazo:</p>
                        <p style="margin: 4px 0 0 0; color: #b91c1c;">Vencimento previsto para: <strong>{medida.data_vencimento.strftime('%d/%m/%Y')}</strong> ({dias_restantes} dia(s) restante(s)).</p>
                    </div>
                    <p><strong>Agressor Vinculado:</strong> {nome_agressor}</p>
                    <p><strong>Restrições Aplicadas:</strong> {', '.join(medida.tipos_restricao)}</p>
                    <p style="font-size: 13px; color: #64748b; margin-top: 24px;">Caso haja necessidade de prorrogação ou suporte de segurança emergencial, procure imediatamente a Delegacia Especializada ou a autoridade policial competente.</p>
                </div>
                <div style="background-color: #f8fafc; padding: 12px 24px; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0;">
                    Mensagem automatizada gerada pelo SGOPI Sentinela conforme a Lei 11.340 e diretrizes institucionais.
                </div>
            </div>
            """
            corpo_txt = (
                f"SGOPI Sentinela - Alerta Oficial\n"
                f"Medida Protetiva: {medida.numero_referencia}\n"
                f"Vítima: {nome_vitima}\n"
                f"Agressor: {nome_agressor}\n"
                f"Data de Vencimento: {medida.data_vencimento.strftime('%d/%m/%Y')} ({dias_restantes} dias restantes)\n"
                f"Restrições: {', '.join(medida.tipos_restricao)}\n"
            )
            try:
                email_sucesso = await self._porta_email.enviar_email(
                    para=destinatario_final,
                    assunto=assunto,
                    corpo_html=corpo_html,
                    corpo_texto=corpo_txt,
                )
            except Exception as e:
                log.warning("Falha ao enviar e-mail de vencimento de medida: %s", e)

        # 2. Gera notificação interna no sistema (para Delegados e Supervisores)
        msg_notif = (
            f"A medida {medida.numero_referencia} (Vítima: {nome_vitima}) vence em {dias_restantes} dia(s) "
            f"({medida.data_vencimento.strftime('%d/%m/%Y')})."
        )
        notif = Notificacao.criar(
            titulo=f"Vencimento de Medida: {medida.numero_referencia}",
            mensagem=msg_notif,
            tipo=TipoNotificacao.VENCIMENTO_MEDIDA,
            prioridade=PrioridadeNotificacao.ALTA if dias_restantes > 0 else PrioridadeNotificacao.CRITICA,
            usuario_id=medida.delegado_id,
            papel_destinatario="DELEGADO",
            link="/medidas",
            metadados={
                "medida_id": str(medida.id),
                "numero_referencia": medida.numero_referencia,
                "dias_restantes": dias_restantes,
                "data_vencimento": medida.data_vencimento.isoformat(),
            },
            instante=agora,
        )
        await self._repo_notif.salvar(notif)

        # 3. Transmite evento de tempo real
        await self._publicador.publicar(
            EventoDominio(
                tipo="MEDIDA_VENCIMENTO_ALERTA",
                ocorrido_em=agora,
                dados={
                    "medida_id": str(medida.id),
                    "numero_referencia": medida.numero_referencia,
                    "dias_restantes": dias_restantes,
                    "vencimento": medida.data_vencimento.isoformat(),
                    "email_enviado": email_sucesso,
                    "destinatario": destinatario_final,
                },
            )
        )

        # 4. Registra no log de auditoria imutável (UC12 / RNF03)
        await self._porta_auditoria.registrar(
            RegistroAuditoria(
                quem=ator.id,
                quando=agora,
                operacao="ALERTA_VENCIMENTO_MEDIDA",
                entidade="medidas_protetivas",
                entidade_id=str(medida.id),
                dados_depois={
                    "numero_referencia": medida.numero_referencia,
                    "dias_restantes": dias_restantes,
                    "email_destinatario": destinatario_final,
                    "email_enviado": email_sucesso,
                    "manual": manual,
                },
            )
        )

        # 5. Atualiza carimbo na medida
        medida.marcar_alerta_vencimento_enviado(agora)
        if self._uow:
            async with self._uow:
                await self._repo_medida.salvar(medida)
                await self._uow.commit()
        else:
            await self._repo_medida.salvar(medida)

        return {
            "medida_id": str(medida.id),
            "numero_referencia": medida.numero_referencia,
            "dias_restantes": dias_restantes,
            "destinatario_email": destinatario_final,
            "email_enviado": email_sucesso,
            "notificacao_gerada": True,
        }

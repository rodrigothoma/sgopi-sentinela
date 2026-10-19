"""
Casos de uso para Comunicação Interagências (RF10 / UC10).
"""
from __future__ import annotations

from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_comunicacoes_interagencias import (
    InterfaceConsultarComunicacoesInteragencias,
    InterfaceEnviarComunicacaoInteragencias,
    InterfaceResponderComunicacaoInteragencias,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_comunicacao_interagencias import (
    GeradorNumeroOficio,
    RepositorioComunicacaoInteragencias,
)
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.interagencias.entity import ComunicacaoInteragencias
from domain.notificacao.entity import Notificacao, PrioridadeNotificacao, TipoNotificacao
from domain.shared.eventos import EventoDominio
from domain.shared.exceptions import EntidadeNaoEncontradaError


class EnviarComunicacaoInteragenciasUseCase(InterfaceEnviarComunicacaoInteragencias):
    def __init__(
        self,
        repositorio_comunicacao: RepositorioComunicacaoInteragencias,
        gerador_oficio: GeradorNumeroOficio,
        repositorio_ocorrencia: RepositorioOcorrencia,
        repositorio_notificacao: RepositorioNotificacao,
        porta_auditoria: PortaAuditoria,
        publicador_eventos: PublicadorEventos,
        relogio: Relogio,
        uow: UnidadeDeTrabalho | None = None,
    ) -> None:
        self._repo = repositorio_comunicacao
        self._gerador = gerador_oficio
        self._repo_ocorrencia = repositorio_ocorrencia
        self._repo_notif = repositorio_notificacao
        self._porta_auditoria = porta_auditoria
        self._publicador = publicador_eventos
        self._relogio = relogio
        self._uow = uow

    async def executar(
        self,
        ator: Ator,
        departamento_origem: str,
        departamentos_destinatarios: list[str],
        assunto: str,
        corpo: str,
        protocolo_ocorrencia: str | None = None,
        nivel_sigilo: str = "PADRAO",
        prioridade: str = "MEDIA",
    ) -> ComunicacaoInteragencias:
        agora = self._relogio.agora()
        ano = agora.year

        # Se houver protocolo informado, valida se existe
        if protocolo_ocorrencia and protocolo_ocorrencia.strip():
            prot_limpo = protocolo_ocorrencia.strip()
            ocorrencia = await self._repo_ocorrencia.buscar_por_protocolo(prot_limpo)
            if ocorrencia is None:
                raise EntidadeNaoEncontradaError(f"Ocorrência de protocolo '{prot_limpo}' não foi localizada.")

        numero_oficio = await self._gerador.proximo_numero(ano)

        comunicacao = ComunicacaoInteragencias.criar(
            numero_oficio=numero_oficio,
            departamento_origem=departamento_origem,
            departamentos_destinatarios=departamentos_destinatarios,
            remetente_id=ator.id,
            assunto=assunto,
            corpo=corpo,
            protocolo_ocorrencia=protocolo_ocorrencia,
            nivel_sigilo=nivel_sigilo,
            prioridade=prioridade,
            instante=agora,
        )

        async def _salvar_tudo():
            salva_obj = await self._repo.salvar(comunicacao)
            for dep in salva_obj.departamentos_destinatarios:
                notif = Notificacao.criar(
                    titulo=f"Novo Ofício Interagências: {salva_obj.numero_oficio}",
                    mensagem=f"Ofício recebido de {salva_obj.departamento_origem}: '{salva_obj.assunto}'",
                    tipo=TipoNotificacao.COMUNICACAO_INTERAGENCIAS,
                    prioridade=PrioridadeNotificacao.ALTA if salva_obj.prioridade in ("ALTA", "URGENTE") else PrioridadeNotificacao.MEDIA,
                    departamento_destinatario=dep,
                    link=f"/interagencias?oficio={salva_obj.numero_oficio}",
                    metadados={
                        "comunicacao_id": str(salva_obj.id),
                        "numero_oficio": salva_obj.numero_oficio,
                        "departamento_origem": salva_obj.departamento_origem,
                        "nivel_sigilo": salva_obj.nivel_sigilo.value if hasattr(salva_obj.nivel_sigilo, "value") else str(salva_obj.nivel_sigilo),
                    },
                    instante=agora,
                )
                await self._repo_notif.salvar(notif)

            await self._porta_auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="ENVIO_COMUNICACAO_INTERAGENCIAS",
                    entidade="comunicacoes_interagencias",
                    entidade_id=str(salva_obj.id),
                    dados_depois={
                        "numero_oficio": salva_obj.numero_oficio,
                        "origem": salva_obj.departamento_origem,
                        "destinatarios": salva_obj.departamentos_destinatarios,
                        "assunto": salva_obj.assunto,
                        "protocolo": salva_obj.protocolo_ocorrencia,
                    },
                )
            )
            return salva_obj

        if self._uow:
            async with self._uow:
                salva = await _salvar_tudo()
                await self._uow.commit()
        else:
            salva = await _salvar_tudo()

        # Transmite via WebSocket
        await self._publicador.publicar(
            EventoDominio(
                tipo="COMUNICACAO_INTERAGENCIAS_CRIADA",
                ocorrido_em=agora,
                dados={
                    "id": str(salva.id),
                    "numero_oficio": salva.numero_oficio,
                    "origem": salva.departamento_origem,
                    "destinatarios": salva.departamentos_destinatarios,
                    "assunto": salva.assunto,
                },
            )
        )

        return salva


class ConsultarComunicacoesInteragenciasUseCase(InterfaceConsultarComunicacoesInteragencias):
    def __init__(self, repositorio: RepositorioComunicacaoInteragencias) -> None:
        self._repo = repositorio

    async def executar(
        self,
        ator: Ator,
        departamento: str | None = None,
        protocolo: str | None = None,
    ) -> list[ComunicacaoInteragencias]:
        return await self._repo.listar(departamento=departamento, protocolo=protocolo)


class ResponderComunicacaoInteragenciasUseCase(InterfaceResponderComunicacaoInteragencias):
    def __init__(
        self,
        repositorio_comunicacao: RepositorioComunicacaoInteragencias,
        gerador_oficio: GeradorNumeroOficio,
        repositorio_notificacao: RepositorioNotificacao,
        porta_auditoria: PortaAuditoria,
        publicador_eventos: PublicadorEventos,
        relogio: Relogio,
        uow: UnidadeDeTrabalho | None = None,
    ) -> None:
        self._repo = repositorio_comunicacao
        self._gerador = gerador_oficio
        self._repo_notif = repositorio_notificacao
        self._porta_auditoria = porta_auditoria
        self._publicador = publicador_eventos
        self._relogio = relogio
        self._uow = uow

    async def executar(
        self,
        ator: Ator,
        mensagem_pai_id: UUID,
        departamento_origem: str,
        assunto: str,
        corpo: str,
        prioridade: str = "MEDIA",
    ) -> ComunicacaoInteragencias:
        pai = await self._repo.obter_por_id(mensagem_pai_id)
        if pai is None:
            raise EntidadeNaoEncontradaError("Comunicação original não encontrada.")

        agora = self._relogio.agora()
        numero_oficio = await self._gerador.proximo_numero(agora.year)

        # Destinatário da resposta é o departamento de origem da mensagem anterior
        destinatarios = [pai.departamento_origem]

        resposta = ComunicacaoInteragencias.criar(
            numero_oficio=numero_oficio,
            departamento_origem=departamento_origem,
            departamentos_destinatarios=destinatarios,
            remetente_id=ator.id,
            assunto=assunto if assunto.startswith("Re: ") else f"Re: {assunto}",
            corpo=corpo,
            protocolo_ocorrencia=pai.protocolo_ocorrencia,
            nivel_sigilo=pai.nivel_sigilo,
            prioridade=prioridade,
            mensagem_pai_id=mensagem_pai_id,
            instante=agora,
        )

        async def _salvar_resposta():
            salva_obj = await self._repo.salvar(resposta)
            notif = Notificacao.criar(
                titulo=f"Resposta a Ofício: {salva_obj.numero_oficio}",
                mensagem=f"Resposta recebida de {salva_obj.departamento_origem} ref. '{pai.numero_oficio}'",
                tipo=TipoNotificacao.COMUNICACAO_INTERAGENCIAS,
                usuario_id=pai.remetente_id,
                departamento_destinatario=pai.departamento_origem,
                link=f"/interagencias?oficio={pai.numero_oficio}",
                instante=agora,
            )
            await self._repo_notif.salvar(notif)
            await self._porta_auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="RESPOSTA_COMUNICACAO_INTERAGENCIAS",
                    entidade="comunicacoes_interagencias",
                    entidade_id=str(salva_obj.id),
                    dados_depois={"mensagem_pai_id": str(mensagem_pai_id), "numero_oficio": salva_obj.numero_oficio},
                )
            )
            return salva_obj

        if self._uow:
            async with self._uow:
                salva = await _salvar_resposta()
                await self._uow.commit()
        else:
            salva = await _salvar_resposta()

        return salva

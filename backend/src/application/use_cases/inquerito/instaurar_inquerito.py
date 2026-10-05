"""Caso de uso: Instaurar Inquérito Policial (RF06 / UC06)."""
from __future__ import annotations

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_inqueritos import (
    InqueritoOutput,
    InstaurarInqueritoInput,
    InterfaceInstaurarInquerito,
    OcorrenciaResumoInqueritoOutput,
)
from application.ports.outbound.gerador_numero_inquerito import GeradorNumeroInquerito
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_inquerito import RepositorioInquerito
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.inquerito.entity import Inquerito
from domain.ocorrencia.status import StatusOcorrencia
from domain.shared.exceptions import AcessoNegadoError, ConflitoError, EntidadeNaoEncontradaError
from domain.usuario.entity import Papel


class InstaurarInquerito(InterfaceInstaurarInquerito):
    def __init__(
        self,
        repositorio_inquerito: RepositorioInquerito,
        repositorio_ocorrencia: RepositorioOcorrencia,
        gerador_numero: GeradorNumeroInquerito,
        relogio: Relogio,
        uow: UnidadeDeTrabalho,
        auditoria: PortaAuditoria,
    ) -> None:
        self._repo_inquerito = repositorio_inquerito
        self._repo_ocorrencia = repositorio_ocorrencia
        self._gerador = gerador_numero
        self._relogio = relogio
        self._uow = uow
        self._auditoria = auditoria

    async def executar(self, ator: Ator, dados: InstaurarInqueritoInput) -> InqueritoOutput:
        if ator.papel != Papel.DELEGADO:
            raise AcessoNegadoError(
                "Apenas o Delegado de Polícia possui competência para instaurar inquérito policial.",
                chave="inquerito.apenas_delegado",
            )

        agora = self._relogio.agora()
        numero = await self._gerador.proximo(agora.year)

        # Validar e carregar ocorrências iniciais se informadas
        ocorrencias_carregadas = []
        ocorrencias_ids = list(dados.ocorrencias_iniciais_ids or [])
        for oc_id in ocorrencias_ids:
            oc = await self._repo_ocorrencia.buscar_por_id(oc_id)
            if not oc:
                raise EntidadeNaoEncontradaError(
                    f"Ocorrência {oc_id} não encontrada.",
                    chave="ocorrencia.nao_encontrada",
                    ocorrencia_id=str(oc_id),
                )
            if oc.status != StatusOcorrencia.VALIDADA:
                raise ConflitoError(
                    f"Apenas ocorrências validadas podem ser vinculadas (protocolo {oc.numero_protocolo} está {oc.status.value}).",
                    chave="inquerito.ocorrencia_nao_validada",
                )
            if oc.inquerito_id is not None:
                raise ConflitoError(
                    f"A ocorrência {oc.numero_protocolo} já pertence a outro inquérito.",
                    chave="inquerito.ocorrencia_ja_vinculada",
                )
            ocorrencias_carregadas.append(oc)

        inquerito = Inquerito.instaurar(
            numero=numero,
            ementa=dados.ementa,
            delegado_id=ator.id,
            instante=agora,
            ocorrencias_iniciais_ids=ocorrencias_ids,
        )

        async with self._uow:
            await self._repo_inquerito.salvar(inquerito)
            for oc in ocorrencias_carregadas:
                oc.vincular_inquerito(inquerito.id)
                await self._repo_ocorrencia.salvar(oc)

            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="inquerito.instaurar",
                    entidade="inquerito",
                    entidade_id=str(inquerito.id),
                    dados_depois={
                        "numero": inquerito.numero,
                        "ementa": inquerito.ementa,
                        "ocorrencias_vinculadas": [str(x) for x in ocorrencias_ids],
                    },
                    ip=ator.ip,
                )
            )
            await self._uow.commit()

        resumos = [
            OcorrenciaResumoInqueritoOutput(
                id=oc.id,
                numero_protocolo=oc.numero_protocolo,
                natureza=oc.natureza,
                localizacao=oc.localizacao,
                data_hora_fato=oc.data_hora_fato.isoformat(),
                status=oc.status.value,
            )
            for oc in ocorrencias_carregadas
        ]

        return InqueritoOutput(
            id=inquerito.id,
            numero=inquerito.numero,
            ementa=inquerito.ementa,
            delegado_id=inquerito.delegado_id,
            status=inquerito.status.value,
            data_abertura=inquerito.data_abertura.isoformat(),
            atualizado_em=inquerito.atualizado_em.isoformat() if inquerito.atualizado_em else inquerito.data_abertura.isoformat(),
            ocorrencias=resumos,
        )

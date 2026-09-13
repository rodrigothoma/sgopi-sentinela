"""Casos de uso de frota (RF15): CadastrarViatura, AlterarSituacaoViatura, ListarViaturas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_viaturas import (
    AlterarSituacaoInput,
    CadastrarViaturaInput,
    InterfaceAlterarSituacaoViatura,
    InterfaceCadastrarViatura,
    InterfaceListarViaturas,
    ViaturaOutput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.auditoria.entity import RegistroAuditoria
from domain.shared.exceptions import ConflitoError, EntidadeNaoEncontradaError, ValorInvalidoError
from domain.usuario.entity import Papel
from domain.viatura.entity import SituacaoViatura, Viatura
from domain.viatura.eventos import viatura_situacao_alterada

PAPEIS_GESTAO = (Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR)
PAPEIS_CONSULTA = (Papel.OPERADOR_CENTRAL, Papel.SUPERVISOR, Papel.DELEGADO, Papel.AGENTE)


def para_output(v: Viatura, agora: datetime, max_idade: int) -> ViaturaOutput:
    p = v.ultima_posicao
    return ViaturaOutput(
        id=v.id,
        prefixo=v.prefixo,
        placa=v.placa,
        situacao=v.situacao.value,
        latitude=p.coordenada.latitude if p else None,
        longitude=p.coordenada.longitude if p else None,
        posicao_registrada_em=p.registrada_em.isoformat() if p else None,
        sinal=v.sinal(agora, max_idade),
        versao=v.versao,
    )


async def carregar_viatura(repositorio: RepositorioViatura, viatura_id: UUID) -> Viatura:
    v = await repositorio.buscar_por_id(viatura_id)
    if v is None:
        raise EntidadeNaoEncontradaError("Viatura não encontrada.", chave="viatura.not_found")
    return v


class CadastrarViatura(InterfaceCadastrarViatura):
    def __init__(self, repositorio: RepositorioViatura, uow: UnidadeDeTrabalho, relogio: Relogio, auditoria: PortaAuditoria, max_idade: int) -> None:
        self._repositorio, self._uow, self._relogio, self._auditoria, self._max_idade = repositorio, uow, relogio, auditoria, max_idade

    async def executar(self, ator: Ator, input_dto: CadastrarViaturaInput) -> ViaturaOutput:
        ator.exigir_papel(*PAPEIS_GESTAO)
        agora = self._relogio.agora()
        viatura = Viatura(prefixo=input_dto.prefixo, placa=input_dto.placa, atualizada_em=agora)
        async with self._uow:
            if await self._repositorio.buscar_por_prefixo(viatura.prefixo):
                raise ConflitoError(f"Prefixo {viatura.prefixo} já cadastrado.", chave="viatura.prefixo_duplicado")
            if await self._repositorio.buscar_por_placa(viatura.placa):
                raise ConflitoError(f"Placa {viatura.placa} já cadastrada.", chave="viatura.placa_duplicada")
            await self._repositorio.salvar(viatura)
            await self._auditoria.registrar(
                RegistroAuditoria(quem=ator.id, quando=agora, operacao="viatura.cadastrar", entidade="Viatura", entidade_id=str(viatura.id), dados_depois={"prefixo": viatura.prefixo, "placa": viatura.placa}, ip=ator.ip)
            )
            await self._uow.commit()
        return para_output(viatura, agora, self._max_idade)


class AlterarSituacaoViatura(InterfaceAlterarSituacaoViatura):
    def __init__(self, repositorio: RepositorioViatura, uow: UnidadeDeTrabalho, relogio: Relogio, auditoria: PortaAuditoria, publicador: PublicadorEventos, max_idade: int) -> None:
        self._repositorio, self._uow, self._relogio, self._auditoria, self._publicador, self._max_idade = repositorio, uow, relogio, auditoria, publicador, max_idade

    async def executar(self, ator: Ator, input_dto: AlterarSituacaoInput) -> ViaturaOutput:
        ator.exigir_papel(*PAPEIS_GESTAO)
        agora = self._relogio.agora()
        if input_dto.situacao not in (SituacaoViatura.DISPONIVEL.value, SituacaoViatura.INDISPONIVEL.value):
            raise ValorInvalidoError("Só DISPONIVEL/INDISPONIVEL podem ser definidas manualmente.", chave="viatura.situacao_manual_invalida")
        async with self._uow:
            viatura = await carregar_viatura(self._repositorio, input_dto.viatura_id)
            antes = viatura.situacao.value
            if input_dto.situacao == SituacaoViatura.INDISPONIVEL.value:
                viatura.marcar_indisponivel(agora)
            else:
                viatura.marcar_disponivel(agora)
            await self._repositorio.salvar(viatura)
            await self._auditoria.registrar(
                RegistroAuditoria(quem=ator.id, quando=agora, operacao="viatura.alterar_situacao", entidade="Viatura", entidade_id=str(viatura.id), dados_antes={"situacao": antes}, dados_depois={"situacao": viatura.situacao.value}, ip=ator.ip)
            )
            await self._uow.commit()
        await self._publicador.publicar(viatura_situacao_alterada(viatura, agora))
        return para_output(viatura, agora, self._max_idade)


class ListarViaturas(InterfaceListarViaturas):
    def __init__(self, repositorio: RepositorioViatura, relogio: Relogio, max_idade: int) -> None:
        self._repositorio, self._relogio, self._max_idade = repositorio, relogio, max_idade

    async def executar(self, ator: Ator) -> tuple[ViaturaOutput, ...]:
        ator.exigir_papel(*PAPEIS_CONSULTA)
        agora = self._relogio.agora()
        return tuple(para_output(v, agora, self._max_idade) for v in await self._repositorio.listar())

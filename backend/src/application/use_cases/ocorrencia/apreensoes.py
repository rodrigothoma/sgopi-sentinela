"""
Casos de uso do inventário de apreensões (RF03 / UC03): registrar item, movimentar
custódia e emitir o Auto de Apreensão.

- Registro: só o Agente autor, com a ocorrência registrada ou em andamento; lacre
  único em toda a base (UC03 exceção I) — verificado via porta do repositório.
- Custódia: eventos append-only (quem, quando, de onde, para onde); Agente autor
  ou Delegado.
- Auto: documento com identificador único derivado do protocolo e hash SHA-256 do
  conteúdo (RNF03); a emissão é auditada.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from uuid import UUID

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_registrar_ocorrencia_policial import ItemApreendidoInputDTO
from application.ports.inbound.interface_gerir_apreensoes import (
    AutoApreensaoOutput,
    InterfaceEmitirAutoApreensao,
    InterfaceMovimentarCustodia,
    InterfaceRegistrarItemApreendido,
    ItemApreendidoOutput,
    MovimentarCustodiaInput,
    RegistrarItemApreendidoInput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.ocorrencia._mapeadores import para_item_apreendido
from application.use_cases.ocorrencia.consultar_ocorrencias import PAPEIS_CONSULTA, carregar_ou_404
from domain.auditoria.entity import RegistroAuditoria
from domain.ocorrencia.apreensao import EstadoConservacao, ItemApreendido, TipoItemApreendido, UnidadeMedida
from domain.ocorrencia.entity import Ocorrencia
from domain.shared.exceptions import AcessoNegadoError, ConflitoError, ValorInvalidoError
from domain.usuario.entity import Papel


def _enum[T](tipo: type[T], valor: str, chave: str) -> T:
    try:
        return tipo(valor)  # type: ignore[call-arg]
    except ValueError as exc:
        raise ValorInvalidoError(f"Valor inválido: {valor}", chave=chave, valor=valor) from exc


def _exigir_acesso_a_ocorrencia(ator: Ator, ocorrencia: Ocorrencia) -> None:
    """Agente só opera nas próprias ocorrências; os demais papéis autorizados enxergam todas."""
    if ator.papel == Papel.AGENTE and ocorrencia.agente_policial_id != ator.id:
        raise AcessoNegadoError("Somente o agente autor pode acessar esta ocorrência.", chave="ocorrencia.nao_e_autor")


def montar_item(dto: RegistrarItemApreendidoInput | ItemApreendidoInputDTO, *, agora: datetime, por_id: UUID) -> ItemApreendido:
    """DTO → entidade (valida enums e regras do item); compartilhado com o registro concomitante (RF01*)."""
    return ItemApreendido(
        tipo=_enum(TipoItemApreendido, dto.tipo, "apreensao.tipo_invalido"),
        descricao=dto.descricao,
        quantidade=dto.quantidade,
        unidade=_enum(UnidadeMedida, dto.unidade, "apreensao.unidade_invalida"),
        estado_conservacao=_enum(EstadoConservacao, dto.estado_conservacao, "apreensao.estado_invalido"),
        numero_lacre=dto.numero_lacre,
        numero_serie=dto.numero_serie,
        marca=dto.marca,
        calibre=dto.calibre,
        localizacao_deposito=dto.localizacao_deposito,
        registrado_em=agora,
        registrado_por_id=por_id,
    )


async def exigir_lacre_inedito(repositorio: RepositorioOcorrencia, item: ItemApreendido) -> None:
    """UC03 exceção I: o lacre é único em toda a base."""
    if await repositorio.lacre_em_uso(item.numero_lacre):
        raise ConflitoError(
            f"Lacre {item.numero_lacre} já cadastrado.", chave="apreensao.lacre_duplicado", numero_lacre=item.numero_lacre
        )


def auditoria_registro_item(ator: Ator, ocorrencia: Ocorrencia, item: ItemApreendido, agora: datetime) -> RegistroAuditoria:
    return RegistroAuditoria(
        quem=ator.id,
        quando=agora,
        operacao="apreensao.registrar",
        entidade="ItemApreendido",
        entidade_id=str(item.id),
        dados_depois={
            "ocorrencia_id": str(ocorrencia.id),
            "tipo": item.tipo.value,
            "numero_lacre": item.numero_lacre,
            "quantidade": item.quantidade,
            "unidade": item.unidade.value,
            "localizacao_deposito": item.localizacao_deposito,
        },
        ip=ator.ip,
    )


def numero_do_auto(numero_protocolo: str) -> str:
    """Identificador único do Auto de Apreensão: um por ocorrência, derivado do protocolo."""
    return f"AA-{numero_protocolo}"


class RegistrarItemApreendido(InterfaceRegistrarItemApreendido):
    def __init__(
        self, repositorio: RepositorioOcorrencia, uow: UnidadeDeTrabalho, relogio: Relogio, auditoria: PortaAuditoria
    ) -> None:
        self._repositorio = repositorio
        self._uow = uow
        self._relogio = relogio
        self._auditoria = auditoria

    async def executar(self, ator: Ator, input_dto: RegistrarItemApreendidoInput) -> ItemApreendidoOutput:
        ator.exigir_papel(Papel.AGENTE)
        agora = self._relogio.agora()
        item = montar_item(input_dto, agora=agora, por_id=ator.id)
        async with self._uow:
            ocorrencia = await carregar_ou_404(self._repositorio, input_dto.ocorrencia_id)
            ocorrencia.exigir_apreensao_permitida(ator.id)
            await exigir_lacre_inedito(self._repositorio, item)
            ocorrencia.registrar_apreensao(item, ator.id, agora)
            await self._repositorio.salvar(ocorrencia)
            await self._auditoria.registrar(auditoria_registro_item(ator, ocorrencia, item, agora))
            await self._uow.commit()
        return para_item_apreendido(item)


class MovimentarCustodia(InterfaceMovimentarCustodia):
    def __init__(
        self, repositorio: RepositorioOcorrencia, uow: UnidadeDeTrabalho, relogio: Relogio, auditoria: PortaAuditoria
    ) -> None:
        self._repositorio = repositorio
        self._uow = uow
        self._relogio = relogio
        self._auditoria = auditoria

    async def executar(self, ator: Ator, input_dto: MovimentarCustodiaInput) -> ItemApreendidoOutput:
        ator.exigir_papel(Papel.AGENTE, Papel.DELEGADO)
        agora = self._relogio.agora()
        async with self._uow:
            ocorrencia = await carregar_ou_404(self._repositorio, input_dto.ocorrencia_id)
            _exigir_acesso_a_ocorrencia(ator, ocorrencia)
            movimentacao = ocorrencia.movimentar_item_apreendido(
                input_dto.item_id, ator.id, input_dto.destino, input_dto.observacao, agora
            )
            await self._repositorio.salvar(ocorrencia)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="apreensao.movimentar",
                    entidade="ItemApreendido",
                    entidade_id=str(input_dto.item_id),
                    dados_antes={"localizacao": movimentacao.origem},
                    dados_depois={
                        "ocorrencia_id": str(ocorrencia.id),
                        "localizacao": movimentacao.destino,
                        "observacao": movimentacao.observacao,
                    },
                    ip=ator.ip,
                )
            )
            await self._uow.commit()
        return para_item_apreendido(ocorrencia.item_apreendido(input_dto.item_id))


class EmitirAutoApreensao(InterfaceEmitirAutoApreensao):
    def __init__(
        self, repositorio: RepositorioOcorrencia, uow: UnidadeDeTrabalho, relogio: Relogio, auditoria: PortaAuditoria
    ) -> None:
        self._repositorio = repositorio
        self._uow = uow
        self._relogio = relogio
        self._auditoria = auditoria

    @staticmethod
    def calcular_hash(numero: str, ocorrencia: Ocorrencia) -> str:
        """SHA-256 determinístico do conteúdo do auto (itens + cadeia de custódia)."""
        partes = [numero, ocorrencia.numero_protocolo, ocorrencia.natureza, ocorrencia.data_hora_fato.isoformat()]
        for item in sorted(ocorrencia.itens_apreendidos, key=lambda i: i.numero_lacre):
            partes.append(
                "|".join(
                    [
                        item.numero_lacre,
                        item.tipo.value,
                        item.descricao,
                        str(item.quantidade),
                        item.unidade.value,
                        item.estado_conservacao.value,
                        item.numero_serie or "",
                        item.marca or "",
                        item.calibre or "",
                    ]
                )
            )
            partes += [f"  {m.em.isoformat()}|{m.por_id}|{m.origem or ''}|{m.destino}" for m in item.movimentacoes]
        return hashlib.sha256("\n".join(partes).encode("utf-8")).hexdigest()

    async def executar(self, ator: Ator, ocorrencia_id: UUID) -> AutoApreensaoOutput:
        ator.exigir_papel(*PAPEIS_CONSULTA)
        agora = self._relogio.agora()
        async with self._uow:
            ocorrencia = await carregar_ou_404(self._repositorio, ocorrencia_id)
            _exigir_acesso_a_ocorrencia(ator, ocorrencia)
            if not ocorrencia.itens_apreendidos:
                raise ValorInvalidoError(
                    "A ocorrência não possui itens apreendidos.", chave="apreensao.sem_itens"
                )
            numero = numero_do_auto(ocorrencia.numero_protocolo)
            hash_ = self.calcular_hash(numero, ocorrencia)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="apreensao.emitir_auto",
                    entidade="AutoApreensao",
                    entidade_id=numero,
                    dados_depois={
                        "ocorrencia_id": str(ocorrencia.id),
                        "itens": len(ocorrencia.itens_apreendidos),
                        "hash_sha256": hash_,
                    },
                    ip=ator.ip,
                )
            )
            await self._uow.commit()
        return AutoApreensaoOutput(
            numero=numero,
            ocorrencia_id=ocorrencia.id,
            numero_protocolo=ocorrencia.numero_protocolo,
            natureza=ocorrencia.natureza,
            localizacao=ocorrencia.localizacao,
            data_hora_fato=ocorrencia.data_hora_fato.isoformat(),
            status=ocorrencia.status.value,
            agente_policial_id=ocorrencia.agente_policial_id,
            emitido_em=agora.isoformat(),
            emitido_por_id=ator.id,
            hash_sha256=hash_,
            itens=tuple(para_item_apreendido(i) for i in ocorrencia.itens_apreendidos),
        )

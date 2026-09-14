"""Caso de uso para validar, armazenar e vincular uma evidência digital (RF22)."""
from __future__ import annotations

import hashlib
from pathlib import PurePath

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_anexar_evidencia import (
    AnexarEvidenciaInput,
    EvidenciaOutput,
    InterfaceAnexarEvidencia,
)
from application.ports.outbound.armazenamento_arquivos import ArmazenamentoArquivos
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.ocorrencia.consultar_ocorrencias import carregar_ou_404
from domain.auditoria.entity import RegistroAuditoria
from domain.ocorrencia.entity import Evidencia
from domain.shared.exceptions import CampoObrigatorioError, ValorInvalidoError
from domain.usuario.entity import Papel

FORMATOS_MIME: dict[str, frozenset[str]] = {
    "pdf": frozenset({"application/pdf"}),
    "jpg": frozenset({"image/jpeg"}),
    "jpeg": frozenset({"image/jpeg"}),
    "png": frozenset({"image/png"}),
}


def _assinatura_valida(formato: str, conteudo: bytes) -> bool:
    if formato == "pdf":
        return conteudo.startswith(b"%PDF-")
    if formato in ("jpg", "jpeg"):
        return conteudo.startswith(b"\xff\xd8\xff")
    if formato == "png":
        return conteudo.startswith(b"\x89PNG\r\n\x1a\n")
    return False


class AnexarEvidencia(InterfaceAnexarEvidencia):
    def __init__(
        self,
        repositorio: RepositorioOcorrencia,
        armazenamento: ArmazenamentoArquivos,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        auditoria: PortaAuditoria,
        tamanho_maximo_bytes: int,
    ) -> None:
        self._repositorio = repositorio
        self._armazenamento = armazenamento
        self._uow = uow
        self._relogio = relogio
        self._auditoria = auditoria
        self._tamanho_maximo = tamanho_maximo_bytes

    def _validar(self, input_dto: AnexarEvidenciaInput) -> tuple[str, str]:
        nome = PurePath(input_dto.nome_arquivo or "").name.strip()
        if not nome:
            raise CampoObrigatorioError("Nome do arquivo é obrigatório.", chave="evidencia.nome_vazio")
        formato = PurePath(nome).suffix.lower().lstrip(".")
        mime = (input_dto.tipo_mime or "").split(";", 1)[0].strip().lower()
        if formato not in FORMATOS_MIME or mime not in FORMATOS_MIME[formato]:
            raise ValorInvalidoError(
                "Formato de evidência não permitido.",
                chave="evidencia.formato_invalido",
                permitidos=sorted(FORMATOS_MIME),
            )
        tamanho = len(input_dto.conteudo)
        if tamanho == 0:
            raise ValorInvalidoError("A evidência não pode estar vazia.", chave="evidencia.arquivo_vazio")
        if tamanho > self._tamanho_maximo:
            raise ValorInvalidoError(
                "A evidência excede o tamanho máximo.",
                chave="evidencia.tamanho_excedido",
                maximo_bytes=self._tamanho_maximo,
            )
        if not _assinatura_valida(formato, input_dto.conteudo):
            raise ValorInvalidoError("Conteúdo incompatível com o formato informado.", chave="evidencia.conteudo_invalido")
        return nome, formato

    async def executar(self, ator: Ator, input_dto: AnexarEvidenciaInput) -> EvidenciaOutput:
        ator.exigir_papel(Papel.AGENTE)
        nome, formato = self._validar(input_dto)
        agora = self._relogio.agora()
        async with self._uow:
            ocorrencia = await carregar_ou_404(self._repositorio, input_dto.ocorrencia_id)
            ocorrencia.exigir_anexo_permitido(ator.id)
            chave = await self._armazenamento.salvar(input_dto.conteudo, nome)
            evidencia = Evidencia(
                nome_original=nome,
                formato=formato,
                tamanho=len(input_dto.conteudo),
                hash_sha256=hashlib.sha256(input_dto.conteudo).hexdigest(),
                chave_armazenamento=chave,
                enviada_em=agora,
            )
            ocorrencia.adicionar_evidencia(evidencia, ator.id, agora)
            await self._repositorio.salvar(ocorrencia)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao="evidencia.anexar",
                    entidade="Evidencia",
                    entidade_id=str(evidencia.id),
                    dados_depois={
                        "ocorrencia_id": str(ocorrencia.id),
                        "nome_original": evidencia.nome_original,
                        "formato": evidencia.formato,
                        "tamanho": evidencia.tamanho,
                        "hash_sha256": evidencia.hash_sha256,
                    },
                    ip=ator.ip,
                )
            )
            await self._uow.commit()
        return EvidenciaOutput(
            id=evidencia.id,
            nome_original=evidencia.nome_original,
            formato=evidencia.formato,
            tamanho=evidencia.tamanho,
            hash_sha256=evidencia.hash_sha256,
            enviada_em=evidencia.enviada_em.isoformat(),
        )

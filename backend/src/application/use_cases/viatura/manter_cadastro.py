"""Manutenção de identificação da frota sem apagar referências de despachos (RF02/RNF03)."""
from datetime import datetime

from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_gerir_viaturas import (
    EditarViaturaInput,
    ExcluirViaturaInput,
    InterfaceEditarViatura,
    InterfaceExcluirViatura,
    ViaturaOutput,
)
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.viatura.gerir_viaturas import carregar_viatura, para_output
from domain.shared.eventos import EventoDominio
from domain.shared.exceptions import ConflitoError
from domain.usuario.permissoes import Permissao
from domain.viatura.auditoria import CadastroViaturaEditado, CadastroViaturaExcluido
from domain.viatura.entity import Viatura


def exigir_versao(viatura: Viatura, versao: int) -> None:
    """Recusa uma intenção baseada em cadastro que já mudou desde a leitura da tela."""
    if viatura.versao != versao:
        raise ConflitoError("A viatura foi alterada; recarregue a frota.", chave="generic.versao_desatualizada")


def dados_cadastro(viatura: Viatura) -> dict[str, str | bool | None]:
    """Snapshot auditável de identificação, responsável e retirada da frota."""
    return {"prefixo": viatura.prefixo, "placa": viatura.placa, "responsavel": viatura.responsavel, "ativo": viatura.ativo}


async def exigir_identificacao_unica(repositorio: RepositorioViatura, viatura: Viatura) -> None:
    """Permite manter a própria identificação, mas não reutilizar a de outro registro, inclusive excluído."""
    prefixo = await repositorio.buscar_por_prefixo(viatura.prefixo)
    placa = await repositorio.buscar_por_placa(viatura.placa)
    if prefixo is not None and prefixo.id != viatura.id:
        raise ConflitoError("Prefixo já cadastrado.", chave="viatura.prefixo_duplicado")
    if placa is not None and placa.id != viatura.id:
        raise ConflitoError("Placa já cadastrada.", chave="viatura.placa_duplicada")


class EditarViatura(InterfaceEditarViatura):
    """Edita o cadastro preservando a posição GPS, situação e identidade histórica."""

    def __init__(self, repositorio: RepositorioViatura, uow: UnidadeDeTrabalho, relogio: Relogio, auditoria: PortaAuditoria, publicador: PublicadorEventos, max_idade: int) -> None:
        self._repositorio, self._uow, self._relogio = repositorio, uow, relogio
        self._auditoria, self._publicador, self._max_idade = auditoria, publicador, max_idade

    async def executar(self, ator: Ator, input_dto: EditarViaturaInput) -> ViaturaOutput:
        """Versiona e audita a alteração; avisa os painéis somente depois do commit."""
        ator.exigir(Permissao.GERIR_FROTA)
        agora = self._relogio.agora()
        async with self._uow:
            viatura = await carregar_viatura(self._repositorio, input_dto.viatura_id)
            exigir_versao(viatura, input_dto.versao)
            antes = dados_cadastro(viatura)
            viatura.alterar_cadastro(input_dto.prefixo, input_dto.placa, input_dto.responsavel, agora)
            await exigir_identificacao_unica(self._repositorio, viatura)
            await self._repositorio.salvar(viatura)
            await self._auditoria.registrar(
                CadastroViaturaEditado.de(viatura, antes), ator.contexto_auditoria(agora)
            )
            await self._uow.commit()
        await self._publicador.publicar(_evento("ViaturaCadastroAlterado", viatura, agora))
        return para_output(viatura, agora, self._max_idade)


class ExcluirViatura(InterfaceExcluirViatura):
    """Exclui logicamente apenas viaturas sem atendimento ou ordem ativa."""

    def __init__(self, repositorio: RepositorioViatura, ordens: RepositorioOrdemDespacho, uow: UnidadeDeTrabalho, relogio: Relogio, auditoria: PortaAuditoria, publicador: PublicadorEventos) -> None:
        self._repositorio, self._ordens, self._uow = repositorio, ordens, uow
        self._relogio, self._auditoria, self._publicador = relogio, auditoria, publicador

    async def executar(self, ator: Ator, input_dto: ExcluirViaturaInput) -> None:
        """Preserva a linha e todos os vínculos para consulta histórica e auditoria."""
        ator.exigir(Permissao.GERIR_FROTA)
        agora = self._relogio.agora()
        async with self._uow:
            viatura = await carregar_viatura(self._repositorio, input_dto.viatura_id)
            exigir_versao(viatura, input_dto.versao)
            if await self._ordens.buscar_ativa_por_viatura(viatura.id):
                raise ConflitoError("Viatura com ordem ativa não pode ser excluída.", chave="viatura.exclusao_em_atendimento")
            antes = dados_cadastro(viatura)
            viatura.excluir(agora)
            await self._repositorio.salvar(viatura)
            await self._auditoria.registrar(
                CadastroViaturaExcluido.de(viatura, antes), ator.contexto_auditoria(agora)
            )
            await self._uow.commit()
        await self._publicador.publicar(_evento("ViaturaExcluida", viatura, agora))


def _evento(tipo: str, viatura: Viatura, agora: datetime) -> EventoDominio:
    """Só expõe o identificador; cada consumidor autorizado recarrega o cadastro pela API."""
    return EventoDominio(tipo=tipo, ocorrido_em=agora, dados={"viatura_id": str(viatura.id)})

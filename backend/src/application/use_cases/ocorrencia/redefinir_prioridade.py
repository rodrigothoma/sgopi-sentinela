"""Caso de uso: RedefinirPrioridade (sugestão #7) — o Delegado ajusta a gravidade, com justificativa auditada."""
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_consultar_ocorrencias import OcorrenciaDetalheOutput
from application.ports.inbound.interface_redefinir_prioridade import InterfaceRedefinirPrioridade, RedefinirPrioridadeInput
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from application.use_cases.ocorrencia._mapeadores import para_detalhe
from application.use_cases.ocorrencia.consultar_ocorrencias import carregar_ou_404
from domain.auditoria.entity import RegistroAuditoria
from domain.ocorrencia import eventos
from domain.ocorrencia.prioridade import interpretar_prioridade
from domain.shared.exceptions import CampoObrigatorioError
from domain.usuario.entity import Papel

OPERACAO = "ocorrencia.redefinir_prioridade"


class RedefinirPrioridade(InterfaceRedefinirPrioridade):
    def __init__(
        self,
        repositorio: RepositorioOcorrencia,
        uow: UnidadeDeTrabalho,
        relogio: Relogio,
        auditoria: PortaAuditoria,
        publicador: PublicadorEventos,
    ) -> None:
        self._repositorio = repositorio
        self._uow = uow
        self._relogio = relogio
        self._auditoria = auditoria
        self._publicador = publicador

    async def executar(self, ator: Ator, input_dto: RedefinirPrioridadeInput) -> OcorrenciaDetalheOutput:
        ator.exigir_papel(Papel.DELEGADO)
        nova = interpretar_prioridade(input_dto.prioridade)
        if nova is None:
            raise CampoObrigatorioError("Informe a nova prioridade.", chave="ocorrencia.prioridade_invalida")
        agora = self._relogio.agora()
        async with self._uow:
            ocorrencia = await carregar_ou_404(self._repositorio, input_dto.ocorrencia_id)
            versao_antes = ocorrencia.versao
            anterior = ocorrencia.redefinir_prioridade(nova, input_dto.justificativa, agora)
            await self._repositorio.salvar(ocorrencia)
            await self._auditoria.registrar(
                RegistroAuditoria(
                    quem=ator.id,
                    quando=agora,
                    operacao=OPERACAO,
                    entidade="Ocorrencia",
                    entidade_id=str(ocorrencia.id),
                    dados_antes={"prioridade": anterior.value, "versao": versao_antes},
                    dados_depois={
                        "prioridade": nova.value,
                        "versao": ocorrencia.versao,
                        "justificativa": input_dto.justificativa.strip(),
                    },
                    ip=ator.ip,
                )
            )
            await self._uow.commit()
        await self._publicador.publicar(
            eventos.ocorrencia_prioridade_alterada(ocorrencia.id, ocorrencia.status.value, agora, prioridade=nova.value)
        )
        return para_detalhe(ocorrencia, ator)

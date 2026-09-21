"""
Composition Root (HEX-02): único lugar que conhece portas E adapters.

Os routers dependem apenas das funções ``get_*`` daqui, tipadas pelas PORTAS.
Testes trocam ``get_session`` (SQLite em memória) ou qualquer ``get_*`` via
``app.dependency_overrides``.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from adapters.inbound.simulador.simulador_telemetria import SimuladorTelemetria
from adapters.inbound.websocket.gerenciador_conexoes import GerenciadorConexoes

from adapters.outbound.arquivos.armazenamento_disco import ArmazenamentoDisco
from adapters.outbound.eventos.publicador_em_memoria import PublicadorEventosEmMemoria
from adapters.outbound.persistence.auditoria_sqlalchemy import AuditoriaSQLAlchemy
from adapters.outbound.persistence.gerador_protocolo_sqlalchemy import GeradorProtocoloSQLAlchemy
from adapters.outbound.persistence.ocorrencia_repositorio_sqlalchemy import OcorrenciaRepositorioSQLAlchemy
from adapters.outbound.persistence.unidade_de_trabalho_sqlalchemy import UnidadeDeTrabalhoSQLAlchemy
from adapters.outbound.persistence.ordem_despacho_repositorio_sqlalchemy import (
    GeradorNumeroOrdemSQLAlchemy,
    OrdemDespachoRepositorioSQLAlchemy,
)
from adapters.outbound.persistence.usuario_repositorio_sqlalchemy import UsuarioRepositorioSQLAlchemy
from adapters.outbound.persistence.viatura_repositorio_sqlalchemy import ViaturaRepositorioSQLAlchemy
from adapters.outbound.relogio.relogio_sistema import RelogioSistema
from adapters.outbound.seguranca.hasher_argon2 import HasherArgon2
from adapters.outbound.seguranca.provedor_token_jose import ProvedorTokenJose
from application.ports.inbound.interface_autenticar_usuario import InterfaceAutenticarUsuario
from application.ports.inbound.interface_listar_usuarios import InterfaceListarUsuarios
from application.ports.inbound.interface_anexar_evidencia import InterfaceAnexarEvidencia
from application.ports.inbound.interface_acessar_evidencia import (
    InterfaceObterEvidenciaParaDownload,
    InterfaceVerificarIntegridadeEvidencia,
)
from application.ports.inbound.interface_arquivar_ocorrencia import (
    InterfaceArquivarOcorrencia,
    InterfaceExcluirOcorrencia,
)
from application.ports.inbound.interface_autenticar_documento import InterfaceAutenticarDocumento
from application.ports.inbound.interface_consultar_auditoria import InterfaceConsultarAuditoria
from application.ports.inbound.interface_gerir_apreensoes import (
    InterfaceEmitirAutoApreensao,
    InterfaceMovimentarCustodia,
    InterfaceRegistrarItemApreendido,
)
from application.ports.inbound.interface_despachar_viatura import (
    InterfaceDespacharViatura,
    InterfaceEncerrarOcorrencia,
    InterfaceListarOrdensDespacho,
    InterfaceSugerirViaturasProximas,
)
from application.ports.inbound.interface_gerir_viaturas import (
    InterfaceAlterarSituacaoViatura,
    InterfaceCadastrarViatura,
    InterfaceListarViaturas,
    InterfaceRegistrarPosicaoViatura,
)
from application.ports.inbound.interface_consultar_ocorrencias import (
    InterfaceListarOcorrencias,
    InterfaceObterDetalheOcorrencia,
)
from application.ports.inbound.interface_revisar_ocorrencia import (
    InterfaceCorrigirOcorrencia,
    InterfaceDevolverParaCorrecao,
    InterfaceReenviarOcorrencia,
    InterfaceRejeitarOcorrencia,
    InterfaceValidarOcorrencia,
)
from application.ports.inbound.interface_registrar_ocorrencia_policial import InterfaceRegistrarOcorrenciaPolicial
from application.ports.outbound.gerador_numero_ordem import GeradorNumeroOrdem
from application.ports.outbound.armazenamento_arquivos import ArmazenamentoArquivos
from application.ports.outbound.gerador_protocolo import GeradorProtocolo
from application.ports.outbound.hasher_senha import HasherSenha
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.provedor_token import ProvedorToken
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.ports.outbound.repositorio_ordem_despacho import RepositorioOrdemDespacho
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from application.ports.outbound.repositorio_viatura import RepositorioViatura
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.shared.geo import Coordenada
from application.use_cases.auditoria.consultar_auditoria import ConsultarAuditoria
from application.use_cases.auth.autenticar_usuario import AutenticarUsuario
from application.use_cases.documento.autenticar_documento import AutenticarDocumento
from application.use_cases.usuario.listar_usuarios import ListarUsuarios
from application.use_cases.ocorrencia.consultar_ocorrencias import ListarOcorrencias, ObterDetalheOcorrencia
from application.use_cases.ocorrencia.anexar_evidencia import AnexarEvidencia
from application.use_cases.ocorrencia.acessar_evidencia import (
    ObterEvidenciaParaDownload,
    VerificarIntegridadeEvidencia,
)
from application.use_cases.ocorrencia.apreensoes import EmitirAutoApreensao, MovimentarCustodia, RegistrarItemApreendido
from application.use_cases.ocorrencia.arquivar_ocorrencia import ArquivarOcorrencia, ExcluirOcorrencia
from application.use_cases.ocorrencia.corrigir_ocorrencia import CorrigirOcorrencia, ReenviarOcorrencia
from application.use_cases.despacho.despachar_viatura import DespacharViatura, ListarOrdensDespacho, SugerirViaturasProximas
from application.use_cases.despacho.encerrar_ocorrencia import EncerrarOcorrencia
from application.use_cases.viatura.gerir_viaturas import AlterarSituacaoViatura, CadastrarViatura, ListarViaturas
from application.use_cases.viatura.registrar_posicao_viatura import RegistrarPosicaoViatura
from application.use_cases.ocorrencia.revisar_ocorrencia import (
    DevolverParaCorrecao,
    RejeitarOcorrencia,
    ValidarOcorrencia,
)
from application.use_cases.ocorrencia.registrar_ocorrencia_policial import RegistrarOcorrenciaPolicial
from infrastructure.config.settings import settings
from infrastructure.database.connection import AsyncSessionLocal, get_session

# ----------------------------------------------------------------- singletons
publicador_eventos = PublicadorEventosEmMemoria()
relogio_sistema = RelogioSistema()
hasher_argon2 = HasherArgon2()
gerenciador_conexoes = GerenciadorConexoes()
publicador_eventos.assinar(gerenciador_conexoes.transmitir)  # RF17: fan-out para os painéis
provedor_token_jose = ProvedorTokenJose(settings.jwt_secret_key, settings.jwt_algorithm, settings.jwt_expires_in_hours)
armazenamento_evidencias = ArmazenamentoDisco(settings.evidencias_diretorio)


# ------------------------------------------------------------ portas de saída
def get_relogio() -> Relogio:
    return relogio_sistema


def get_publicador() -> PublicadorEventos:
    return publicador_eventos


def get_hasher() -> HasherSenha:
    return hasher_argon2


def get_provedor_token() -> ProvedorToken:
    return provedor_token_jose


def get_armazenamento_arquivos() -> ArmazenamentoArquivos:
    return armazenamento_evidencias


def get_repositorio_usuario(session: AsyncSession = Depends(get_session)) -> RepositorioUsuario:
    return UsuarioRepositorioSQLAlchemy(session)


def get_repositorio_viatura(session: AsyncSession = Depends(get_session)) -> RepositorioViatura:
    return ViaturaRepositorioSQLAlchemy(session)


def get_repositorio_ordem(session: AsyncSession = Depends(get_session)) -> RepositorioOrdemDespacho:
    return OrdemDespachoRepositorioSQLAlchemy(session)


def get_gerador_numero_ordem(session: AsyncSession = Depends(get_session)) -> GeradorNumeroOrdem:
    return GeradorNumeroOrdemSQLAlchemy(session)


def get_gerenciador_conexoes() -> GerenciadorConexoes:
    return gerenciador_conexoes


def get_uow(session: AsyncSession = Depends(get_session)) -> UnidadeDeTrabalho:
    return UnidadeDeTrabalhoSQLAlchemy(session)


def get_repositorio_ocorrencia(session: AsyncSession = Depends(get_session)) -> RepositorioOcorrencia:
    return OcorrenciaRepositorioSQLAlchemy(session)


def get_auditoria(session: AsyncSession = Depends(get_session)) -> PortaAuditoria:
    return AuditoriaSQLAlchemy(session)


def get_gerador_protocolo(session: AsyncSession = Depends(get_session)) -> GeradorProtocolo:
    return GeradorProtocoloSQLAlchemy(session)


# --------------------------------------------------------------- casos de uso
def get_registrar_ocorrencia(
    repositorio: RepositorioOcorrencia = Depends(get_repositorio_ocorrencia),
    uow: UnidadeDeTrabalho = Depends(get_uow),
    relogio: Relogio = Depends(get_relogio),
    gerador: GeradorProtocolo = Depends(get_gerador_protocolo),
    auditoria: PortaAuditoria = Depends(get_auditoria),
) -> InterfaceRegistrarOcorrenciaPolicial:
    return RegistrarOcorrenciaPolicial(repositorio, uow, relogio, gerador, auditoria)


def get_anexar_evidencia(
    repositorio: RepositorioOcorrencia = Depends(get_repositorio_ocorrencia),
    armazenamento: ArmazenamentoArquivos = Depends(get_armazenamento_arquivos),
    uow: UnidadeDeTrabalho = Depends(get_uow),
    relogio: Relogio = Depends(get_relogio),
    auditoria: PortaAuditoria = Depends(get_auditoria),
) -> InterfaceAnexarEvidencia:
    return AnexarEvidencia(
        repositorio,
        armazenamento,
        uow,
        relogio,
        auditoria,
        settings.evidencias_tamanho_maximo_bytes,
    )


def _deps_acesso_evidencia(
    repositorio: RepositorioOcorrencia = Depends(get_repositorio_ocorrencia),
    armazenamento: ArmazenamentoArquivos = Depends(get_armazenamento_arquivos),
    auditoria: PortaAuditoria = Depends(get_auditoria),
    uow: UnidadeDeTrabalho = Depends(get_uow),
    relogio: Relogio = Depends(get_relogio),
) -> tuple:
    return repositorio, armazenamento, auditoria, uow, relogio


def get_verificar_integridade_evidencia(
    deps: tuple = Depends(_deps_acesso_evidencia),
) -> InterfaceVerificarIntegridadeEvidencia:
    return VerificarIntegridadeEvidencia(*deps)


def get_obter_evidencia_para_download(
    deps: tuple = Depends(_deps_acesso_evidencia),
) -> InterfaceObterEvidenciaParaDownload:
    return ObterEvidenciaParaDownload(*deps)


def get_autenticar_usuario(
    repositorio: RepositorioUsuario = Depends(get_repositorio_usuario),
    hasher: HasherSenha = Depends(get_hasher),
    provedor: ProvedorToken = Depends(get_provedor_token),
    relogio: Relogio = Depends(get_relogio),
    auditoria: PortaAuditoria = Depends(get_auditoria),
    uow: UnidadeDeTrabalho = Depends(get_uow),
) -> InterfaceAutenticarUsuario:
    return AutenticarUsuario(repositorio, hasher, provedor, relogio, auditoria, uow)


def get_listar_usuarios(repositorio: RepositorioUsuario = Depends(get_repositorio_usuario)) -> InterfaceListarUsuarios:
    return ListarUsuarios(repositorio)


def get_listar_ocorrencias(repositorio: RepositorioOcorrencia = Depends(get_repositorio_ocorrencia)) -> InterfaceListarOcorrencias:
    return ListarOcorrencias(repositorio)


def get_obter_detalhe_ocorrencia(repositorio: RepositorioOcorrencia = Depends(get_repositorio_ocorrencia)) -> InterfaceObterDetalheOcorrencia:
    return ObterDetalheOcorrencia(repositorio)


def _deps_revisao(
    repositorio: RepositorioOcorrencia = Depends(get_repositorio_ocorrencia),
    uow: UnidadeDeTrabalho = Depends(get_uow),
    relogio: Relogio = Depends(get_relogio),
    auditoria: PortaAuditoria = Depends(get_auditoria),
    publicador: PublicadorEventos = Depends(get_publicador),
) -> tuple:
    return repositorio, uow, relogio, auditoria, publicador


def get_validar_ocorrencia(deps: tuple = Depends(_deps_revisao)) -> InterfaceValidarOcorrencia:
    return ValidarOcorrencia(*deps)


def get_devolver_para_correcao(deps: tuple = Depends(_deps_revisao)) -> InterfaceDevolverParaCorrecao:
    return DevolverParaCorrecao(*deps)


def get_rejeitar_ocorrencia(deps: tuple = Depends(_deps_revisao)) -> InterfaceRejeitarOcorrencia:
    return RejeitarOcorrencia(*deps)


def get_corrigir_ocorrencia(deps: tuple = Depends(_deps_revisao)) -> InterfaceCorrigirOcorrencia:
    repositorio, uow, relogio, auditoria, _ = deps
    return CorrigirOcorrencia(repositorio, uow, relogio, auditoria)


def get_reenviar_ocorrencia(deps: tuple = Depends(_deps_revisao)) -> InterfaceReenviarOcorrencia:
    return ReenviarOcorrencia(*deps)


def get_arquivar_ocorrencia(deps: tuple = Depends(_deps_revisao)) -> InterfaceArquivarOcorrencia:
    return ArquivarOcorrencia(*deps)


def get_excluir_ocorrencia(deps: tuple = Depends(_deps_revisao)) -> InterfaceExcluirOcorrencia:
    return ExcluirOcorrencia(*deps)


def get_consultar_auditoria(
    auditoria: PortaAuditoria = Depends(get_auditoria),
    repositorio_usuario: RepositorioUsuario = Depends(get_repositorio_usuario),
    repositorio_ocorrencia: RepositorioOcorrencia = Depends(get_repositorio_ocorrencia),
    repositorio_viatura: RepositorioViatura = Depends(get_repositorio_viatura),
) -> InterfaceConsultarAuditoria:
    return ConsultarAuditoria(
        auditoria=auditoria,
        repositorio_usuario=repositorio_usuario,
        repositorio_ocorrencia=repositorio_ocorrencia,
        repositorio_viatura=repositorio_viatura,
    )


# ----------------------------------------------------- documento público (RF08)
def get_autenticar_documento(deps: tuple = Depends(_deps_revisao)) -> InterfaceAutenticarDocumento:
    repositorio, uow, relogio, auditoria, _ = deps
    return AutenticarDocumento(repositorio, uow, relogio, auditoria)


# ---------------------------------------------------------------- apreensões (RF03)
def get_registrar_item_apreendido(deps: tuple = Depends(_deps_revisao)) -> InterfaceRegistrarItemApreendido:
    repositorio, uow, relogio, auditoria, _ = deps
    return RegistrarItemApreendido(repositorio, uow, relogio, auditoria)


def get_movimentar_custodia(deps: tuple = Depends(_deps_revisao)) -> InterfaceMovimentarCustodia:
    repositorio, uow, relogio, auditoria, _ = deps
    return MovimentarCustodia(repositorio, uow, relogio, auditoria)


def get_emitir_auto_apreensao(deps: tuple = Depends(_deps_revisao)) -> InterfaceEmitirAutoApreensao:
    repositorio, uow, relogio, auditoria, _ = deps
    return EmitirAutoApreensao(repositorio, uow, relogio, auditoria)


# ------------------------------------------------------------------ viaturas
def get_cadastrar_viatura(
    repositorio: RepositorioViatura = Depends(get_repositorio_viatura),
    uow: UnidadeDeTrabalho = Depends(get_uow),
    relogio: Relogio = Depends(get_relogio),
    auditoria: PortaAuditoria = Depends(get_auditoria),
) -> InterfaceCadastrarViatura:
    return CadastrarViatura(repositorio, uow, relogio, auditoria, settings.telemetria_max_idade_segundos)


def get_alterar_situacao_viatura(
    repositorio: RepositorioViatura = Depends(get_repositorio_viatura),
    uow: UnidadeDeTrabalho = Depends(get_uow),
    relogio: Relogio = Depends(get_relogio),
    auditoria: PortaAuditoria = Depends(get_auditoria),
    publicador: PublicadorEventos = Depends(get_publicador),
) -> InterfaceAlterarSituacaoViatura:
    return AlterarSituacaoViatura(repositorio, uow, relogio, auditoria, publicador, settings.telemetria_max_idade_segundos)


def get_listar_viaturas(
    repositorio: RepositorioViatura = Depends(get_repositorio_viatura), relogio: Relogio = Depends(get_relogio)
) -> InterfaceListarViaturas:
    return ListarViaturas(repositorio, relogio, settings.telemetria_max_idade_segundos)


def _registrar_posicao(session: AsyncSession, relogio: Relogio) -> RegistrarPosicaoViatura:
    """Telemetria (HTTP ou simulador) com detecção de chegada ao local da ocorrência (RF18/RF19)."""
    return RegistrarPosicaoViatura(
        ViaturaRepositorioSQLAlchemy(session),
        UnidadeDeTrabalhoSQLAlchemy(session),
        relogio,
        publicador_eventos,
        settings.telemetria_max_idade_segundos,
        ordens=OrdemDespachoRepositorioSQLAlchemy(session),
        ocorrencias=OcorrenciaRepositorioSQLAlchemy(session),
        auditoria=AuditoriaSQLAlchemy(session),
        raio_chegada_metros=settings.despacho_raio_chegada_metros,
    )


def get_registrar_posicao_viatura(
    session: AsyncSession = Depends(get_session), relogio: Relogio = Depends(get_relogio)
) -> InterfaceRegistrarPosicaoViatura:
    return _registrar_posicao(session, relogio)


# ----------------------------------------------------------------- simulador
def montar_simulador(session_factory: async_sessionmaker, relogio: Relogio | None = None, **kw) -> SimuladorTelemetria:
    """Monta o simulador com a fábrica de sessão informada (a suíte usa SQLite)."""
    relogio = relogio or relogio_sistema

    @asynccontextmanager
    async def contexto() -> AsyncIterator[tuple]:
        async with session_factory() as session:
            ordens = OrdemDespachoRepositorioSQLAlchemy(session)
            ocorrencias = OcorrenciaRepositorioSQLAlchemy(session)

            async def destino_de(viatura_id) -> Coordenada | None:
                ordem = await ordens.buscar_ativa_por_viatura(viatura_id)
                if ordem is None:
                    return None
                ocorrencia = await ocorrencias.buscar_por_id(ordem.ocorrencia_id)
                return ocorrencia.coordenada if ocorrencia else None

            yield ViaturaRepositorioSQLAlchemy(session), _registrar_posicao(session, relogio), destino_de

    return SimuladorTelemetria(
        contexto,
        relogio,
        intervalo_segundos=kw.get("intervalo_segundos", settings.simulador_intervalo_segundos),
        raio_metros=kw.get("raio_metros", settings.simulador_raio_metros),
        semente=kw.get("semente"),
        velocidade_kmh=kw.get("velocidade_kmh", settings.simulador_velocidade_kmh),
    )


simulador = montar_simulador(AsyncSessionLocal)


def get_simulador() -> SimuladorTelemetria:
    return simulador


# ------------------------------------------------------------------ despacho
def get_sugerir_viaturas(
    ocorrencias: RepositorioOcorrencia = Depends(get_repositorio_ocorrencia),
    viaturas: RepositorioViatura = Depends(get_repositorio_viatura),
    relogio: Relogio = Depends(get_relogio),
) -> InterfaceSugerirViaturasProximas:
    return SugerirViaturasProximas(ocorrencias, viaturas, relogio, settings.telemetria_max_idade_segundos, settings.despacho_qtd_sugestoes)


def get_despachar_viatura(
    ocorrencias: RepositorioOcorrencia = Depends(get_repositorio_ocorrencia),
    viaturas: RepositorioViatura = Depends(get_repositorio_viatura),
    ordens: RepositorioOrdemDespacho = Depends(get_repositorio_ordem),
    gerador: GeradorNumeroOrdem = Depends(get_gerador_numero_ordem),
    uow: UnidadeDeTrabalho = Depends(get_uow),
    relogio: Relogio = Depends(get_relogio),
    auditoria: PortaAuditoria = Depends(get_auditoria),
    publicador: PublicadorEventos = Depends(get_publicador),
) -> InterfaceDespacharViatura:
    return DespacharViatura(ocorrencias, viaturas, ordens, gerador, uow, relogio, auditoria, publicador)


def get_listar_ordens(ordens: RepositorioOrdemDespacho = Depends(get_repositorio_ordem)) -> InterfaceListarOrdensDespacho:
    return ListarOrdensDespacho(ordens)


def get_encerrar_ocorrencia(
    ocorrencias: RepositorioOcorrencia = Depends(get_repositorio_ocorrencia),
    viaturas: RepositorioViatura = Depends(get_repositorio_viatura),
    ordens: RepositorioOrdemDespacho = Depends(get_repositorio_ordem),
    uow: UnidadeDeTrabalho = Depends(get_uow),
    relogio: Relogio = Depends(get_relogio),
    auditoria: PortaAuditoria = Depends(get_auditoria),
    publicador: PublicadorEventos = Depends(get_publicador),
) -> InterfaceEncerrarOcorrencia:
    return EncerrarOcorrencia(ocorrencias, viaturas, ordens, uow, relogio, auditoria, publicador)

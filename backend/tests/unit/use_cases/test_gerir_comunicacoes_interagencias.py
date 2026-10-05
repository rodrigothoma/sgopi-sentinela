from datetime import datetime, timezone
from uuid import uuid4

import pytest

from application.ports.inbound.ator import Ator
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_comunicacao_interagencias import (
    GeradorNumeroOficio,
    RepositorioComunicacaoInteragencias,
)
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.use_cases.interagencias.gerir_comunicacoes import (
    ConsultarComunicacoesInteragenciasUseCase,
    EnviarComunicacaoInteragenciasUseCase,
    ResponderComunicacaoInteragenciasUseCase,
)
from domain.interagencias.entity import ComunicacaoInteragencias
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido
from domain.shared.geo import Coordenada
from domain.usuario.entity import Papel


class GeradorOficioFake(GeradorNumeroOficio):
    def __init__(self) -> None:
        self.seq = 0

    async def proximo_numero(self, ano: int) -> str:
        self.seq += 1
        return f"OFI-{ano}-{self.seq:06d}"


class RepoComFake(RepositorioComunicacaoInteragencias):
    def __init__(self) -> None:
        self.itens: dict[str, ComunicacaoInteragencias] = {}

    async def salvar(self, comunicacao: ComunicacaoInteragencias) -> ComunicacaoInteragencias:
        self.itens[str(comunicacao.id)] = comunicacao
        return comunicacao

    async def obter_por_id(self, comunicacao_id):
        return self.itens.get(str(comunicacao_id))

    async def listar(self, departamento=None, protocolo=None, remetente_id=None, limite=50):
        res = list(self.itens.values())
        if departamento:
            res = [c for c in res if c.departamento_origem == departamento or departamento in c.departamentos_destinatarios]
        if protocolo:
            res = [c for c in res if c.protocolo_ocorrencia == protocolo]
        return res[:limite]

    async def listar_respostas(self, mensagem_pai_id):
        return [c for c in self.itens.values() if c.mensagem_pai_id == mensagem_pai_id]


class RepoOcFake(RepositorioOcorrencia):
    def __init__(self) -> None:
        self.itens = {}

    async def salvar(self, oc):
        self.itens[oc.numero_protocolo] = oc

    async def buscar_por_id(self, oc_id):
        return None

    async def buscar_por_protocolo(self, numero_protocolo):
        return self.itens.get(numero_protocolo)

    async def buscar_por_chave_autenticidade(self, chave):
        return None

    async def buscar_por_hash_narrativa(self, hash_narrativa):
        return None

    async def listar(self, filtro):
        return list(self.itens.values())

    async def contar(self, filtro):
        return len(self.itens)

    async def lacre_em_uso(self, numero_lacre):
        return False


class RepoNotifFake(RepositorioNotificacao):
    def __init__(self) -> None:
        self.itens = []

    async def registrar_leitura(self, notificacao_id, usuario_id, instante):
        return None

    async def salvar(self, notificacao):
        self.itens.append(notificacao)
        return notificacao

    async def obter_por_id(self, notificacao_id):
        return None

    async def listar(self, **kwargs):
        return self.itens

    async def contar_nao_lidas(self, **kwargs):
        return len(self.itens)

    async def marcar_todas_lidas(self, usuario_id, papel, instante):
        return len(self.itens)


class AuditFake(PortaAuditoria):
    def __init__(self) -> None:
        self.registros = []

    async def registrar(self, reg):
        self.registros.append(reg)

    async def listar(self, **kwargs):
        return self.registros


class PubFake(PublicadorEventos):
    def __init__(self) -> None:
        self.eventos = []

    async def publicar(self, ev):
        self.eventos.append(ev)


class RelFixo(Relogio):
    def agora(self):
        return datetime(2026, 10, 3, 14, 0, 0, tzinfo=timezone.utc)


@pytest.mark.asyncio
async def test_fluxo_completo_comunicacao_interagencias():
    repo_com = RepoComFake()
    gerador = GeradorOficioFake()
    repo_oc = RepoOcFake()
    repo_notif = RepoNotifFake()
    porta_audit = AuditFake()
    pub = PubFake()
    rel = RelFixo()

    ator = Ator(id=uuid4(), papel=Papel.OPERADOR_CENTRAL, login="operador_santos")

    # Registra ocorrência de referência
    oc = Ocorrencia.registrar(
        numero_protocolo="2026-000555",
        agente_policial_id=ator.id,
        natureza="Acidente com Vítima",
        descricao="Acidente de trânsito em rodovia federal com vítimas.",
        localizacao="Rodovia BR-290, km 500, Alegrete",
        coordenada=Coordenada(latitude=-29.78, longitude=-55.79),
        data_hora_fato=rel.agora(),
        envolvidos=[Envolvido(nome="Condutor da Silva", tipo=TipoEnvolvido.VITIMA)],
        agora=rel.agora(),
    )
    await repo_oc.salvar(oc)

    uc_enviar = EnviarComunicacaoInteragenciasUseCase(
        repositorio_comunicacao=repo_com,
        gerador_oficio=gerador,
        repositorio_ocorrencia=repo_oc,
        repositorio_notificacao=repo_notif,
        porta_auditoria=porta_audit,
        publicador_eventos=pub,
        relogio=rel,
    )
    uc_consultar = ConsultarComunicacoesInteragenciasUseCase(repo_com)
    uc_responder = ResponderComunicacaoInteragenciasUseCase(
        repositorio_comunicacao=repo_com,
        gerador_oficio=gerador,
        repositorio_notificacao=repo_notif,
        porta_auditoria=porta_audit,
        publicador_eventos=pub,
        relogio=rel,
    )

    # 1. Enviar ofício inicial
    com1 = await uc_enviar.executar(
        ator=ator,
        departamento_origem="POLICIA_CIVIL",
        departamentos_destinatarios=["POLICIA_RODOVIARIA_FEDERAL"],
        assunto="Pedido de Relatório de Acidente de Trânsito",
        corpo="Solicita-se croqui e laudo preliminar do sinistro na BR-290.",
        protocolo_ocorrencia="2026-000555",
        nivel_sigilo="RESERVADO",
        prioridade="ALTA",
    )
    assert com1.numero_oficio == "OFI-2026-000001"
    assert len(porta_audit.registros) == 1
    assert porta_audit.registros[0].operacao == "ENVIO_COMUNICACAO_INTERAGENCIAS"
    assert len(repo_notif.itens) == 1
    assert repo_notif.itens[0].departamento_destinatario == "POLICIA_RODOVIARIA_FEDERAL"

    # 2. Consultar recebidas/enviadas
    lista_prf = await uc_consultar.executar(ator=ator, departamento="POLICIA_RODOVIARIA_FEDERAL")
    assert len(lista_prf) == 1
    assert lista_prf[0].numero_oficio == "OFI-2026-000001"

    # 3. Responder na thread
    resp = await uc_responder.executar(
        ator=Ator(id=uuid4(), papel=Papel.OPERADOR_CENTRAL, login="inspetor_prf"),
        mensagem_pai_id=com1.id,
        departamento_origem="POLICIA_RODOVIARIA_FEDERAL",
        assunto="Pedido de Relatório de Acidente de Trânsito",
        corpo="Informamos que a equipe prestou socorro e anexará o croqui pericial em breve.",
    )
    assert resp.numero_oficio == "OFI-2026-000002"
    assert resp.mensagem_pai_id == com1.id
    assert "POLICIA_CIVIL" in resp.departamentos_destinatarios
    assert len(porta_audit.registros) == 2
    assert porta_audit.registros[1].operacao == "RESPOSTA_COMUNICACAO_INTERAGENCIAS"

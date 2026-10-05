from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from application.ports.inbound.ator import Ator
from application.ports.outbound.porta_auditoria import PortaAuditoria
from application.ports.outbound.porta_notificacao_email import PortaNotificacaoEmail
from application.ports.outbound.publicador_eventos import PublicadorEventos
from application.ports.outbound.relogio import Relogio
from application.ports.outbound.repositorio_medida_protetiva import RepositorioMedidaProtetiva
from application.ports.outbound.repositorio_notificacao import RepositorioNotificacao
from application.ports.outbound.repositorio_ocorrencia import RepositorioOcorrencia
from application.use_cases.medida_protetiva.emitir_alerta_vencimento import EmitirAlertaVencimentoMedidaUseCase
from domain.medida_protetiva.entity import MedidaProtetiva
from domain.ocorrencia.entity import Envolvido, Ocorrencia, TipoEnvolvido
from domain.shared.geo import Coordenada
from domain.usuario.entity import Papel


class EmailFake(PortaNotificacaoEmail):
    def __init__(self) -> None:
        self.enviados = []

    async def enviar_email(self, para: str, assunto: str, corpo_html: str, corpo_texto: str) -> bool:
        self.enviados.append({"para": para, "assunto": assunto})
        return True


class AuditoriaFake(PortaAuditoria):
    def __init__(self) -> None:
        self.registros = []

    async def registrar(self, registro) -> None:
        self.registros.append(registro)

    async def listar(self, **kwargs):
        return self.registros


class PublicadorFake(PublicadorEventos):
    def __init__(self) -> None:
        self.eventos = []

    async def publicar(self, evento) -> None:
        self.eventos.append(evento)


class RelogioFixo(Relogio):
    def agora(self) -> datetime:
        return datetime(2026, 10, 3, 10, 0, 0, tzinfo=timezone.utc)


class RepoMedidaFake(RepositorioMedidaProtetiva):
    def __init__(self) -> None:
        self.itens: dict[str, MedidaProtetiva] = {}

    async def salvar(self, medida: MedidaProtetiva) -> None:
        self.itens[str(medida.id)] = medida

    async def buscar_por_id(self, medida_id):
        return self.itens.get(str(medida_id))

    async def buscar_por_referencia(self, numero_referencia):
        for m in self.itens.values():
            if m.numero_referencia == numero_referencia:
                return m
        return None

    async def listar(self, status=None, ocorrencia_id=None, limit=50, offset=0):
        res = list(self.itens.values())
        return res, len(res)


class RepoOcorrenciaFake(RepositorioOcorrencia):
    def __init__(self) -> None:
        self.itens: dict[str, Ocorrencia] = {}

    async def salvar(self, ocorrencia):
        self.itens[str(ocorrencia.id)] = ocorrencia

    async def buscar_por_id(self, ocorrencia_id):
        return self.itens.get(str(ocorrencia_id))

    async def buscar_por_protocolo(self, numero_protocolo):
        for o in self.itens.values():
            if o.numero_protocolo == numero_protocolo:
                return o
        return None

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


@pytest.mark.asyncio
async def test_emitir_alerta_vencimento_manual_com_email_vitima():
    rel = RelogioFixo()
    agora = rel.agora()
    hoje = agora.date()

    repo_medida = RepoMedidaFake()
    repo_ocorrencia = RepoOcorrenciaFake()
    repo_notif = RepoNotifFake()
    porta_email = EmailFake()
    porta_audit = AuditoriaFake()
    pub = PublicadorFake()

    ator = Ator(id=uuid4(), papel=Papel.DELEGADO, login="delegado_santos")

    # Cria vítima com e-mail
    vitima = Envolvido(nome="Maria da Silva", tipo=TipoEnvolvido.VITIMA, email="maria@exemplo.com")
    agressor = Envolvido(nome="João Infrator", tipo=TipoEnvolvido.SUSPEITO)
    oc = Ocorrencia.registrar(
        numero_protocolo="2026-000001",
        agente_policial_id=ator.id,
        natureza="Ameaça",
        descricao="Relato detalhado com mais de vinte caracteres.",
        localizacao="Rua das Flores, 100, Alegrete",
        coordenada=Coordenada(latitude=-29.78, longitude=-55.79),
        data_hora_fato=agora - timedelta(days=1),
        envolvidos=[vitima, agressor],
        agora=agora,
    )
    await repo_ocorrencia.salvar(oc)

    # Medida que vence em 2 dias (48h)
    medida = MedidaProtetiva.conceder(
        numero_referencia="MP-2026-000001",
        ocorrencia_id=oc.id,
        delegado_id=ator.id,
        vitima_id=vitima.id,
        agressor_id=agressor.id,
        tipos_restricao=["AFASTAMENTO_DO_LAR"],
        data_inicio=hoje - timedelta(days=28),
        prazo_dias=30,  # Vence em 2 dias
        instante=agora,
    )
    await repo_medida.salvar(medida)

    uc = EmitirAlertaVencimentoMedidaUseCase(
        repositorio_medida=repo_medida,
        repositorio_ocorrencia=repo_ocorrencia,
        repositorio_notificacao=repo_notif,
        porta_email=porta_email,
        porta_auditoria=porta_audit,
        publicador_eventos=pub,
        relogio=rel,
    )

    # 1. Executa alerta manual
    res = await uc.executar(ator=ator, medida_id=medida.id)
    assert res["sucesso"] is True
    assert res["alertas_enviados"] == 1
    assert len(porta_email.enviados) == 1
    assert porta_email.enviados[0]["para"] == "maria@exemplo.com"
    assert len(repo_notif.itens) == 1
    assert len(porta_audit.registros) == 1
    assert len(pub.eventos) == 1
    assert pub.eventos[0].tipo == "MEDIDA_VENCIMENTO_ALERTA"


@pytest.mark.asyncio
async def test_emitir_alerta_vencimento_automatico_lote():
    rel = RelogioFixo()
    agora = rel.agora()
    hoje = agora.date()

    repo_medida = RepoMedidaFake()
    repo_ocorrencia = RepoOcorrenciaFake()
    repo_notif = RepoNotifFake()
    porta_email = EmailFake()
    porta_audit = AuditoriaFake()
    pub = PublicadorFake()

    ator = Ator(id=uuid4(), papel=Papel.AGENTE, login="robo_agendador")

    # Medida 1: Vence em 2 dias -> deve gerar alerta
    m1 = MedidaProtetiva.conceder(
        numero_referencia="MP-2026-000001",
        ocorrencia_id=uuid4(),
        delegado_id=uuid4(),
        vitima_id=uuid4(),
        agressor_id=uuid4(),
        tipos_restricao=["AFASTAMENTO_DO_LAR"],
        data_inicio=hoje - timedelta(days=28),
        prazo_dias=30,
        instante=agora,
    )
    # Medida 2: Vence em 60 dias -> NÃO deve gerar alerta
    m2 = MedidaProtetiva.conceder(
        numero_referencia="MP-2026-000002",
        ocorrencia_id=uuid4(),
        delegado_id=uuid4(),
        vitima_id=uuid4(),
        agressor_id=uuid4(),
        tipos_restricao=["AFASTAMENTO_DO_LAR"],
        data_inicio=hoje,
        prazo_dias=60,
        instante=agora,
    )
    await repo_medida.salvar(m1)
    await repo_medida.salvar(m2)

    uc = EmitirAlertaVencimentoMedidaUseCase(
        repositorio_medida=repo_medida,
        repositorio_ocorrencia=repo_ocorrencia,
        repositorio_notificacao=repo_notif,
        porta_email=porta_email,
        porta_auditoria=porta_audit,
        publicador_eventos=pub,
        relogio=rel,
    )

    res = await uc.executar(ator=ator, medida_id=None)
    assert res["sucesso"] is True
    assert res["total_processadas"] == 2
    assert res["alertas_enviados"] == 1


def test_corpo_html_escapa_dados_do_cadastro():
    from types import SimpleNamespace

    from application.use_cases.medida_protetiva.emitir_alerta_vencimento import _corpo_html

    medida = SimpleNamespace(numero_referencia="MP-1", data_vencimento=date(2026, 10, 10), tipos_restricao=["<b>x</b>"])
    corpo = _corpo_html(medida, '<img src=x onerror="alert(1)">', "<script>", 2)
    assert "<img" not in corpo and "<script>" not in corpo and "&lt;img" in corpo


def test_destinatario_customizado_precisa_estar_cadastrado():
    from types import SimpleNamespace

    from application.use_cases.medida_protetiva.emitir_alerta_vencimento import _destinatario
    from domain.shared.exceptions import ValorInvalidoError

    ocorrencia = SimpleNamespace(envolvidos=[SimpleNamespace(email="Vitima@Exemplo.com")])
    assert _destinatario("vitima@exemplo.com", None, ocorrencia) == "vitima@exemplo.com"
    assert _destinatario(None, "vitima@exemplo.com", ocorrencia) == "vitima@exemplo.com"
    with pytest.raises(ValorInvalidoError):
        _destinatario("terceiro@fora.com", None, ocorrencia)

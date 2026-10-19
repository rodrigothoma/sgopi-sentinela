"""EnviadorEmailSMTP: STARTTLS com verificação de certificado e sem credenciais em claro."""
import ssl

from adapters.outbound.email import enviador_email_smtp as modulo
from adapters.outbound.email.enviador_email_smtp import EnviadorEmailSMTP, mascarar_email


class _SMTPFake:
    instancias: list["_SMTPFake"] = []

    def __init__(self, host, port, timeout):
        self.contexto, self.logins, self.enviados = None, [], []
        _SMTPFake.instancias.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self, context=None):
        self.contexto = context

    def login(self, usuario, senha):
        self.logins.append(usuario)

    def sendmail(self, de, para, msg):
        self.enviados.append(para)


async def test_starttls_usa_contexto_que_verifica_certificado(monkeypatch):
    monkeypatch.setattr(modulo.smtplib, "SMTP", _SMTPFake)
    enviador = EnviadorEmailSMTP(smtp_host="smtp.exemplo", smtp_usuario="u", smtp_senha="s", smtp_tls=True)
    assert await enviador.enviar_email("a@b.com", "Assunto", "<p>x</p>", "x")
    smtp = _SMTPFake.instancias[-1]
    assert isinstance(smtp.contexto, ssl.SSLContext)
    assert smtp.contexto.verify_mode == ssl.CERT_REQUIRED and smtp.contexto.check_hostname


async def test_credenciais_nao_trafegam_sem_tls(monkeypatch):
    _SMTPFake.instancias.clear()
    monkeypatch.setattr(modulo.smtplib, "SMTP", _SMTPFake)
    enviador = EnviadorEmailSMTP(smtp_host="smtp.exemplo", smtp_usuario="u", smtp_senha="s", smtp_tls=False)
    assert await enviador.enviar_email("a@b.com", "Assunto", "<p>x</p>", "x") is False
    assert _SMTPFake.instancias == []


async def test_historico_em_memoria_e_limitado():
    enviador = EnviadorEmailSMTP()
    for i in range(modulo.MAXIMO_HISTORICO_EM_MEMORIA + 5):
        await enviador.enviar_email(f"p{i}@b.com", "A", "<p>x</p>", "x")
    assert len(enviador.emails_enviados) == modulo.MAXIMO_HISTORICO_EM_MEMORIA


def test_mascara_email():
    assert mascarar_email("carlos.silva@exemplo.com") == "c***@exemplo.com"
    assert mascarar_email("invalido") == "***"

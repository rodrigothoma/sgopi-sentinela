"""
Adapter de saída: EnviadorEmailSMTP (RF09 / UC12).

Dispara e-mails institucionais via SMTP padrão ou modo em memória/mock quando não
configurado (ideal para desenvolvimento local e testes automatizados sem rede externa).
"""
from __future__ import annotations

import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib

from application.ports.outbound.porta_notificacao_email import PortaNotificacaoEmail

log = logging.getLogger("sgopi.email")


class EnviadorEmailSMTP(PortaNotificacaoEmail):
    def __init__(
        self,
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_usuario: str = "",
        smtp_senha: str = "",
        smtp_from: str = "sentinela@seguranca.gov.br",
        smtp_tls: bool = True,
    ) -> None:
        self.smtp_host = smtp_host.strip() if smtp_host else ""
        self.smtp_port = smtp_port
        self.smtp_usuario = smtp_usuario.strip() if smtp_usuario else ""
        self.smtp_senha = smtp_senha
        self.smtp_from = smtp_from.strip() if smtp_from else "sentinela@seguranca.gov.br"
        self.smtp_tls = smtp_tls
        self.emails_enviados: list[dict] = []

    async def enviar_email(self, para: str, assunto: str, corpo_html: str, corpo_texto: str) -> bool:
        registro = {
            "para": para,
            "assunto": assunto,
            "corpo_html": corpo_html,
            "corpo_texto": corpo_texto,
            "from": self.smtp_from,
        }
        self.emails_enviados.append(registro)

        # Se não há servidor SMTP configurado, registra no log estruturado e conclui com sucesso (modo seguro)
        if not self.smtp_host:
            log.info(
                "E-mail simulado com sucesso (modo local/mock): para=%s, assunto=%s",
                para,
                assunto,
                extra={"email": para, "assunto": assunto},
            )
            return True

        # Envio real em thread assíncrona
        return await asyncio.to_thread(self._enviar_smtp_sync, para, assunto, corpo_html, corpo_texto)

    def _enviar_smtp_sync(self, para: str, assunto: str, corpo_html: str, corpo_texto: str) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = assunto
            msg["From"] = self.smtp_from
            msg["To"] = para

            parte_txt = MIMEText(corpo_texto, "plain", "utf-8")
            parte_html = MIMEText(corpo_html, "html", "utf-8")
            msg.attach(parte_txt)
            msg.attach(parte_html)

            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as servidor:
                if self.smtp_tls:
                    servidor.starttls()
                if self.smtp_usuario and self.smtp_senha:
                    servidor.login(self.smtp_usuario, self.smtp_senha)
                servidor.sendmail(self.smtp_from, [para], msg.as_string())

            log.info("E-mail SMTP entregue com sucesso: para=%s", para)
            return True
        except Exception as e:
            log.error("Erro ao enviar e-mail via SMTP (%s:%d): %s", self.smtp_host, self.smtp_port, e)
            return False

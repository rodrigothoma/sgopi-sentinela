"""
Caso de uso: RegistrarOcorrenciaPublica (RF01 — Delegacia Online).

Aplica as regras do canal público (declaração de maioridade e conferência do CPF) e
qualifica o cidadão como COMUNICANTE; o registro em si é delegado ao caso de uso de RF01
pela sua porta de entrada (mesmas invariantes, auditoria e protocolo).

O autor técnico é o usuário de sistema CIDADAO (inativo, sem senha): a auditoria nunca aponta
um policial que não agiu, e nenhum agente pode corrigir a comunicação. O cidadão recebe um
código de acompanhamento secreto, exigido na consulta pública junto com o protocolo.
"""
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    EnvolvidoInputDTO,
    InterfaceRegistrarOcorrenciaPolicial,
    RegistrarOcorrenciaInput,
)
from application.ports.inbound.interface_registrar_ocorrencia_publica import (
    InterfaceRegistrarOcorrenciaPublica,
    RegistrarOcorrenciaPublicaInput,
    RegistrarOcorrenciaPublicaOutput,
)
from application.ports.outbound.repositorio_usuario import RepositorioUsuario
from application.ports.outbound.unidade_de_trabalho import UnidadeDeTrabalho
from domain.ocorrencia.comunicacao_publica import (
    gerar_codigo_acompanhamento,
    hash_codigo_acompanhamento,
    validar_comunicacao_publica,
)
from domain.ocorrencia.entity import OrigemOcorrencia, TipoEnvolvido
from domain.usuario.entity import LOGIN_SISTEMA_CIDADAO, Usuario


class RegistrarOcorrenciaPublica(InterfaceRegistrarOcorrenciaPublica):
    def __init__(
        self,
        registrar_ocorrencia: InterfaceRegistrarOcorrenciaPolicial,
        usuarios: RepositorioUsuario,
        uow: UnidadeDeTrabalho,
    ) -> None:
        self._registrar_ocorrencia = registrar_ocorrencia
        self._usuarios = usuarios
        self._uow = uow

    async def executar(self, input_dto: RegistrarOcorrenciaPublicaInput) -> RegistrarOcorrenciaPublicaOutput:
        validar_comunicacao_publica(input_dto.documento, input_dto.declaracao_maioridade)
        ator = await self._ator_sistema(input_dto.ip)
        codigo = gerar_codigo_acompanhamento()
        out = await self._registrar_ocorrencia.executar(ator, self._registro(input_dto, codigo))
        return RegistrarOcorrenciaPublicaOutput(
            ocorrencia_id=out.ocorrencia_id,
            numero_protocolo=out.numero_protocolo,
            status=out.status,
            criada_em=out.criada_em,
            codigo_acompanhamento=codigo,
        )

    async def _ator_sistema(self, ip: str | None) -> Ator:
        """Usuário de sistema criado pela migração 0013; criado aqui se a base não o tiver (ex.: testes)."""
        usuario = await self._usuarios.buscar_por_login(LOGIN_SISTEMA_CIDADAO)
        if usuario is None:
            usuario = Usuario.sistema_cidadao()
            async with self._uow:
                await self._usuarios.salvar(usuario)
                await self._uow.commit()
        return Ator(id=usuario.id, login=usuario.login, papel=usuario.papel, ip=ip)

    @staticmethod
    def _registro(input_dto: RegistrarOcorrenciaPublicaInput, codigo: str) -> RegistrarOcorrenciaInput:
        comunicante = EnvolvidoInputDTO(
            nome=input_dto.nome_solicitante.strip(),
            tipo=TipoEnvolvido.COMUNICANTE.value,
            documento=input_dto.documento.strip(),
            email=input_dto.email.strip(),
            telefone=input_dto.telefone.strip(),
        )
        return RegistrarOcorrenciaInput(
            natureza=input_dto.natureza,
            descricao=input_dto.descricao.strip(),
            localizacao=input_dto.localizacao,
            latitude=input_dto.latitude,
            longitude=input_dto.longitude,
            data_hora_fato=input_dto.data_hora_fato,
            envolvidos=(comunicante,),
            origem=OrigemOcorrencia.PUBLICA,
            codigo_acompanhamento_hash=hash_codigo_acompanhamento(codigo),
        )

"""
Caso de uso: RegistrarOcorrenciaPublica (RF01 — Delegacia Online).

Aplica as regras do canal público (declaração de maioridade e conferência do CPF) e
qualifica o cidadão como COMUNICANTE; o registro em si é delegado ao caso de uso de RF01
pela sua porta de entrada (mesmas invariantes, auditoria e protocolo).
"""
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_registrar_ocorrencia_policial import (
    EnvolvidoInputDTO,
    InterfaceRegistrarOcorrenciaPolicial,
    RegistrarOcorrenciaInput,
    RegistrarOcorrenciaOutput,
)
from application.ports.inbound.interface_registrar_ocorrencia_publica import (
    InterfaceRegistrarOcorrenciaPublica,
    RegistrarOcorrenciaPublicaInput,
)
from domain.ocorrencia.comunicacao_publica import validar_comunicacao_publica
from domain.ocorrencia.entity import TipoEnvolvido


class RegistrarOcorrenciaPublica(InterfaceRegistrarOcorrenciaPublica):
    def __init__(self, registrar_ocorrencia: InterfaceRegistrarOcorrenciaPolicial) -> None:
        self._registrar_ocorrencia = registrar_ocorrencia

    async def executar(self, ator: Ator, input_dto: RegistrarOcorrenciaPublicaInput) -> RegistrarOcorrenciaOutput:
        validar_comunicacao_publica(input_dto.documento, input_dto.declaracao_maioridade)
        comunicante = EnvolvidoInputDTO(
            nome=input_dto.nome_solicitante.strip(),
            tipo=TipoEnvolvido.COMUNICANTE.value,
            documento=input_dto.documento.strip(),
            email=input_dto.email.strip(),
            telefone=input_dto.telefone.strip(),
        )
        return await self._registrar_ocorrencia.executar(
            ator,
            RegistrarOcorrenciaInput(
                natureza=input_dto.natureza,
                descricao=input_dto.descricao.strip(),
                localizacao=input_dto.localizacao,
                latitude=input_dto.latitude,
                longitude=input_dto.longitude,
                data_hora_fato=input_dto.data_hora_fato,
                envolvidos=(comunicante,),
            ),
        )

"""Mappers de persistência: mapeamento entre entidades de domínio e modelos ORM SQLAlchemy."""
from adapters.outbound.persistence.mappers.comunicacao_interagencias_mapper import ComunicacaoInteragenciasMapper
from adapters.outbound.persistence.mappers.inquerito_mapper import InqueritoMapper
from adapters.outbound.persistence.mappers.laudo_mapper import LaudoMapper
from adapters.outbound.persistence.mappers.medida_protetiva_mapper import MedidaProtetivaMapper
from adapters.outbound.persistence.mappers.notificacao_mapper import NotificacaoMapper
from adapters.outbound.persistence.mappers.ocorrencia_mapper import OcorrenciaMapper
from adapters.outbound.persistence.mappers.ordem_despacho_mapper import OrdemDespachoMapper
from adapters.outbound.persistence.mappers.usuario_mapper import UsuarioMapper
from adapters.outbound.persistence.mappers.viatura_mapper import ViaturaMapper

__all__ = [
    "ComunicacaoInteragenciasMapper",
    "InqueritoMapper",
    "LaudoMapper",
    "MedidaProtetivaMapper",
    "NotificacaoMapper",
    "OcorrenciaMapper",
    "OrdemDespachoMapper",
    "UsuarioMapper",
    "ViaturaMapper",
]

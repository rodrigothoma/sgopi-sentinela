"""Mappers de persistência: mapeamento entre entidades de domínio e modelos ORM SQLAlchemy."""
from adapters.outbound.persistence.mappers.ocorrencia_mapper import OcorrenciaMapper
from adapters.outbound.persistence.mappers.viatura_mapper import ViaturaMapper

__all__ = ["OcorrenciaMapper", "ViaturaMapper"]

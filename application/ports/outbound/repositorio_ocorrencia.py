"""
Porta de saída: RepositorioOcorrencia

Interface abstrata (contrato). Quem implementa de fato com SQLAlchemy
fica em adapters/outbound/persistence/ocorrencia_dao.py. O caso de uso
só conhece esta interface, nunca o banco de dados diretamente.
"""

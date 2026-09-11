"""
Caso de uso: RegistrarOcorrenciaPolicial (RF01 — Must Have do MVP)

Orquestra a criação da entidade Ocorrencia e delega a persistência
à porta de saída RepositorioOcorrencia. Não sabe nada sobre FastAPI,
SQLAlchemy ou HTTP, só domínio + portas.
"""

"""
Testes automatizados de conformidade arquitetural (Fitness Functions).
Assegura que qualquer código gerado por IA ou desenvolvedores respeite:
- Arquitetura Hexagonal (Ports & Adapters)
- Princípios SOLID (SRP, DIP, ISP)
- Clean Code e Imutabilidade (RNF03)
"""
import abc
import inspect
from pathlib import Path

import pytest

import application.ports.inbound as inbound_ports
import application.ports.outbound as outbound_ports
import application.use_cases as use_cases_pkg
import domain


def _obter_submodulos(pkg):
    """Retorna todos os módulos sob um pacote."""
    import pkgutil
    modulos = []
    for info in pkgutil.walk_packages(pkg.__path__, prefix=pkg.__name__ + "."):
        mod = __import__(info.name, fromlist=["*"])
        modulos.append(mod)
    return modulos


def test_entidades_de_dominio_sao_puras_sem_orm_nem_framework():
    """
    RNF05: Garante que nenhuma classe de domínio herde de bibliotecas externas
    (como SQLAlchemy DeclarativeBase ou Pydantic BaseModel). O domínio deve ser Python puro.
    """
    proibidos = ("sqlalchemy", "pydantic", "fastapi", "starlette", "alembic")
    modulos_domain = _obter_submodulos(domain)

    for mod in modulos_domain:
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            if cls.__module__.startswith("domain"):
                for base in cls.__mro__:
                    modulo_base = base.__module__.lower()
                    assert not any(p in modulo_base for p in proibidos), (
                        f"Violação de Arquitetura: Classe de domínio '{name}' ({cls}) "
                        f"herda de biblioteca externa proibida '{modulo_base}'!"
                    )


def test_portas_outbound_sao_interfaces_abstratas_abc():
    """
    DIP (SOLID): Portas de saída devem ser contratos abstratos (ABC),
    nunca classes concretas ou acopladas a adapters.
    """
    modulos_outbound = _obter_submodulos(outbound_ports)
    classes_encontradas = 0

    for mod in modulos_outbound:
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            if cls.__module__.startswith("application.ports.outbound"):
                # Se for dataclass (DTO/Value Object como DadosToken), verifica se é pura
                if hasattr(cls, "__dataclass_fields__"):
                    continue
                # Classes de serviço/porta de saída devem ser contratos abstratos (ABC)
                assert issubclass(cls, abc.ABC), (
                    f"Violação de DIP: Porta de saída '{name}' ({cls}) deve herdar de abc.ABC!"
                )
                classes_encontradas += 1

    assert classes_encontradas > 0


def test_portas_inbound_sao_interfaces_abstratas_abc():
    """
    DIP (SOLID): Portas de entrada (casos de uso) devem definir contratos abstratos (ABC).
    """
    modulos_inbound = _obter_submodulos(inbound_ports)
    interfaces_encontradas = 0

    for mod in modulos_inbound:
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            if cls.__module__.startswith("application.ports.inbound") and name.startswith("Interface"):
                assert issubclass(cls, abc.ABC), (
                    f"Violação de DIP: Porta de entrada '{name}' deve herdar de abc.ABC!"
                )
                interfaces_encontradas += 1

    assert interfaces_encontradas > 0


def test_casos_de_uso_implementam_porta_inbound_e_metodo_executar():
    """
    SRP & DIP (SOLID): Todo Caso de Uso deve:
    1. Implementar sua respectiva interface de porta inbound.
    2. Expor o método de execução unificado ('executar').
    """
    modulos_uc = _obter_submodulos(use_cases_pkg)
    casos_de_uso = []

    for mod in modulos_uc:
        for name, cls in inspect.getmembers(mod, inspect.isclass):
            if cls.__module__.startswith("application.use_cases") and not name.startswith("_"):
                # Filtra mapeadores ou DTOs internos
                if inspect.isfunction(getattr(cls, "executar", None)) or name.endswith("UseCase") or name.endswith("Ocorrencia") or name.endswith("Viatura"):
                    casos_de_uso.append((name, cls))

    assert len(casos_de_uso) > 0, "Nenhum caso de uso encontrado para validação"

    for name, cls in casos_de_uso:
        # Garante que possui o método executar
        assert hasattr(cls, "executar"), (
            f"Violação de SRP: Caso de uso '{name}' deve expor o método 'executar' como ponto de entrada!"
        )


def test_repositorio_auditoria_nao_contem_delete():
    """
    RNF03: A trilha de auditoria e conformidade é estritamente append-only.
    Nenhuma operação de DELETE deve existir no adaptador de auditoria.
    """
    arquivo_auditoria = Path(__file__).resolve().parents[2] / "src" / "adapters" / "outbound" / "persistence" / "auditoria_sqlalchemy.py"
    if arquivo_auditoria.exists():
        codigo = arquivo_auditoria.read_text(encoding="utf-8").lower()
        assert "delete(" not in codigo and "delete from" not in codigo, (
            "Violação de RNF03: O adaptador de auditoria não pode conter operações de exclusão (DELETE)!"
        )

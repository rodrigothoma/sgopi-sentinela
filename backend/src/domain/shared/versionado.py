"""
Mixin de controle otimista de concorrência (RNF03) para entidades persistidas com ``versao``.

Toda mutação de estado chama ``_tocar(instante)``: incrementa a versão (verificada pelo
repositório ao salvar) e registra o instante da alteração. É um mixin de comportamento,
não uma classe base com campos: cada entidade declara ``versao`` e o campo de atualização
na própria dataclass, o que preserva a ordem dos campos com e sem valor padrão.
"""
from __future__ import annotations

from datetime import datetime
from typing import ClassVar


class Versionado:
    # Nome do campo de atualização na entidade (inquérito e laudo usam o masculino,
    # como as colunas ``atualizado_em`` das suas tabelas).
    CAMPO_ATUALIZACAO: ClassVar[str] = "atualizada_em"

    versao: int

    def _tocar(self, instante: datetime) -> None:
        self.versao += 1
        setattr(self, self.CAMPO_ATUALIZACAO, instante)

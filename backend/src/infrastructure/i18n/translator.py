"""
Helper de internacionalização do backend.
Carrega o default.json do idioma solicitado e resolve chaves no formato 'entidade.chave'.
"""
import json
from pathlib import Path

_LOCALES_DIR = Path(__file__).parent / "locales"
_cache: dict[str, dict] = {}


def get_message(key: str, lang: str = "pt") -> str:
    """
    Resolve uma mensagem pelo caminho de chave (ex: 'ocorrencia.created').
    Usa o idioma solicitado com fallback para 'pt'.
    """
    for lng in (lang, "pt"):
        if lng not in _cache:
            path = _LOCALES_DIR / lng / "default.json"
            if path.exists():
                _cache[lng] = json.loads(path.read_text(encoding="utf-8"))
        node = _cache.get(lng, {})
        for k in key.split("."):
            node = node.get(k, {}) if isinstance(node, dict) else {}
        if isinstance(node, str):
            return node
    return key

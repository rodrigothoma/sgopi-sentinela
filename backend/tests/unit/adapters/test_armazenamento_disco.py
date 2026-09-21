"""Leitura segura do adapter local de evidências."""
import pytest

from adapters.outbound.arquivos.armazenamento_disco import ArmazenamentoDisco


async def test_salva_e_le_preservando_bytes(tmp_path):
    armazenamento = ArmazenamentoDisco(tmp_path)
    conteudo = b"\x00%PDF-1.7\xff\nbytes"
    chave = await armazenamento.salvar(conteudo, "laudo.pdf")
    assert await armazenamento.ler(chave) == conteudo


async def test_arquivo_ausente(tmp_path):
    assert await ArmazenamentoDisco(tmp_path).ler("ausente.pdf") is None


async def test_rejeita_caminho_absoluto(tmp_path):
    externo = tmp_path.parent / "segredo.pdf"
    externo.write_bytes(b"segredo")
    assert await ArmazenamentoDisco(tmp_path).ler(str(externo.resolve())) is None


async def test_rejeita_path_traversal(tmp_path):
    externo = tmp_path.parent / "segredo.pdf"
    externo.write_bytes(b"segredo")
    assert await ArmazenamentoDisco(tmp_path).ler("../segredo.pdf") is None


async def test_rejeita_symlink_apontando_para_fora_da_raiz(tmp_path):
    externo = tmp_path.parent / f"{tmp_path.name}-externo.pdf"
    externo.write_bytes(b"segredo")
    link = tmp_path / "atalho.pdf"
    try:
        link.symlink_to(externo)
    except (NotImplementedError, OSError) as exc:
        pytest.skip(f"Criação de symlink indisponível neste ambiente: {exc}")

    assert await ArmazenamentoDisco(tmp_path).ler(link.name) is None

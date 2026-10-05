"""Adapter de entrada: evidências digitais da ocorrência — anexo, conferência e download (RF01 / RF22)."""
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from adapters.inbound.http.deps import exigir_papel
from adapters.inbound.http.v1.ocorrencias_router import PAPEIS_CONSULTA, EvidenciaSchema, IntegridadeEvidenciaSchema
from application.ports.inbound.ator import Ator
from application.ports.inbound.interface_acessar_evidencia import (
    InterfaceObterEvidenciaParaDownload,
    InterfaceVerificarIntegridadeEvidencia,
)
from application.ports.inbound.interface_anexar_evidencia import AnexarEvidenciaInput, InterfaceAnexarEvidencia
from domain.usuario.entity import Papel
from infrastructure.config.settings import settings
from infrastructure.di import get_anexar_evidencia, get_obter_evidencia_para_download, get_verificar_integridade_evidencia

router = APIRouter(prefix="/v1/ocorrencias", tags=["ocorrencias"])

MIME_EVIDENCIA = {
    "pdf": "application/pdf",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}



@router.post("/{ocorrencia_id}/evidencias", response_model=EvidenciaSchema, status_code=201)
async def anexar_evidencia(
    ocorrencia_id: UUID,
    arquivo: UploadFile = File(...),
    ator: Ator = Depends(exigir_papel(Papel.AGENTE)),
    use_case: InterfaceAnexarEvidencia = Depends(get_anexar_evidencia),
) -> EvidenciaSchema:
    """Anexa PDF/JPEG/PNG de até 10 MB à ocorrência do agente autor (RF01)."""
    try:
        conteudo = await arquivo.read(settings.evidencias_tamanho_maximo_bytes + 1)
    finally:
        await arquivo.close()
    out = await use_case.executar(
        ator,
        AnexarEvidenciaInput(
            ocorrencia_id=ocorrencia_id,
            nome_arquivo=arquivo.filename or "",
            tipo_mime=arquivo.content_type or "",
            conteudo=conteudo,
        ),
    )
    return EvidenciaSchema(**out.__dict__)



@router.get(
    "/{ocorrencia_id}/evidencias/{evidencia_id}/integridade",
    response_model=IntegridadeEvidenciaSchema,
)
async def verificar_integridade_evidencia(
    ocorrencia_id: UUID,
    evidencia_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceVerificarIntegridadeEvidencia = Depends(get_verificar_integridade_evidencia),
) -> IntegridadeEvidenciaSchema:
    """Confere o SHA-256 do arquivo armazenado contra o hash registrado (RF22)."""
    out = await use_case.executar(ator, ocorrencia_id, evidencia_id)
    return IntegridadeEvidenciaSchema(**{**out.__dict__, "verificado_em": out.verificado_em.isoformat()})


@router.get("/{ocorrencia_id}/evidencias/{evidencia_id}/download")
async def download_evidencia(
    ocorrencia_id: UUID,
    evidencia_id: UUID,
    ator: Ator = Depends(exigir_papel(*PAPEIS_CONSULTA)),
    use_case: InterfaceObterEvidenciaParaDownload = Depends(get_obter_evidencia_para_download),
) -> Response:
    """Download autorizado da evidência; bloqueado (409) se a integridade divergir (RF22)."""
    out = await use_case.executar(ator, ocorrencia_id, evidencia_id)
    nome_codificado = quote(out.nome_original, safe="")
    return Response(
        content=out.conteudo,
        media_type=MIME_EVIDENCIA[out.formato],
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{nome_codificado}",
            "Content-Length": str(len(out.conteudo)),
            "X-Content-Type-Options": "nosniff",
        },
    )

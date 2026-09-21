# ETAPA 10 — Autenticação pública de documento (RF08 / UC08)

**Data:** 14/09/2026 · **Prioridade:** 🟡 (*Could Have* na matriz MoSCoW — primeira fatia fora do Must do MVP) · **Autor da fatia:** Mateus Estivalet Valau

**Origem:** `DOCUMENTACAO_DE_ENGENHARIA.md` §1.1 RF08, §2 (Could Have), §6 UC08 (cenário principal, regras 1–2, exceções I–II); DEC-09 (hash SHA-256 da narrativa — a Etapa 4 já registrava "base para RF08"); RNF02 (ocultar dados sensíveis na consulta pública); RNF03 (auditoria imutável); RNF10 (LGPD).

## 1. Objetivo

Permitir que um cidadão, advogado ou órgão externo confira, **sem login**, se um Boletim de Ocorrência é autêntico e íntegro, usando a chave de segurança impressa no documento ou lida por QR Code — sem que o portal exponha qualquer dado pessoal.

É uma fatia vertical completa (princípio 01 do `PLANEJAMENTO_DESENVOLVIMENTO.md`): domínio → porta → caso de uso → adapter HTTP → migração → frontend → testes → este documento.

## 2. O que foi implementado

| Item | Arquivo | Requisito |
| :--- | :--- | :--- |
| Chave de autenticidade de **24 caracteres** em alfabeto sem ambiguidade (`0/O/1/I` excluídos), `normalizar_chave` (aceita hífens/minúsculas), `formatar_chave` (`XXXX-XXXX-…`), enum `SituacaoDocumento` (`VALIDO` / `ADULTERADO`) | `domain/ocorrencia/autenticidade.py` | UC08 passo 2, regra 1 |
| `Ocorrencia.validar()` passa a **emitir o documento**: gera `chave_autenticidade` junto com o `hash_narrativa`; `situacao_documento()` compara o hash atual com o congelado na validação; `emitida_em()` | `domain/ocorrencia/entity.py` | UC08 passo 5, DEC-09 |
| Porta de saída `RepositorioOcorrencia.buscar_por_chave_autenticidade` | `application/ports/outbound/repositorio_ocorrencia.py` | UC08 passo 4 |
| Porta de entrada `InterfaceAutenticarDocumento` + DTOs (`AutenticarDocumentoInput` com `ip`, `DocumentoAutenticadoOutput`) — **única porta do sistema sem `Ator`** | `application/ports/inbound/interface_autenticar_documento.py` | UC08 regra 1 |
| Caso de uso `AutenticarDocumento`: normaliza → localiza → confere integridade → **audita a consulta como anônima** (`quem=None`, IP do consulente) → devolve o espelho de conferência. Documento adulterado gera operação `documento.suspeita_fraude` | `application/use_cases/documento/autenticar_documento.py` | UC08 passos 4–8, Exceção II, RNF03 |
| Chave formatada exposta no detalhe interno da ocorrência (`chave_autenticidade`) para quem já pode ver o detalhe | `interface_consultar_ocorrencias.py`, `_mapeadores.py`, `ocorrencias_router.py` | UC08 pré-condição |
| Coluna `ocorrencias.chave_autenticidade` (`String(24)`, índice único) + migração **0005** (`batch_alter_table` para portabilidade SQLite/Postgres; `alembic check` limpo) | `infrastructure/database/models.py`, `migrations/versions/0005_chave_autenticidade.py` | RNF07 |
| Adapter SQLAlchemy: mapeamento ida/volta + `buscar_por_chave_autenticidade` | `adapters/outbound/persistence/ocorrencia_repositorio_sqlalchemy.py` | — |
| Router **`GET /v1/publico/documentos/{chave}`** — sem `exigir_papel`; `Path(min_length=24)` barra lixo antes do caso de uso | `adapters/inbound/http/v1/publico_router.py` | UC08 passos 1–3 |
| Wiring `get_autenticar_documento`; registro do router | `infrastructure/di.py`, `main.py` | HEX-02 |
| Mensagens `documento.not_found` / `documento.chave_invalida` em pt/en | `infrastructure/i18n/locales/*/default.json` | RNF08, UC08 Exceção I |
| **Consulta pública unificada** em **`/consulta`**: um único campo aceita o protocolo (acompanhamento) ou a chave de autenticidade; o modo é inferido pelo formato (`detectarModoConsulta`) e pode ser trocado por abas. **`/autenticar/:chave`** (deep-link do QR Code) renderiza a mesma página já conferindo; `/autenticar` redireciona para `/consulta?modo=chave`. Resultado com selo verde/vermelho e aviso LGPD | `frontend/src/pages/ConsultaPublicaPage.tsx`, `components/publico/ResultadoDocumento.tsx`, `utils/consultaPublica.ts`, `App.tsx` | UC08 passos 1–6 |
| `DocumentoEmitido`: chave + **QR Code** (`qrcode.react`) no detalhe da ocorrência validada; acesso público pela home (hero, card "Consulta Pública" e navbar) | `components/ocorrencias/DocumentoEmitido.tsx`, `OcorrenciaDetalhe.tsx`, `LandingPage.tsx`, `NavbarPublica.tsx` | UC08 passo 2 |
| `documentosService`, tipo `DocumentoAutenticado`, namespace i18n `publico` (pt/en), estilos | `services/documentosService.ts`, `types/api.ts`, `public/locales/*/publico.json`, `styles.css` | RNF08, RNF12 |
| Seed de um documento fictício já validado com chave fixa **`SGPX-SENT-DEMX-CHAV-EXEM-PLAR`** (idempotente), exibida como dica copiável na página pública — mesmo padrão da dica de credenciais do login | `scripts/seed_documento_demo.py`, `scripts/seed.py` | RNF07, RNF10 |

## 3. Decisões tomadas durante a implementação

- **A chave é emitida na validação, não na criação.** Só a ocorrência `VALIDADA` (e seus estados posteriores) é um documento oficial; `REJEITADA` nunca ganha chave. Isso reaproveita o momento em que o hash já é congelado (DEC-09).
- **Geração no domínio com `secrets` (stdlib)**, no mesmo espírito do `uuid4` já usado nas entidades — sem nova porta, sem alteração na assinatura de `validar()` e, portanto, **zero mudança nos casos de uso de revisão existentes**.
- **Espelho público sem dados pessoais (RNF02 / LGPD):** o portal devolve protocolo, situação, datas, natureza, tipificações, *contagem* de envolvidos por tipo e quantidade de evidências. **Nunca** nomes, documentos, endereço, coordenada, narrativa ou IDs de usuários. O teste de integração afirma isso campo a campo.
- **Consulta pública é auditada como anônima** (`quem=None`, `ip` do consulente, sufixo da chave) — UC08 passo 8. Uma chave inexistente **não** gera auditoria (espaço de 32²⁴ chaves torna enumeração impraticável; evita poluir o log).
- **`ADULTERADO` só pode surgir por alteração fora do sistema** (a máquina de estados não permite editar após validação). É exatamente o que o RF08 se propõe a detectar — e o cenário é demonstrável ao vivo (ver §5).
- **`RETIFICADO` / `ANULADO`** (UC08 passo 5) e **download da via com marca d'água** (passo 7) ficam fora: não existem retificação pós-validação nem geração de PDF no MVP (§3.2 da documentação de engenharia).
- Sem *rate limiting* nesta etapa: a chave é imprevisível e a consulta é somente leitura.

## 4. Testes

```
uv run pytest -q --cov   →   290 passed · cobertura 97 %
PYTHONPATH=src uv run lint-imports   →   3 contratos mantidos
uv run alembic check                 →   sem operações pendentes
npm run build (tsc + vite)           →   150 módulos, sem erros
```

| Arquivo | Cobre |
| :--- | :--- |
| `tests/unit/domain/test_autenticidade.py` (13) | tamanho/alfabeto da chave, unicidade, normalização (hífens, espaços, minúsculas), formatação, 7 formas malformadas, entidade sem documento antes de validar, emissão na validação (`emitida_em`), adulteração detectada, rejeição não emite |
| `tests/unit/use_cases/test_autenticar_documento.py` (7) | espelho sem dados pessoais (asserção negativa sobre nomes/CPF/endereço/narrativa), auditoria anônima com IP e commit, chave "como impressa", fraude → `documento.suspeita_fraude`, 404 sem auditoria, chave malformada, ocorrência não validada sem chave |
| `tests/integration/test_publico_http.py` (6) | chave só após validação (formato `XXXX-…`), portal sem token + campos ausentes + linha de auditoria, chave sem hífens/minúscula, **adulteração via `UPDATE` direto no banco → `ADULTERADO` + auditoria de fraude**, 404/422, `Accept-Language: en` |

## 5. Roteiro de demonstração

0. `uv run python -m scripts.seed` deixa pronto o documento demo — em `/consulta`, aba "Autenticar documento", basta clicar em "Copiar" na dica e conferir.
1. Agente registra uma ocorrência; Delegado valida → o detalhe mostra a chave e o QR Code.
2. Abrir a home em uma **janela anônima** (sem sessão) → "Consulta Pública" → colar a chave (a página reconhece o formato e troca para o modo de autenticação sozinha) → selo verde "Documento autêntico e íntegro".
3. Alterar a narrativa direto no banco (`UPDATE ocorrencias SET descricao=… WHERE chave_autenticidade=…`) → repetir a consulta → selo vermelho "documento adulterado" e linha `documento.suspeita_fraude` em `GET /v1/auditoria`.
4. Escanear o QR Code com o celular → abre `/autenticar/<chave>` já com o resultado.

## 6. Fora desta etapa

- PDF do BO com marca d'água e carimbo de tempo ICP-Brasil (UC08 passo 7; limite explícito do MVP).
- Status `RETIFICADO` / `ANULADO` e "segredo de justiça" (UC08 regra 2) — dependem de fluxos que o MVP não tem.
- *Rate limiting* / CAPTCHA no portal público.

## 7. Rastreabilidade

RF08 ✅ (Could Have → entregue) · UC08 cenário principal ✅ (passos 1–6, 8) · UC08 Exceção I ✅ · UC08 Exceção II ✅ · UC08 regra 1 ✅ · DEC-09 (reuso) ✅ · RNF02 ✅ · RNF03 ✅ · RNF08 ✅ · RNF10 ✅ · RNF12 ✅

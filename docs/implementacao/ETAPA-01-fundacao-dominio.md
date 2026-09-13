# ETAPA 01 — Fundação do domínio (máquina de estados, geolocalização, invariantes)

**Data:** 13/09/2026 · **Branch:** `matheus-Fastapi` · **Prioridade:** 🔴 bloqueante
**Origem:** `docs/analise/ETAPA-04` §1–2 (DEC-02, DEC-03, DEC-04, DEC-05, DEC-09) e §6 (HEX-03…HEX-08); `ETAPA-05` NEXT-01, NEXT-02 (parte de domínio), NEXT-05.

## 1. Objetivo

Fechar as três divergências bloqueantes da análise antes de qualquer outra fatia:
máquina de estados única (DIV-03), coordenada geográfica (DIV-16) e invariante
"≥ 1 envolvido" (DIV-18) — tudo em Python puro, sem tocar em infraestrutura.

## 2. O que foi implementado

| Item | Arquivo | Requisito / lacuna |
| :--- | :--- | :--- |
| Hierarquia de exceções com chave i18n (`DomainError.chave`, `.detalhes`) + `CampoObrigatorioError`, `ValorInvalidoError`, `AcessoNegadoError`, `ConflitoError` | `domain/shared/exceptions.py` | HEX-03, DIV-28 |
| Value object `Coordenada` (faixa validada, imutável) e `calcular_distancia_km` (Haversine, raio 6371,0088 km) | `domain/shared/geo.py` | DEC-03, DEC-05, HEX-05 |
| Validação de CPF (dígitos verificadores), aceite de RG como texto livre, máscara LGPD `***.***.789-**` | `domain/shared/documentos.py` | DEC-04, RNF10 |
| `EventoDominio` base | `domain/shared/eventos.py` | DEC-06 |
| `StatusOcorrencia` com 6 estados + tabela `TRANSICOES` (6 arestas) + `proximo_estado()` | `domain/ocorrencia/status.py` | DEC-02, HEX-04 |
| Fábricas de eventos (`ocorrencia_validada`, `_devolvida`, `_rejeitada`, `_reenviada`, `_despachada`, `_encerrada`) | `domain/ocorrencia/eventos.py` | RF17 |
| `Ocorrencia` reescrita: factory `registrar(...)`, `coordenada`, `data_hora_fato` (não futura, com fuso), `versao`, `atualizada_em`, `historico_status` (append-only), `hash_narrativa` SHA-256 na validação, métodos `validar`, `devolver_para_correcao`, `rejeitar`, `corrigir`, `reenviar`, `despachar`, `encerrar` | `domain/ocorrencia/entity.py` | RF01\*, RF04\*, RF14, RF18, RF19, DEC-09, HEX-06/07/08, RNF-P10 |
| `Envolvido` valida nome e documento; `TipificacaoPenal` valida campos | idem | RF01\* |
| `RegistroAuditoria` (imutável) | `domain/auditoria/entity.py` | RF20 |
| `Usuario` + enum `Papel` (6 papéis, 3 ativos no MVP) | `domain/usuario/entity.py` | RF12, DEC-08 |
| DTO `Ator` com `exigir_papel()` (defesa em profundidade) | `application/ports/inbound/ator.py` | RF12 |
| Portas de saída `Relogio`, `GeradorProtocolo` (+ `formatar_protocolo`), `UnidadeDeTrabalho` (context manager), `PortaAuditoria`, `PublicadorEventos`; `RepositorioOcorrencia` ganha `FiltroOcorrencias`, `contar()` e deixa de confirmar transação | `application/ports/outbound/*.py` | HEX-07/08/09/10, RNF11 |
| `RegistrarOcorrenciaPolicial` reescrito: ator do token, protocolo pela porta, instante pela porta, auditoria, commit explícito | `application/use_cases/ocorrencia/registrar_ocorrencia_policial.py` | RF01\* critérios 1–5 |
| Fakes: `RelogioFake`, `GeradorProtocoloFake`, `UnidadeDeTrabalhoFake`, `AuditoriaFake`, `PublicadorEventosFake`, `RepositorioOcorrenciaFake` (com checagem de versão) e atores por papel | `tests/fakes/` | RNF06 |

### Máquina de estados implementada (DEC-02)

```
[registrar] ─► AGUARDANDO_REVISAO ──validar──► VALIDADA ──despachar──► EM_ATENDIMENTO ──encerrar──► ENCERRADA
                    │      ▲
                    │      └──reenviar── EM_CORRECAO ◄──devolver_para_correcao──┘ (justificativa ≥ 10)
                    └──rejeitar (justificativa)──► REJEITADA
```

Removidos `REGISTRADA`, `EM_VALIDACAO` e a transição `enviar_para_validacao` (DIV-04).

## 3. Decisões tomadas durante a implementação

- **Descrição ≥ 20 caracteres** conforme RF01\* reescrito; testes antigos foram ajustados.
- **CPF "123.456.789-00" do teste original era inválido** pelos dígitos verificadores → substituído por `123.456.789-09`. Documentos com 11 dígitos são tratados como CPF; qualquer outro formato é aceito como texto livre (RG).
- **`__init__` da entidade é reservado à re-hidratação** pelo repositório (aceita construção sem envolvidos); a invariante é imposta na factory `registrar()` e em `corrigir()`, conforme sugestão HEX-06.
- **`versao` incrementa a cada mutação** (transição ou correção) — base do *optimistic locking* (RNF11) implementado no adapter na Etapa 2.
- **Hash da narrativa** cobre natureza, descrição, localização, data do fato, envolvidos e tipificações (ordenados) — reutilizável por RF08 no futuro.
- `Ator.ip` viaja no DTO para que a auditoria registre o IP sem o caso de uso conhecer HTTP.

## 4. Testes

```
uv run pytest tests/unit -q   →   61 passed
```

| Arquivo | Cobre |
| :--- | :--- |
| `tests/unit/domain/test_geo.py` (7) | faixa de coordenada, imutabilidade, Haversine (0 km, ~441 km Alegrete↔Porto Alegre, 1° ≈ 111,19 km, simetria) |
| `tests/unit/domain/test_documentos.py` (6) | CPF válido/inválido, RG livre, máscara |
| `tests/unit/domain/test_ocorrencia_entity.py` (39) | factory e invariantes, todas as 6 transições, terminais, ciclo correção→reenvio→validação, hash de integridade, autoria |
| `tests/unit/use_cases/test_registrar_ocorrencia_policial.py` (9) | protocolo sequencial, ator do token, commit/rollback, auditoria, papel exigido, erros de validação |

## 5. Fora desta etapa (vai para as próximas)

- Adapters SQLAlchemy, Alembic, DI, handler HTTP de `DomainError` → **Etapa 2**.
- Autenticação real (JWT) que produz o `Ator` → **Etapa 3**.
- Casos de uso de listagem, revisão e correção que usam os métodos criados aqui → **Etapa 4**.
- O router HTTP existente **ficou temporariamente incompatível** com o novo DTO (será reescrito na Etapa 2); os testes de unidade não o carregam.

## 6. Rastreabilidade

DIV-03 ✅ · DIV-04 ✅ · DIV-05 ✅ · DIV-16 ✅ · DIV-17 (decisão DEC-04 aplicada) · DIV-18 ✅ · DIV-28 ✅ (domínio) · RF-P02 ✅ · RF-P04 ✅ · RF-P07 ✅ (domínio) · RF-P10 ✅ (domínio) · RF-P15 ✅ · RF-P18 ✅ · HEX-03 ✅ · HEX-04 ✅ · HEX-05 ✅ · HEX-06 ✅ · HEX-07 ✅ · HEX-08 ✅ · HEX-10 ✅ (portas)

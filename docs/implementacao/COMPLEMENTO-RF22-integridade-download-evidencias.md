# Complemento RF22 — Integridade e download seguro de evidências digitais

**Data:** 19/09/2026 · **Issue:** #41 · **Escopo:** RF01, RF22, RF20, RNF02, RNF03 e RNF05

## 1. Objetivo e rastreabilidade

Este complemento registra a conclusão da gestão de integridade e do acesso seguro às evidências digitais vinculadas à ocorrência. A implementação amplia o RF22 sem alterar o fluxo de registro do RF01:

| Referência | Relação com a implementação |
| :--- | :--- |
| **RF01** | A evidência permanece vinculada à ocorrência e seus metadados são apresentados no detalhe. |
| **RF22** | O arquivo armazenado pode ter sua integridade conferida e, quando íntegro, ser baixado por usuário autorizado. |
| **RF20** | Verificações de integridade, downloads e ausência do arquivo físico geram registros de auditoria. |
| **RNF02** | As operações exigem autenticação, papel autorizado e a mesma política de autoria usada na consulta da ocorrência. |
| **RNF03** | O SHA-256 persistido é comparado com o hash recalculado a partir dos bytes armazenados; divergências ficam visíveis e impedem o download. |
| **RNF05** | FastAPI e filesystem permanecem fora de `domain` e `application`; o arquivo é acessado por porta outbound. |

## 2. Situação anterior

Antes da issue #41, o sistema já permitia:

- upload `multipart/form-data` de PDF, JPG, JPEG e PNG;
- validação de formato, assinatura do conteúdo, tamanho e limite por ocorrência;
- persistência do arquivo em disco por `ArmazenamentoDisco`;
- vínculo permanente da evidência à ocorrência;
- persistência de `nome_original`, `formato`, `tamanho`, `hash_sha256`, `chave_armazenamento` e data/hora do envio;
- listagem dos metadados da evidência no contrato de detalhe da ocorrência.

O schema necessário já existia. A issue não exigiu alteração de tabela nem nova migration.

## 3. Incrementos da issue #41

Foram adicionados:

1. exibição do SHA-256 completo no detalhe da ocorrência;
2. verificação criptográfica pela releitura do arquivo armazenado e recálculo do SHA-256;
3. estados fechados `INTEGRA` e `DIVERGENTE`;
4. download autenticado e autorizado;
5. bloqueio do download quando o hash recalculado diverge do hash persistido;
6. reutilização da política de autorização da consulta de ocorrência;
7. operação `ArmazenamentoArquivos.ler(...)` e implementação no adapter de disco;
8. auditoria da verificação, do download e da ausência do arquivo físico;
9. proteção contra path traversal, caminhos absolutos e symlinks que escapem da raiz configurada;
10. respostas HTTP e frontend sem exposição da chave de armazenamento ou do caminho físico;
11. indicador visual de integridade e botão de download habilitado apenas para arquivo íntegro.

## 4. Fluxo de verificação de integridade

1. O cliente chama `GET /v1/ocorrencias/{ocorrencia_id}/evidencias/{evidencia_id}/integridade` com token válido.
2. O adapter HTTP obtém o `Ator` do token e chama `VerificarIntegridadeEvidencia` pela porta inbound.
3. O caso de uso aplica a política compartilhada de consulta: valida o papel e, para `AGENTE`, exige que ele seja o autor da ocorrência.
4. A ocorrência e a evidência são localizadas pelo `RepositorioOcorrencia`.
5. O conteúdo é recuperado por `ArmazenamentoArquivos.ler(chave_armazenamento)`.
6. O caso de uso recalcula `SHA-256(conteudo)` e compara o resultado com `evidencia.hash_sha256`.
7. A operação e o estado resultante são auditados.
8. A API devolve `INTEGRA` ou `DIVERGENTE`, sem devolver a chave ou o caminho físico.

Ocorrência inexistente, evidência inexistente ou arquivo físico ausente produzem `404`; ator autenticado sem autorização produz `403`.

## 5. Fluxo de download seguro

1. O cliente somente habilita o botão após uma verificação com estado `INTEGRA`.
2. O cliente chama `GET /v1/ocorrencias/{ocorrencia_id}/evidencias/{evidencia_id}/download` com token válido.
3. `ObterEvidenciaParaDownload` repete a autorização, relê o arquivo e recalcula o SHA-256 no momento do download; o estado anterior da interface não é considerado prova suficiente.
4. Se o resultado for `DIVERGENTE`, a tentativa é auditada e o caso de uso lança conflito; a API responde `409` com `evidencia.integridade_divergente` e não entrega os bytes.
5. Se o resultado for `INTEGRA`, a operação é auditada e o adapter HTTP devolve os bytes com MIME controlado, nome original codificado em `Content-Disposition`, `Content-Length` e `X-Content-Type-Options: nosniff`.

## 6. Mapeamento da Arquitetura Hexagonal

| Camada | Elementos |
| :--- | :--- |
| **Inbound adapter** | Rotas de integridade e download em `adapters/inbound/http/v1/ocorrencias_router.py`; autenticação antecipada e transformação para resposta HTTP, delegando as regras de autorização e integridade aos casos de uso. |
| **Portas inbound** | `InterfaceVerificarIntegridadeEvidencia` e `InterfaceObterEvidenciaParaDownload`, com DTOs independentes de FastAPI. |
| **Casos de uso** | `VerificarIntegridadeEvidencia` e `ObterEvidenciaParaDownload`, responsáveis por autorização, localização, leitura, hash, auditoria e bloqueio de divergência. |
| **Política compartilhada** | `carregar_autorizada(...)`, reutilizada pelo detalhe da ocorrência e pelos acessos à evidência. |
| **Porta outbound** | `ArmazenamentoArquivos.ler(chave) -> bytes | None`, além da operação de gravação já existente. |
| **Outbound adapter** | `ArmazenamentoDisco`, responsável pela leitura concreta no filesystem e pela contenção do caminho na raiz configurada. |
| **Composition root** | Providers dos dois casos de uso em `infrastructure/di.py`. |
| **Auditoria** | `PortaAuditoria` recebe `evidencia.verificar_integridade` e `evidencia.download`, incluindo o estado observado. |

Os módulos `domain` e `application` continuam sem dependências de FastAPI, SQLAlchemy ou filesystem. O acesso ao arquivo ocorre exclusivamente pela porta `ArmazenamentoArquivos`.

## 7. Autorização, auditoria e proteção do armazenamento

- Papéis de consulta autorizados: `AGENTE`, `DELEGADO`, `OPERADOR_CENTRAL` e `SUPERVISOR`.
- O `AGENTE` somente acessa evidências de ocorrências de sua autoria.
- A autorização é aplicada no caso de uso, além da restrição antecipada do adapter HTTP.
- A auditoria registra o ator, instante, operação, evidência, ocorrência, IP e estado de integridade.
- Arquivo ausente é auditado como `ARQUIVO_AUSENTE`.
- `ArmazenamentoDisco.ler(...)` rejeita chave vazia, caminho absoluto, múltiplos segmentos e path traversal.
- O caminho candidato é resolvido e precisa permanecer contido na raiz configurada; symlink apontando para fora é rejeitado.
- A API não serializa `chave_armazenamento` nem caminhos locais.

## 8. Persistência e migrations

Não foi criada migration. A tabela de evidências já continha os metadados necessários, incluindo `hash_sha256` e `chave_armazenamento`. A implementação adicionou comportamento de leitura, conferência, autorização e entrega, sem alterar o schema persistido.

## 9. Testes e validações

Foram adicionados ou ampliados testes para:

- arquivo íntegro e divergente;
- arquivo físico ausente;
- ocorrência e evidência inexistentes;
- papéis autorizados, agente não autor e papel não permitido;
- download dos mesmos bytes armazenados;
- bloqueio do download divergente;
- auditoria da verificação e do download;
- leitura do adapter de disco;
- rejeição de caminho absoluto e path traversal;
- rejeição de symlink apontando para fora da raiz;
- autenticação e autorização das rotas HTTP;
- conteúdo, MIME, `Content-Disposition`, `nosniff` e ausência de vazamento de caminho físico.

Resultados finais:

| Verificação | Resultado |
| :--- | :--- |
| Testes específicos de evidências | **44 passed** |
| Suíte backend completa | **286 passed** |
| `PYTHONPATH=src uv run lint-imports --config pyproject.toml` | **3 contratos mantidos, 0 quebrados** |
| `npx tsc --noEmit` | OK |
| `npm run build` | OK |
| `git diff --check` | OK |
| Teste manual | SHA-256 exibido; arquivo marcado como íntegro; download autorizado concluído; imagem baixada e aberta corretamente |

## 10. Limitações e fronteira do escopo

Esta entrega **não deve ser descrita como uma cadeia de custódia completa**. Ela fornece integridade criptográfica, vínculo permanente e rastreabilidade das operações de verificação e download, mas ainda não modela eventos de transferência de custódia, origem, destino, responsáveis pela entrega/recebimento ou uma linha temporal própria de movimentações.

Esses elementos pertencem à evolução da cadeia de custódia de apreensões já identificada em RF03/RF-P13 e não foram adicionados pela issue #41.

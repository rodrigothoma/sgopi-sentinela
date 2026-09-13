# 📘 Documentação do MVP — SGOPI Sentinela

Esta pasta complementa a [Documentação de Engenharia](../DOCUMENTACAO_DE_ENGENHARIA.md) com o material produzido **durante a implementação** do MVP (React + Next.js, Arquitetura Hexagonal).

| Documento | Conteúdo |
| :--- | :--- |
| [01 — Análise de Complexidade](01-analise-de-complexidade.md) | Complexidade de cada RF/RNF, do prompt de implementação e das decisões tomadas sob ambiguidade. |
| [02 — Plano de Implementação do MVP](02-plano-de-implementacao-mvp.md) | Passos ordenados para construir (e continuar) o MVP: o que já está feito, o que falta, como executar e testar. |
| [03 — Problemas Encontrados](03-problemas-encontrados.md) | Problemas técnicos e de especificação **não previstos na documentação original**, com impacto e solução/mitigação adotada. |
| [04 — Arquitetura Implementada](04-arquitetura-implementada.md) | Mapa do código para as camadas hexagonais, contratos das portas, API REST/SSE, matriz RBAC e máquina de estados. |

## Execução rápida

```bash
npm install
cp .env.example .env.local     # opcional em dev; obrigatório em produção (SESSION_SECRET)
npm run dev                    # http://localhost:3000
npm test                       # testes do núcleo (vitest)
npm run build && npm start     # produção (exige SESSION_SECRET)
```

Contas de demonstração (senha `sgopi123`): `agente`, `agente2`, `delegado`, `operador`, `supervisor`, `perito`.

## Roteiro de demonstração (fluxo ponta a ponta — Seção 3.3 da especificação)

1. **Agente** (`agente`) → *Nova ocorrência* → preenche fato, local (coordenada pré-preenchida em Alegrete), ≥ 1 envolvido → *Submeter para revisão*. Protocolo `BO-2026-000001` é gerado.
2. **Delegado** (`delegado`) → *Fila de revisão* → *Analisar* → escreve o despacho da autoridade → *Validar ocorrência*. A narrativa é selada com SHA-256.
3. **Operador** (`operador`) → *Painel tático* → viaturas se movem em tempo real (SSE) → clica na ocorrência → vê as 3 mais próximas com distância → *Despachar*. A viatura fica `EM_DESLOCAMENTO` e a ocorrência `EM_ATENDIMENTO`.
4. **Supervisor/Delegado** → *Auditoria* → cadeia de hashes íntegra com todos os eventos, incluindo tentativas negadas.
5. **RNF04**: aguarde ~80 s; a `VTR-1205` perde sinal (marcador amarelo, aviso no painel, botão vira *Despacho manual* exigindo posição via rádio). *Ver listagem tabular* mostra a última posição conhecida.

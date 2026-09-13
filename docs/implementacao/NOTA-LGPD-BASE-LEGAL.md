# Nota de conformidade — LGPD e imutabilidade (RNF03\*, RNF10)

**Contexto:** o SGOPI trata dados pessoais e dados pessoais sensíveis (LGPD art. 5º, I e II) de vítimas, testemunhas e suspeitos, e o RNF03 exige que registros validados, ordens de despacho e auditoria **não sejam excluídos**.

## Base legal adotada no MVP

| Tratamento | Base legal (LGPD) | Observação |
| :--- | :--- | :--- |
| Registro e revisão de ocorrências policiais | Art. 4º, III, *a* — atividades de **segurança pública** ficam fora do regime geral e sujeitas a legislação específica; subsidiariamente art. 7º, II/III (obrigação legal; execução de políticas públicas) | O sistema é acadêmico (dados fictícios); em produção, exige norma da corporação. |
| Auditoria append-only e retenção sem exclusão | Art. 7º, II (cumprimento de obrigação legal) e art. 16, I (conservação para cumprimento de obrigação legal) | Justifica a recusa ao direito de eliminação (art. 18, VI) enquanto durar a finalidade. |
| Exibição de CPF | Princípio da necessidade (art. 6º, III) | Em claro só para Delegado e para o Agente autor; mascarado (`***.***.789-**`) para Operador/Supervisor e **sempre** em logs. |

## Medidas técnicas implementadas

- Máscara de CPF por papel nas respostas da API (`application/use_cases/ocorrencia/_mapeadores.py`).
- Máscara de CPF em todo log (mensagem, campos extra e *stack trace*) — `infrastructure/logging.py`.
- Sem `DELETE` na API; filhos removidos ficam `ativo = false`; auditoria e histórico protegidos por *trigger* no Postgres.
- Seed apenas com dados fictícios (`scripts/seed.py`).
- Toda operação sensível auditada com autor, IP e instante (RF20).

## Pendências (fora do MVP)

- Política de retenção/anonimização (RNF B9 da análise).
- Revisão de segurança do frontend (armazenamento de token, CSP).
- Registro de operações de tratamento (art. 37) — documento organizacional.

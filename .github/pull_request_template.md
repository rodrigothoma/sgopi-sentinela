## 📌 Descrição da Alteração
<!-- Resumo conciso do que foi implementado, refatorado ou corrigido. -->

## 🎯 Rastreabilidade com a Documentação
- **Requisito Atendido:** [ex: RF01 - Gestão de Ocorrência Policial, RF04 - Validação]
- **Caso de Uso:** [ex: UC01 - Registrar Ocorrência Policial, UC02 - Despachar Viatura]
- **Diagrama UML de Referência:** [ex: docs/diagramas/sequencia/sq01-registrar-ocorrencia-policial.png]
- **Card no Kanban / Issue:** Closes #...

---

## 🏛️ Checklist de Arquitetura Hexagonal & SOLID (Obrigatório)

### Arquitetura Hexagonal:
- [ ] O `domain/` permanece em Python puro, sem importações de ORM, framework web ou schemas HTTP.
- [ ] O `application/` depende unicamente de abstrações definidas em `ports/`, sem acoplamento a adapters concretos.
- [ ] Todo novo adaptador de persistência ou serviço implementa uma porta em `ports/outbound/`.
- [ ] Injeção de dependência realizada exclusivamente no composition root (`infrastructure/di.py`).

### Princípios SOLID & Clean Code:
- [ ] **S (SRP):** Cada classe e função possui responsabilidade única e coesa.
- [ ] **O (OCP):** Comportamentos novos foram adicionados via extensão de interfaces/portas, sem alterar código estável.
- [ ] **L (LSP):** As implementações concretas honram integralmente os contratos abstratos das portas.
- [ ] **I (ISP):** Portas são focadas e não forçam métodos desnecessários para os consumidores.
- [ ] **D (DIP):** Dependências invertidas através de contratos abstratos (`abc.ABC`).
- [ ] **Clean Code:** Nomes autoexplicativos em português no domínio, tipagem estrita e ausência de código comentado ou comentários redundantes.

### Governança & RNF03:
- [ ] Nenhuma exclusão física (`DELETE`) adicionada em tabelas de negócio (utiliza exclusão lógica `ativo = false`).
- [ ] Tabelas append-only (`registros_auditoria`, `historico_status_ocorrencia`) preservadas sem comandos destrutivos.

---

## 🧪 Verificação Local Executada
- [ ] `PYTHONPATH=src uv run lint-imports --config pyproject.toml` executou e passou com 0 violações.
- [ ] `uv run pytest --cov` executou com sucesso e atendeu à cobertura mínima de 80% em `domain/` e `application/`.
- [ ] No frontend, `npx tsc --noEmit` e `npm run build` executaram sem erros (se aplicável).
- [ ] Verificado que não há resíduos de chat de IA (`contentReference`, notas conversacionais, etc.).

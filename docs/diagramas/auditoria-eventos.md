# Auditoria — eventos tipados (RNF03)

Diagramas da auditoria por eventos. Código em `backend/src/domain/auditoria/` (classe base) e nos `auditoria.py` de cada agregado (subclasses). O GitHub desenha os blocos `mermaid` abaixo direto na página.

## 1. Diagrama de classes — eventos da ocorrência

Cada nível da hierarquia preenche uma parte do registro. A ação concreta (ex.: `OcorrenciaValidada`) declara só a `OPERACAO` e herda o resto. O `RegistroAuditoria` **não faz parte da herança**: ele é criado pelo `para_registro()` da classe base.

```mermaid
classDiagram
    direction TB

    class EventoAuditoria {
        <<abstract>>
        +str OPERACAO
        +str ENTIDADE
        +id_entidade() str*
        +dados_antes() dict
        +dados_depois() dict*
        +para_registro(contexto) RegistroAuditoria
        +catalogo() tuple
    }

    class EventoOcorrencia {
        <<abstract>>
        +str ENTIDADE = 'Ocorrencia'
        +UUID ocorrencia_id
        +id_entidade() str
    }

    class MudancaStatusOcorrencia {
        <<abstract>>
        +SituacaoOcorrencia antes
        +SituacaoOcorrencia depois
        +dados_antes() dict
        +dados_depois() dict
    }

    class SituacaoOcorrencia {
        +str status
        +int versao
        +como_dict() dict
    }

    class DecisaoSobreOcorrencia {
        <<abstract>>
        +str CAMPO_TEXTO = 'justificativa'
        +str texto
        +dados_depois() dict
    }

    class OcorrenciaValidada {
        +str OPERACAO = 'ocorrencia.validar'
        +str CAMPO_TEXTO = 'despacho'
    }
    class OcorrenciaDevolvidaParaCorrecao {
        +str OPERACAO = 'ocorrencia.devolver_para_correcao'
    }
    class OcorrenciaRejeitada {
        +str OPERACAO = 'ocorrencia.rejeitar'
    }
    class OcorrenciaReenviada {
        +str OPERACAO = 'ocorrencia.reenviar'
    }
    class OcorrenciaRegistrada {
        +str OPERACAO = 'ocorrencia.registrar'
        +str protocolo
        +str prioridade
        +dados_depois() dict
    }
    class OcorrenciaCorrigida {
        +str OPERACAO = 'ocorrencia.corrigir'
        +str descricao_antes
        +str descricao
        +dados_antes() dict
        +dados_depois() dict
    }

    class ContextoAuditoria {
        +UUID quem
        +datetime quando
        +str ip
    }

    class RegistroAuditoria {
        +UUID quem
        +datetime quando
        +str operacao
        +str entidade
        +str entidade_id
        +dict dados_antes
        +dict dados_depois
        +str ip
    }

    EventoAuditoria <|-- EventoOcorrencia
    EventoOcorrencia <|-- OcorrenciaRegistrada
    EventoOcorrencia <|-- OcorrenciaCorrigida
    EventoOcorrencia <|-- MudancaStatusOcorrencia
    MudancaStatusOcorrencia <|-- OcorrenciaReenviada
    MudancaStatusOcorrencia <|-- DecisaoSobreOcorrencia
    DecisaoSobreOcorrencia <|-- OcorrenciaValidada
    DecisaoSobreOcorrencia <|-- OcorrenciaDevolvidaParaCorrecao
    DecisaoSobreOcorrencia <|-- OcorrenciaRejeitada

    MudancaStatusOcorrencia *-- "2" SituacaoOcorrencia : antes e depois
    EventoAuditoria ..> ContextoAuditoria : recebe
    EventoAuditoria ..> RegistroAuditoria : para_registro() cria
```

Como ler:

- **Setas com triângulo vazado** indicam herança, sempre da filha para a mãe.
- **Seta tracejada** indica que uma classe usa ou cria a outra, sem herdar dela.
- `<<abstract>>` marca as classes que não podem ser instanciadas: a base e as intermediárias, que não têm `OPERACAO`.
- Métodos com `*` são abstratos e cada subclasse precisa implementá-los.

### De onde vem cada campo do registro de `OcorrenciaValidada`

| Campo do `RegistroAuditoria` | Quem fornece |
| :--- | :--- |
| `operacao` | `OcorrenciaValidada.OPERACAO` → `"ocorrencia.validar"` |
| `entidade` | `EventoOcorrencia.ENTIDADE` → `"Ocorrencia"` |
| `entidade_id` | `EventoOcorrencia.id_entidade()` → id da ocorrência |
| `dados_antes` | `MudancaStatusOcorrencia.dados_antes()` → `status` e `versao` antes |
| `dados_depois` | `DecisaoSobreOcorrencia.dados_depois()` → `status` e `versao` depois + `despacho` (nome vindo do `CAMPO_TEXTO` da `OcorrenciaValidada`) |
| `quem`, `quando`, `ip` | `ContextoAuditoria`, montado por `ator.contexto_auditoria(agora)` |

## 2. Diagrama de sequência — gravação

```mermaid
sequenceDiagram
    participant UC as ValidarOcorrencia<br/>(caso de uso)
    participant A as Ator
    participant E as OcorrenciaValidada<br/>(evento)
    participant P as AuditoriaSQLAlchemy<br/>(implementa PortaAuditoria)
    participant R as RegistroAuditoria
    participant DB as registros_auditoria<br/>(tabela)

    UC->>E: OcorrenciaValidada.de(ocorrencia, antes)
    UC->>A: contexto_auditoria(agora)
    A-->>UC: ContextoAuditoria(quem, quando, ip)
    UC->>P: registrar(evento, contexto)
    rect rgba(13, 127, 99, 0.12)
        Note over P,R: Template Method
        P->>E: para_registro(contexto)
        E->>R: cria com OPERACAO, ENTIDADE, id_entidade(), dados_antes(), dados_depois() e o contexto
        E-->>P: RegistroAuditoria
    end
    P->>DB: INSERT (RegistroAuditoriaModel), na mesma transação da validação
```

O caso de uso conhece só a porta (`PortaAuditoria`). Quem sabe montar a linha é o evento, e quem sabe gravar no banco é o adapter. Como a gravação acontece na mesma transação da validação, ou entram as duas coisas (ocorrência validada e auditoria), ou nenhuma.

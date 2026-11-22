import 'papel.dart';

/// Capacidades que o app mobile oferece, espelhando o backend.
///
/// O backend continua sendo a autoridade (ele recusa com 403); aqui a matriz só
/// decide quais telas e ações aparecem. Mantenha alinhado com
/// `backend/src/domain/usuario/permissoes.py` e com `exigir_papel` dos routers:
/// registrar/corrigir ocorrência é exclusivo do AGENTE e a revisão (RF04) do DELEGADO.
enum Permissao {
  registrarOcorrencia({Papel.agente}),
  revisarOcorrencia({Papel.delegado});

  const Permissao(this.papeis);

  final Set<Papel> papeis;
}

extension PermissoesDoPapel on Papel {
  bool pode(Permissao permissao) => permissao.papeis.contains(this);
}

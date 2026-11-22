import '../../ocorrencias/domain/enums.dart';
import '../../ocorrencias/domain/ocorrencia.dart';

/// Fila de triagem do Delegado: aguardando revisão, as mais graves primeiro
/// e, na mesma gravidade, as mais antigas (ordem padrão do backend).
const filtroFilaRevisao = FiltroOcorrencias(
  status: {StatusOcorrencia.aguardandoRevisao},
  ordenarPorPrioridade: true,
);

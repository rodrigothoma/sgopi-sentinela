import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:material_ui/material_ui.dart';

import '../../../../core/aplicacao/dependencias.dart';
import '../../../../core/apresentacao/contexto.dart';
import '../../../../core/apresentacao/componentes/barra_acoes.dart';
import '../../../../core/apresentacao/componentes/cartao_secao.dart';
import '../../application/dependencias.dart';
import '../../domain/arquivo_evidencia.dart';
import '../../domain/dados_ocorrencia.dart';
import '../../domain/enums.dart';
import '../../domain/ocorrencia.dart';
import '../../domain/portas.dart';
import '../rotulos.dart';
import 'dialogo_envolvido.dart';
import 'dialogo_tipificacao.dart';
import 'painel_evidencias.dart';

/// Quanto tempo para trás o seletor de data do fato permite escolher.
const _janelaDataFato = Duration(days: 365);

typedef AoEnviarOcorrencia = Future<void> Function(
  DadosOcorrencia dados,
  List<ArquivoEvidencia> evidencias,
);

/// Formulário da narrativa (UC01), usado no registro e na correção.
///
/// Valida com as mesmas regras do domínio antes de chamar [aoEnviar]; erros
/// lançados por [aoEnviar] (rede, regra do backend) aparecem num aviso.
class FormularioOcorrencia extends ConsumerStatefulWidget {
  const FormularioOcorrencia({
    required this.titulo,
    required this.rotuloEnviar,
    required this.aoEnviar,
    this.inicial,
    this.evidenciasJaAnexadas = 0,
    super.key,
  });

  final String titulo;
  final String rotuloEnviar;
  final AoEnviarOcorrencia aoEnviar;
  final OcorrenciaDetalhe? inicial;
  final int evidenciasJaAnexadas;

  @override
  ConsumerState<FormularioOcorrencia> createState() => _FormularioOcorrenciaState();
}

class _FormularioOcorrenciaState extends ConsumerState<FormularioOcorrencia> {
  late final _natureza = TextEditingController(text: widget.inicial?.natureza);
  late final _descricao = TextEditingController(text: widget.inicial?.descricao);
  late final _localizacao = TextEditingController(text: widget.inicial?.localizacao);
  late Coordenada? _coordenada = widget.inicial?.coordenada;
  late DateTime _dataHoraFato = widget.inicial?.dataHoraFato ?? ref.read(relogioProvider).agora();
  late final List<Envolvido> _envolvidos = [...?widget.inicial?.envolvidos];
  late final List<Tipificacao> _tipificacoes = [...?widget.inicial?.tipificacoes];
  final List<ArquivoEvidencia> _evidencias = [];
  PrioridadeOcorrencia? _prioridade;
  Set<ErroOcorrencia> _erros = const {};
  bool _localizando = false;
  bool _enviando = false;

  bool get _novo => widget.inicial == null;

  @override
  void initState() {
    super.initState();
    if (_novo) WidgetsBinding.instance.addPostFrameCallback((_) => _usarMinhaLocalizacao());
  }

  @override
  void dispose() {
    for (final c in [_natureza, _descricao, _localizacao]) {
      c.dispose();
    }
    super.dispose();
  }

  DadosOcorrencia _montarDados() => DadosOcorrencia(
    natureza: _natureza.text,
    descricao: _descricao.text,
    localizacao: _localizacao.text,
    coordenada: _coordenada,
    dataHoraFato: _dataHoraFato,
    envolvidos: List.of(_envolvidos),
    tipificacoes: List.of(_tipificacoes),
    prioridade: _prioridade,
  );

  Future<void> _enviar() async {
    final dados = _montarDados();
    setState(() => _erros = dados.validar(ref.read(relogioProvider).agora()));
    if (_erros.isNotEmpty) {
      // O envio fica fixo no rodapé: o resumo avisa de erros em cartões fora da tela.
      final t = context.textos;
      return context.avisar(_erros.map((e) => mensagemErroOcorrencia(t, e)).join('\n'));
    }
    setState(() => _enviando = true);
    try {
      await widget.aoEnviar(dados, List.of(_evidencias));
    } on Exception catch (erro) {
      if (mounted) context.avisar(mensagemDeErro(context.textos, erro));
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  Future<void> _usarMinhaLocalizacao() async {
    setState(() => _localizando = true);
    try {
      final coordenada = await ref.read(portaLocalizacaoProvider).obterAtual();
      if (mounted) setState(() => _coordenada = coordenada);
    } on LocalizacaoIndisponivel catch (erro) {
      if (mounted) context.avisar(mensagemDeErro(context.textos, erro));
    } finally {
      if (mounted) setState(() => _localizando = false);
    }
  }

  Future<void> _adicionarEvidencia(OrigemImagem origem) async {
    final arquivo = await ref.read(portaSeletorImagemProvider).selecionar(origem);
    if (arquivo == null || !mounted) return;
    final erro = validarLoteEvidencias([
      ..._evidencias,
      arquivo,
    ], jaAnexadas: widget.evidenciasJaAnexadas);
    if (erro != null) return context.avisar(mensagemErroEvidencia(context.textos, erro));
    setState(() => _evidencias.add(arquivo));
  }

  Future<void> _escolherDataHora() async {
    final agora = ref.read(relogioProvider).agora().toLocal();
    final atual = _dataHoraFato.toLocal();
    final dia = await showDatePicker(
      context: context,
      initialDate: atual,
      firstDate: agora.subtract(_janelaDataFato),
      lastDate: agora,
    );
    if (dia == null || !mounted) return;
    final hora = await showTimePicker(context: context, initialTime: TimeOfDay.fromDateTime(atual));
    if (hora == null) return;
    setState(() => _dataHoraFato = DateTime(dia.year, dia.month, dia.day, hora.hour, hora.minute));
  }

  String? _erro(ErroOcorrencia erro) =>
      _erros.contains(erro) ? mensagemErroOcorrencia(context.textos, erro) : null;

  /// Cartões na ordem do registro em campo, com o envio fixo no rodapé. O
  /// formulário monta o próprio Scaffold para o botão ocupar o `bottomNavigationBar`:
  /// assim os avisos flutuantes aparecem acima dele, sem cobri-lo.
  @override
  Widget build(BuildContext context) {
    final t = context.textos;
    const espaco = SizedBox(height: 12);
    return Scaffold(
      appBar: AppBar(title: Text(widget.titulo)),
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          CartaoSecao(titulo: t.secaoFato, icone: Icons.event_note_outlined, filhos: _secaoFato()),
          espaco,
          CartaoSecao(titulo: t.secaoLocal, icone: Icons.place_outlined, filhos: _secaoLocal()),
          espaco,
          _secaoEnvolvidos(),
          espaco,
          _secaoTipificacoes(),
          espaco,
          CartaoSecao(
            titulo: t.secaoEvidencias,
            icone: Icons.photo_library_outlined,
            filhos: [
              PainelEvidencias(
                arquivos: _evidencias,
                aoAdicionar: _adicionarEvidencia,
                aoRemover: (a) => setState(() => _evidencias.remove(a)),
              ),
            ],
          ),
        ],
      ),
      bottomNavigationBar: BarraAcoes(
        child: SizedBox(
          width: double.infinity,
          child: FilledButton.icon(
            key: const Key('ocorrencia.enviar'),
            onPressed: _enviando ? null : _enviar,
            icon: _enviando
                ? const SizedBox.square(
                    dimension: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.send),
            label: Text(widget.rotuloEnviar),
          ),
        ),
      ),
    );
  }

  List<Widget> _secaoFato() {
    final t = context.textos;
    return [
      TextField(
        key: const Key('ocorrencia.natureza'),
        controller: _natureza,
        textCapitalization: TextCapitalization.sentences,
        decoration: InputDecoration(
          labelText: t.campoNatureza,
          hintText: t.dicaNatureza,
          errorText: _erro(ErroOcorrencia.naturezaVazia),
        ),
      ),
      const SizedBox(height: 12),
      TextField(
        key: const Key('ocorrencia.descricao'),
        controller: _descricao,
        minLines: 4,
        maxLines: 10,
        textCapitalization: TextCapitalization.sentences,
        decoration: InputDecoration(
          labelText: t.campoDescricao,
          helperText: t.ajudaDescricao(tamanhoMinimoDescricao),
          errorText: _erro(ErroOcorrencia.descricaoCurta),
        ),
      ),
      const SizedBox(height: 12),
      ListTile(
        contentPadding: EdgeInsets.zero,
        leading: const Icon(Icons.event),
        title: Text(t.campoDataHora),
        subtitle: Text(_erro(ErroOcorrencia.dataFatoFutura) ?? context.dataHora(_dataHoraFato)),
        onTap: _escolherDataHora,
      ),
      if (_novo) ...[const SizedBox(height: 4), _campoPrioridade()],
    ];
  }

  Widget _campoPrioridade() {
    final t = context.textos;
    return DropdownButtonFormField<PrioridadeOcorrencia?>(
      initialValue: _prioridade,
      isExpanded: true,
      decoration: InputDecoration(labelText: t.campoPrioridade),
      items: [
        DropdownMenuItem(child: Text(t.prioridadeAutomatica, overflow: TextOverflow.ellipsis)),
        for (final p in PrioridadeOcorrencia.values)
          DropdownMenuItem(value: p, child: Text(p.rotulo(t))),
      ],
      onChanged: (p) => setState(() => _prioridade = p),
    );
  }

  List<Widget> _secaoLocal() {
    final t = context.textos;
    final c = _coordenada;
    return [
      TextField(
        key: const Key('ocorrencia.localizacao'),
        controller: _localizacao,
        decoration: InputDecoration(
          labelText: t.campoLocalizacao,
          errorText: _erro(ErroOcorrencia.localizacaoVazia),
        ),
      ),
      ListTile(
        contentPadding: EdgeInsets.zero,
        leading: const Icon(Icons.my_location),
        title: Text(
          c == null
              ? t.coordenadaPendente
              : t.coordenadaDefinida(c.latitude.toStringAsFixed(6), c.longitude.toStringAsFixed(6)),
        ),
        subtitle: _erros.contains(ErroOcorrencia.coordenadaInvalida)
            ? Text(
                _erro(ErroOcorrencia.coordenadaInvalida)!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              )
            : null,
      ),
      // Fora do ListTile: com texto ampliado o botão não cabe como `trailing`.
      Align(
        alignment: Alignment.centerLeft,
        child: OutlinedButton.icon(
          onPressed: _localizando ? null : _usarMinhaLocalizacao,
          icon: _localizando
              ? const SizedBox.square(
                  dimension: 18,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Icon(Icons.gps_fixed),
          label: Text(_localizando ? t.obtendoLocalizacao : t.usarMinhaLocalizacao),
        ),
      ),
    ];
  }

  Widget _secaoEnvolvidos() {
    final t = context.textos;
    return CartaoSecao(
      titulo: t.secaoEnvolvidos,
      icone: Icons.people_outline,
      acao: IconButton.filledTonal(
        key: const Key('ocorrencia.adicionarEnvolvido'),
        tooltip: t.adicionarEnvolvido,
        icon: const Icon(Icons.person_add_alt),
        onPressed: _adicionarEnvolvido,
      ),
      filhos: [
        if (_erros.contains(ErroOcorrencia.semEnvolvidos))
          Text(
            _erro(ErroOcorrencia.semEnvolvidos)!,
            style: TextStyle(color: Theme.of(context).colorScheme.error),
          ),
        for (final (i, e) in _envolvidos.indexed)
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.person_outline),
            title: Text(e.nome),
            subtitle: Text(e.tipo.rotulo(t)),
            onTap: () => _editarEnvolvido(i),
            trailing: IconButton(
              tooltip: t.remover,
              icon: const Icon(Icons.delete_outline),
              onPressed: () => setState(() => _envolvidos.removeAt(i)),
            ),
          ),
      ],
    );
  }

  Future<void> _adicionarEnvolvido() async {
    final novo = await abrirDialogoEnvolvido(context);
    if (novo != null) setState(() => _envolvidos.add(novo));
  }

  Future<void> _editarEnvolvido(int indice) async {
    final editado = await abrirDialogoEnvolvido(context, inicial: _envolvidos[indice]);
    if (editado != null) setState(() => _envolvidos[indice] = editado);
  }

  Widget _secaoTipificacoes() {
    final t = context.textos;
    return CartaoSecao(
      titulo: t.secaoTipificacoes,
      icone: Icons.gavel_outlined,
      acao: IconButton.filledTonal(
        tooltip: t.adicionarTipificacao,
        icon: const Icon(Icons.add),
        onPressed: () async {
          final nova = await abrirDialogoTipificacao(context);
          if (nova != null) setState(() => _tipificacoes.add(nova));
        },
      ),
      filhos: [
        for (final (i, tp) in _tipificacoes.indexed)
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.gavel_outlined),
            title: Text(tp.artigo),
            subtitle: Text(tp.descricao),
            trailing: IconButton(
              tooltip: t.remover,
              icon: const Icon(Icons.delete_outline),
              onPressed: () => setState(() => _tipificacoes.removeAt(i)),
            ),
          ),
      ],
    );
  }
}

import i18n from '../i18n';

const NATUREZA_MAPA: Record<string, string> = {
  // Português
  'Furto': 'furto',
  'Perda ou Extravio de Documento/Objeto': 'perda_extravio',
  'Acidente de Trânsito sem Vítima': 'acidente_sem_vitima',
  'Ameaça': 'ameaca',
  'Perturbação do Sossego': 'perturbacao_sossego',
  'Dano ao Patrimônio': 'dano_patrimonio',
  'Outro Fato Circunstanciado': 'outro',
  // Inglês
  'Theft / Larceny': 'furto',
  'Lost Document / Property': 'perda_extravio',
  'Traffic Accident (Non-Injury)': 'acidente_sem_vitima',
  'Threat': 'ameaca',
  'Disturbance of the Peace': 'perturbacao_sossego',
  'Property Damage / Vandalism': 'dano_patrimonio',
  'Other Circumstanced Incident': 'outro',
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function formatarNatureza(
  natureza: string | undefined | null,
  t?: any
): string {
  if (!natureza) return '';
  const limpo = natureza.trim();
  const chave = NATUREZA_MAPA[limpo];
  if (chave) {
    const translate = typeof t === 'function' ? t : i18n.t.bind(i18n);
    const traduzido = translate(`common:naturezas.${chave}`, { defaultValue: '' });
    if (traduzido && traduzido !== `common:naturezas.${chave}`) {
      return String(traduzido);
    }
    const traduzidoPublico = translate(`publico:registro.naturezas.${chave}`, { defaultValue: '' });
    if (traduzidoPublico && traduzidoPublico !== `publico:registro.naturezas.${chave}`) {
      return String(traduzidoPublico);
    }
  }
  return limpo;
}

export default formatarNatureza;

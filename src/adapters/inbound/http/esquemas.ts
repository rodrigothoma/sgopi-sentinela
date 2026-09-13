import { z } from "zod";

/**
 * Validação sintática das requisições (formato/tipos). A validação semântica
 * (regras de negócio) fica no domínio — ambas são necessárias.
 */
export const esquemaCoordenada = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
});

export const esquemaLogin = z.object({
  matricula: z.string().min(1).max(50),
  senha: z.string().min(1).max(200),
});

export const esquemaRegistrarOcorrencia = z.object({
  tipificacao: z.string().min(3).max(200),
  descricaoFato: z.string().min(20).max(20_000),
  gravidade: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4)]),
  endereco: z.object({
    logradouro: z.string().min(1).max(200),
    numero: z.string().max(20).optional(),
    bairro: z.string().min(1).max(100),
    cidade: z.string().min(1).max(100),
    uf: z.string().length(2),
  }),
  coordenada: esquemaCoordenada.optional(),
  envolvidos: z
    .array(
      z.object({
        nome: z.string().min(3).max(200),
        tipo: z.enum(["VITIMA", "TESTEMUNHA", "SUSPEITO"]),
        documento: z.string().max(20).optional(),
        dataNascimento: z.string().max(10).optional(),
        observacoes: z.string().max(2000).optional(),
      }),
    )
    .min(1),
  evidencias: z
    .array(z.object({ nomeArquivo: z.string().min(1).max(255), tamanhoBytes: z.number().int().nonnegative(), conteudoBase64: z.string().optional() }))
    .default([]),
});

export const esquemaValidar = z.object({ despachoAutoridade: z.string().min(1).max(5000) });
export const esquemaDevolver = z.object({ pendencias: z.string().min(10).max(5000) });
export const esquemaCorrigir = z.object({ descricaoFato: z.string().min(20).max(20_000) });

export const esquemaTelemetria = z.object({
  coordenada: esquemaCoordenada,
  recebidaEm: z.string().datetime().optional(),
});

export const esquemaDespachar = z.object({
  ocorrenciaId: z.string().min(1),
  viaturaId: z.string().min(1),
  posicaoInformada: esquemaCoordenada.optional(),
  observacao: z.string().max(1000).optional(),
});

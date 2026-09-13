import { DomainError } from "@/core/domain/shared/DomainError";
import type { Ator } from "../seguranca/Ator";
import { Acao } from "../seguranca/PoliticaAutorizacao";
import type { Autorizador } from "../seguranca/Autorizador";
import type { RepositorioUsuarios } from "../ports/outbound/Repositorios";
import type { PortaAuditoria, PortaHash } from "../ports/outbound/Infraestrutura";
import type { AutenticarUsuario, ConsultarAuditoria } from "../ports/inbound/CasosDeUso";
import type { RegistroAuditoria } from "@/core/domain/auditoria/RegistroAuditoria";

export class AutenticarUsuarioUseCase implements AutenticarUsuario {
  constructor(
    private readonly usuarios: RepositorioUsuarios,
    private readonly hash: PortaHash,
    private readonly auditoria: PortaAuditoria,
  ) {}

  async executar(matricula: string, senha: string): Promise<Ator> {
    const usuario = await this.usuarios.obterPorMatricula(matricula.trim());
    const senhaConfere = usuario !== null && usuario.senhaHash === this.hash.sha256(senha);

    if (!usuario || !senhaConfere) {
      await this.auditoria.registrar({
        atorId: matricula, atorPapel: "DESCONHECIDO", acao: "auth.login",
        recursoTipo: "sessao", recursoId: matricula, resultado: "NEGADO",
      });
      // Mensagem genérica: não revelar se a matrícula existe (enumeração de usuários).
      throw new DomainError("NAO_AUTORIZADO", "Matrícula ou senha inválidos.");
    }

    await this.auditoria.registrar({
      atorId: usuario.id, atorPapel: usuario.papel, acao: "auth.login",
      recursoTipo: "sessao", recursoId: usuario.id, resultado: "SUCESSO",
    });
    return { id: usuario.id, nome: usuario.nome, papel: usuario.papel };
  }
}

export class ConsultarAuditoriaUseCase implements ConsultarAuditoria {
  constructor(private readonly auditoria: PortaAuditoria, private readonly autorizador: Autorizador) {}

  async listar(ator: Ator, limite = 100): Promise<{ registros: RegistroAuditoria[]; integra: boolean }> {
    await this.autorizador.exigir(ator, Acao.AUDITORIA_CONSULTAR, { tipo: "auditoria", id: "*" });
    const [registros, verificacao] = await Promise.all([this.auditoria.listar(limite), this.auditoria.verificarIntegridade()]);
    return { registros, integra: verificacao.integra };
  }
}

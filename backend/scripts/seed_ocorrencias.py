"""
Seed de ocorrências policiais realistas em Alegrete-RS (RF01, RF04, RF02, DEC-02, DEC-09).
Chamado por scripts/seed.py para preparar o ambiente de demonstração da banca.
"""
from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from adapters.outbound.persistence.auditoria_sqlalchemy import AuditoriaSQLAlchemy  # noqa: E402
from adapters.outbound.persistence.ocorrencia_repositorio_sqlalchemy import (  # noqa: E402
    OcorrenciaRepositorioSQLAlchemy,
)
from adapters.outbound.persistence.ordem_despacho_repositorio_sqlalchemy import (  # noqa: E402
    OrdemDespachoRepositorioSQLAlchemy,
)
from adapters.outbound.persistence.usuario_repositorio_sqlalchemy import (  # noqa: E402
    UsuarioRepositorioSQLAlchemy,
)
from adapters.outbound.persistence.viatura_repositorio_sqlalchemy import (  # noqa: E402
    ViaturaRepositorioSQLAlchemy,
)
from domain.auditoria.entity import RegistroAuditoria  # noqa: E402
from domain.despacho.entity import OrdemDeDespacho  # noqa: E402
from domain.ocorrencia.entity import (  # noqa: E402
    Envolvido,
    Ocorrencia,
    TipificacaoPenal,
    TipoEnvolvido,
)
from domain.shared.geo import Coordenada  # noqa: E402
from infrastructure.database.connection import AsyncSessionLocal  # noqa: E402
from infrastructure.database.models import (  # noqa: E402
    OcorrenciaModel,
    OrdemDespachoModel,
    SequenciaOrdemDespachoModel,
    SequenciaProtocoloModel,
)


async def semear_ocorrencias() -> None:
    agora = datetime.now(UTC)
    ano_atual = agora.year

    async with AsyncSessionLocal() as session:
        user_repo = UsuarioRepositorioSQLAlchemy(session)
        vtr_repo = ViaturaRepositorioSQLAlchemy(session)
        ocorrencia_repo = OcorrenciaRepositorioSQLAlchemy(session)
        despacho_repo = OrdemDespachoRepositorioSQLAlchemy(session)
        auditoria_repo = AuditoriaSQLAlchemy(session)

        agente = await user_repo.buscar_por_login("agente")
        delegado = await user_repo.buscar_por_login("delegado")
        operador = await user_repo.buscar_por_login("operador")

        if not (agente and delegado and operador):
            print("  ! Usuários padrão não encontrados. Execute semear_usuarios primeiro.")
            return

        vtr_02 = await vtr_repo.buscar_por_prefixo("VTR-02")

        # ------------------------------------------------------------------
        # 1. Ocorrência AGUARDANDO_REVISAO (Para demonstrar validação pelo Delegado)
        # ------------------------------------------------------------------
        p1 = f"SGOPI-{ano_atual}-000001"
        res1 = await session.execute(select(OcorrenciaModel).where(OcorrenciaModel.numero_protocolo == p1))
        if res1.scalar_one_or_none():
            print(f"  = ocorrência '{p1}' já existe")
        else:
            criada_em1 = agora - timedelta(hours=2)
            oc1 = Ocorrencia.registrar(
                agente_policial_id=agente.id,
                natureza="Furto",
                descricao="Furto de bicicleta aro 29 e aparelho celular ocorrido na Praça Getúlio Vargas enquanto a vítima caminhava.",
                localizacao="Praça Getúlio Vargas, Centro, Alegrete - RS",
                coordenada=Coordenada(latitude=-29.7836, longitude=-55.7940),
                data_hora_fato=criada_em1 - timedelta(minutes=45),
                numero_protocolo=p1,
                agora=criada_em1,
                envolvidos=[
                    Envolvido(
                        nome="Maria Silveira da Silva",
                        tipo=TipoEnvolvido.VITIMA,
                        documento="123.456.789-09",
                        email="maria.silveira@email.com",
                        telefone="(55) 99911-2233",
                    ),
                    Envolvido(
                        nome="Maria Silveira da Silva",
                        tipo=TipoEnvolvido.COMUNICANTE,
                        documento="123.456.789-09",
                        email="maria.silveira@email.com",
                        telefone="(55) 99911-2233",
                    ),
                ],
                tipificacoes=[
                    TipificacaoPenal(
                        artigo="Art. 155, CP",
                        descricao="Subtrair, para si ou para outrem, coisa alheia móvel (Furto Simples)",
                    )
                ],
            )
            await ocorrencia_repo.salvar(oc1)
            await auditoria_repo.registrar(
                RegistroAuditoria(
                    quem=agente.id,
                    quando=criada_em1,
                    operacao="REGISTRO_OCORRENCIA",
                    entidade="ocorrencias",
                    entidade_id=str(oc1.id),
                    dados_depois={"numero_protocolo": p1, "status": "AGUARDANDO_REVISAO"},
                    ip="127.0.0.1",
                )
            )
            print(f"  + ocorrência '{p1}' (AGUARDANDO_REVISAO) - Pronta para Triagem do Delegado")

        # ------------------------------------------------------------------
        # 2. Ocorrência VALIDADA (Para demonstrar despacho tático no mapa Leaflet)
        # ------------------------------------------------------------------
        p2 = f"SGOPI-{ano_atual}-000002"
        res2 = await session.execute(select(OcorrenciaModel).where(OcorrenciaModel.numero_protocolo == p2))
        if res2.scalar_one_or_none():
            print(f"  = ocorrência '{p2}' já existe")
        else:
            criada_em2 = agora - timedelta(hours=3)
            oc2 = Ocorrencia.registrar(
                agente_policial_id=agente.id,
                natureza="Roubo a Estabelecimento Comercial",
                descricao="Assalto a mão armada em farmácia na Av. Tiaraju. Dois suspeitos subtraíram valores do caixa e fugiram.",
                localizacao="Av. Tiaraju, 1250, Alegrete - RS",
                coordenada=Coordenada(latitude=-29.7950, longitude=-55.7850),
                data_hora_fato=criada_em2 - timedelta(minutes=30),
                numero_protocolo=p2,
                agora=criada_em2,
                envolvidos=[
                    Envolvido(
                        nome="Carlos Eduardo Mendes",
                        tipo=TipoEnvolvido.VITIMA,
                        documento="234.567.890-92",
                        email="gerente.farmacia@email.com",
                        telefone="(55) 99888-4455",
                    ),
                    Envolvido(
                        nome="Indivíduo não identificado",
                        tipo=TipoEnvolvido.SUSPEITO,
                        documento=None,
                    ),
                ],
                tipificacoes=[
                    TipificacaoPenal(
                        artigo="Art. 157, CP",
                        descricao="Subtrair coisa móvel alheia com grave ameaça com arma de fogo",
                    )
                ],
            )
            validada_em2 = criada_em2 + timedelta(minutes=20)
            oc2.validar(delegado.id, em=validada_em2)
            await ocorrencia_repo.salvar(oc2)
            await auditoria_repo.registrar(
                RegistroAuditoria(
                    quem=delegado.id,
                    quando=validada_em2,
                    operacao="HOMOLOGACAO_OCORRENCIA",
                    entidade="ocorrencias",
                    entidade_id=str(oc2.id),
                    dados_depois={"numero_protocolo": p2, "status": "VALIDADA", "hash": oc2.hash_narrativa},
                    ip="127.0.0.1",
                )
            )
            print(f"  + ocorrência '{p2}' (VALIDADA) - Pronta para Despacho Tático")

        # ------------------------------------------------------------------
        # 3. Ocorrência EM_ATENDIMENTO (Com viatura VTR-02 despachada)
        # ------------------------------------------------------------------
        p3 = f"SGOPI-{ano_atual}-000003"
        res3 = await session.execute(select(OcorrenciaModel).where(OcorrenciaModel.numero_protocolo == p3))
        if res3.scalar_one_or_none():
            print(f"  = ocorrência '{p3}' já existe")
        else:
            criada_em3 = agora - timedelta(hours=4)
            oc3 = Ocorrencia.registrar(
                agente_policial_id=agente.id,
                natureza="Acidente de Trânsito com Lesão Corporal",
                descricao="Colisão transversal entre automóvel e moto na Rua dos Andradas esquina com Vasco Alves com danos materiais.",
                localizacao="Rua dos Andradas, Centro, Alegrete - RS",
                coordenada=Coordenada(latitude=-29.7880, longitude=-55.7910),
                data_hora_fato=criada_em3 - timedelta(minutes=20),
                numero_protocolo=p3,
                agora=criada_em3,
                envolvidos=[
                    Envolvido(
                        nome="Juliana Fagundes de Oliveira",
                        tipo=TipoEnvolvido.VITIMA,
                        documento="345.678.901-75",
                        telefone="(55) 99777-1122",
                    ),
                    Envolvido(
                        nome="Paulo Roberto Soares",
                        tipo=TipoEnvolvido.TESTEMUNHA,
                        documento="456.789.012-49",
                    ),
                ],
                tipificacoes=[
                    TipificacaoPenal(
                        artigo="Art. 303, CTB",
                        descricao="Praticar lesão corporal culposa na direção de veículo automotor",
                    )
                ],
            )
            validada_em3 = criada_em3 + timedelta(minutes=10)
            oc3.validar(delegado.id, em=validada_em3)
            despachada_em3 = validada_em3 + timedelta(minutes=5)
            oc3.despachar(operador.id, em=despachada_em3)
            await ocorrencia_repo.salvar(oc3)

            # Ordem de despacho ativa
            od_num = f"OD-{ano_atual}-000001"
            res_od = await session.execute(select(OrdemDespachoModel).where(OrdemDespachoModel.numero == od_num))
            if not res_od.scalar_one_or_none() and vtr_02:
                ordem = OrdemDeDespacho(
                    numero=od_num,
                    ocorrencia_id=oc3.id,
                    viatura_id=vtr_02.id,
                    operador_id=operador.id,
                    criada_em=despachada_em3,
                    observacoes="Viatura VTR-02 designada para prestar socorro e isolar local do sinistro.",
                    ativa=True,
                )
                await despacho_repo.salvar(ordem)
                await auditoria_repo.registrar(
                    RegistroAuditoria(
                        quem=operador.id,
                        quando=despachada_em3,
                        operacao="DESPACHO_VIATURA",
                        entidade="ordens_despacho",
                        entidade_id=str(ordem.id),
                        dados_depois={"numero": od_num, "viatura": "VTR-02", "ocorrencia": p3},
                        ip="127.0.0.1",
                    )
                )
            print(f"  + ocorrência '{p3}' (EM_ATENDIMENTO) - VTR-02 despachada ({od_num})")

        # ------------------------------------------------------------------
        # 4. Ocorrência ENCERRADA (Ciclo de vida completo com desfecho)
        # ------------------------------------------------------------------
        p4 = f"SGOPI-{ano_atual}-000004"
        res4 = await session.execute(select(OcorrenciaModel).where(OcorrenciaModel.numero_protocolo == p4))
        if res4.scalar_one_or_none():
            print(f"  = ocorrência '{p4}' já existe")
        else:
            criada_em4 = agora - timedelta(days=1)
            oc4 = Ocorrencia.registrar(
                agente_policial_id=agente.id,
                natureza="Perturbação da Tranquilidade Pública",
                descricao="Emissão reiterada de som excessivo em residência na Cidade Alta perturbando o repouso da vizinhança.",
                localizacao="Rua Barão do Cerro Largo, Cidade Alta, Alegrete - RS",
                coordenada=Coordenada(latitude=-29.7750, longitude=-55.8010),
                data_hora_fato=criada_em4 - timedelta(hours=1),
                numero_protocolo=p4,
                agora=criada_em4,
                envolvidos=[
                    Envolvido(
                        nome="Luciana Dornelles",
                        tipo=TipoEnvolvido.VITIMA,
                        documento="567.890.123-03",
                        telefone="(55) 99666-3344",
                    ),
                    Envolvido(
                        nome="Marcos Vinicius Ribeiro",
                        tipo=TipoEnvolvido.SUSPEITO,
                        documento="RS-10.987.654",
                    ),
                ],
                tipificacoes=[
                    TipificacaoPenal(
                        artigo="Art. 42, LCP",
                        descricao="Perturbar alguém o trabalho ou o sossego alheios com algazarra",
                    )
                ],
            )
            oc4.validar(delegado.id, em=criada_em4 + timedelta(minutes=15))
            oc4.despachar(operador.id, em=criada_em4 + timedelta(minutes=20))
            encerrada_em4 = criada_em4 + timedelta(hours=1, minutes=30)
            oc4.encerrar(
                operador.id,
                desfecho="Guarnição compareceu ao local. Proprietário advertido verbalmente, desligou o aparelho sonoro imediatamente.",
                em=encerrada_em4,
            )
            await ocorrencia_repo.salvar(oc4)
            await auditoria_repo.registrar(
                RegistroAuditoria(
                    quem=operador.id,
                    quando=encerrada_em4,
                    operacao="ENCERRAMENTO_OCORRENCIA",
                    entidade="ocorrencias",
                    entidade_id=str(oc4.id),
                    dados_depois={"numero_protocolo": p4, "status": "ENCERRADA"},
                    ip="127.0.0.1",
                )
            )
            print(f"  + ocorrência '{p4}' (ENCERRADA) - Histórico completo")

        # ------------------------------------------------------------------
        # 5. Ocorrência EM_CORRECAO (Para demonstrar devolução formal com justificativa)
        # ------------------------------------------------------------------
        p5 = f"SGOPI-{ano_atual}-000005"
        res5 = await session.execute(select(OcorrenciaModel).where(OcorrenciaModel.numero_protocolo == p5))
        if res5.scalar_one_or_none():
            print(f"  = ocorrência '{p5}' já existe")
        else:
            criada_em5 = agora - timedelta(hours=5)
            oc5 = Ocorrencia.registrar(
                agente_policial_id=agente.id,
                natureza="Dano ao Patrimônio Público",
                descricao="Pichação constatada no muro lateral de prédio público na Av. Assis Brasil durante ronda preventiva.",
                localizacao="Av. Assis Brasil, Alegrete - RS",
                coordenada=Coordenada(latitude=-29.7910, longitude=-55.7890),
                data_hora_fato=criada_em5 - timedelta(minutes=40),
                numero_protocolo=p5,
                agora=criada_em5,
                envolvidos=[
                    Envolvido(
                        nome="Vigilante Noturno",
                        tipo=TipoEnvolvido.COMUNICANTE,
                        documento="RS-20.987.654",
                    ),
                ],
                tipificacoes=[
                    TipificacaoPenal(
                        artigo="Art. 163, CP",
                        descricao="Destruir, inutilizar ou deteriorar coisa alheia (Dano contra patrimônio público)",
                    )
                ],
            )
            devolvida_em5 = criada_em5 + timedelta(minutes=25)
            oc5.devolver_para_correcao(
                delegado.id,
                justificativa="Necessário qualificar testemunhas que presenciaram o fato e detalhar ponto de referência exato.",
                em=devolvida_em5,
            )
            await ocorrencia_repo.salvar(oc5)
            await auditoria_repo.registrar(
                RegistroAuditoria(
                    quem=delegado.id,
                    quando=devolvida_em5,
                    operacao="DEVOLUCAO_CORRECAO",
                    entidade="ocorrencias",
                    entidade_id=str(oc5.id),
                    dados_depois={"numero_protocolo": p5, "status": "EM_CORRECAO"},
                    ip="127.0.0.1",
                )
            )
            print(f"  + ocorrência '{p5}' (EM_CORRECAO) - Justificativa do delegado registrada")

        # ------------------------------------------------------------------
        # Sincronização dos contadores sequenciais
        # ------------------------------------------------------------------
        seq_prot = await session.execute(
            select(SequenciaProtocoloModel).where(SequenciaProtocoloModel.ano == ano_atual)
        )
        row_prot = seq_prot.scalar_one_or_none()
        if not row_prot:
            session.add(SequenciaProtocoloModel(ano=ano_atual, ultimo=5))
        elif row_prot.ultimo < 5:
            row_prot.ultimo = 5

        seq_od = await session.execute(
            select(SequenciaOrdemDespachoModel).where(SequenciaOrdemDespachoModel.ano == ano_atual)
        )
        row_od = seq_od.scalar_one_or_none()
        if not row_od:
            session.add(SequenciaOrdemDespachoModel(ano=ano_atual, ultimo=1))
        elif row_od.ultimo < 1:
            row_od.ultimo = 1

        await session.commit()

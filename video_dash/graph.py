import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

def calcular_banda_disponivel(t):
    """Retorna a banda configurada no experimento.sh (em kbps) para o segundo t."""
    if t <= 30:
        return 5000
    elif t <= 60:
        return 1000
    elif t <= 90:
        return 300
    else:
        return 5000

def carregar_e_limpar(caminho_csv, limite_s=120):
    df = pd.read_csv(caminho_csv)
    df = df[df['tempo_s'] <= limite_s].copy()
    df['em_stall'] = df['buffer_s'].isna()
    df['buffer_limpo'] = df['buffer_s'].fillna(0.0)
    df['banda_kbps'] = df['tempo_s'].apply(calcular_banda_disponivel)
    return df

def calcular_metricas(df, nome):
    """
    Calcula métricas individuais e QoE (modelo linear clássico MPC/Pensieve):
    QoE = sum(R_t) - 4.3 * T_stall - 1.0 * sum(|R_t - R_{t-1}|)
    onde R_t está em Mbps e T_stall é o total de segundos travados.
    """
    bitrate_mbps = df['bitrate_kbps'] / 1000.0
    soma_bitrate = bitrate_mbps.sum()
    tempo_travado = int(df['em_stall'].sum())
    trocas = int((df['bitrate_kbps'].diff().fillna(0) != 0).sum())
    instabilidade = bitrate_mbps.diff().abs().fillna(0).sum()

    qoe_total = soma_bitrate - (4.3 * tempo_travado) - (1.0 * instabilidade)
    qoe_medio = qoe_total / len(df)

    return {
        'Algoritmo': nome,
        'Bitrate Médio (kbps)': round(df['bitrate_kbps'].mean(), 1),
        'Buffer Médio (s)': round(df['buffer_limpo'].mean(), 2),
        'Eventos Travamento': int(df['travamentos'].max()),
        'Tempo Travado (s)': tempo_travado,
        'Trocas de Qualidade': trocas,
        'QoE Total': round(qoe_total, 2),
        'QoE Médio (/s)': round(qoe_medio, 3),
    }

def gerar_comparativo(csv_throughput, csv_bola):
    df_thr = carregar_e_limpar(csv_throughput)
    df_bola = carregar_e_limpar(csv_bola)

    fases = [
        (0, 30, "Fase 1\n5 Mbit/s", "#e8f5e9"),
        (30, 60, "Fase 2\n1 Mbit/s", "#fff8e1"),
        (60, 90, "Fase 3\n300 kbit/s + 100ms", "#ffebee"),
        (90, 120, "Fase 4\n5 Mbit/s", "#e3f2fd"),
    ]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8.5), sharex=True)
    fig.suptitle("Comparação de Algoritmos ABR (Vazão vs. BOLA) sob Banda Variável",
                 fontsize=14, fontweight='bold')

    for ax in (ax1, ax2):
        for inicio, fim, _, cor in fases:
            ax.axvspan(inicio, fim, color=cor, alpha=0.45, zorder=0)
            if inicio > 0:
                ax.axvline(inicio, color='gray', linestyle='--', linewidth=1, alpha=0.6)
        ax.grid(True, linestyle=':', alpha=0.6)

    # --- GRÁFICO 1: Banda Disponível + Bitrate (Vazão vs BOLA) ---
    ax1.step(df_thr['tempo_s'], df_thr['banda_kbps'], where='post',
             color='#424242', linestyle='--', linewidth=1.8, alpha=0.85,
             label='Banda Disponível (tc netem)')
    ax1.step(df_thr['tempo_s'], df_thr['bitrate_kbps'], where='post',
             color='#1565c0', linewidth=2.2, label='Bitrate — ABR Vazão (Throughput)')
    ax1.step(df_bola['tempo_s'], df_bola['bitrate_kbps'], where='post',
             color='#e65100', linewidth=2.2, linestyle='-.', label='Bitrate — ABR BOLA (Buffer)')

    ax1.set_ylabel("Taxa de Bits (kbps)", fontweight='bold')
    ax1.set_yticks([500, 1000, 1500, 3000, 5000])
    ax1.set_yticklabels(["500 (360p)", "1000", "1500 (720p)", "3000 (1080p)", "5000"])
    ax1.set_ylim(0, 6000)
    ax1.legend(loc='center right', fontsize=9)

    for inicio, fim, nome, _ in fases:
        ax1.text((inicio + fim) / 2, 5650, nome, ha='center', va='top',
                 fontsize=9, fontweight='bold', color='#333333')

    # --- GRÁFICO 2: Nível do Buffer e Travamentos (Vazão vs BOLA) ---
    ax2.plot(df_thr['tempo_s'], df_thr['buffer_limpo'],
             color='#1565c0', linewidth=2, label='Buffer — ABR Vazão (s)')
    ax2.plot(df_bola['tempo_s'], df_bola['buffer_limpo'],
             color='#e65100', linewidth=2, linestyle='-.', label='Buffer — ABR BOLA (s)')

    # Marca os eventos de travamento de cada algoritmo
    trav_thr = df_thr[df_thr['travamentos'].diff().fillna(0) > 0]
    trav_bola = df_bola[df_bola['travamentos'].diff().fillna(0) > 0]

    if not trav_thr.empty:
        ax2.scatter(trav_thr['tempo_s'], trav_thr['buffer_limpo'],
                    color='#1565c0', marker='X', s=85, zorder=5, label='Travamento (Vazão)')
    if not trav_bola.empty:
        ax2.scatter(trav_bola['tempo_s'], trav_bola['buffer_limpo'],
                    color='#e65100', marker='X', s=85, zorder=5, label='Travamento (BOLA)')

    max_buf = max(df_thr['buffer_limpo'].max(), df_bola['buffer_limpo'].max())
    ax2.set_xlabel("Tempo do Experimento (segundos)", fontweight='bold')
    ax2.set_ylabel("Buffer (segundos)", fontweight='bold')
    ax2.set_xlim(0, 120)
    ax2.set_ylim(-0.5, max_buf * 1.22)
    ax2.legend(loc='upper right', fontsize=9, ncol=2)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    # Extrai série e episódio do nome do CSV (ex: metricas_mecanimais_ep5_abrThroughput.csv -> mecanimais_ep5)
    nome_base = os.path.splitext(os.path.basename(csv_throughput))[0]
    identificador = (
        nome_base
        .replace("metricas_", "")
        .replace("_abrThroughput", "")
        .replace("_abrBola", "")
    )
    saida = f"grafico_comparativo_{identificador}.png"
    plt.savefig(saida, dpi=300)
    print(f"\nGráfico comparativo salvo em: {saida}\n")

    # Tabela resumo para o relatório
    resumo = pd.DataFrame([
        calcular_metricas(df_thr, "ABR Vazão (Throughput)"),
        calcular_metricas(df_bola, "ABR BOLA (Buffer)")
    ])
    print("=== RESUMO COMPARATIVO PARA O RELATÓRIO ===")
    print(resumo.to_string(index=False))
    print("\nFórmula de QoE usada (MPC/Pensieve): QoE = Σ(Bitrate_Mbps) - 4.3*(Tempo_Travado_s) - 1.0*Σ(|ΔBitrate_Mbps|)")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python3 gerar_graficos.py <csv_throughput> <csv_bola>")
        print("Exemplo: python3 gerar_graficos.py metricas_mecanimais_ep5_abrThroughput.csv metricas_mecanimais_ep5_abrBola.csv")
        sys.exit(1)

    gerar_comparativo(sys.argv[1], sys.argv[2])

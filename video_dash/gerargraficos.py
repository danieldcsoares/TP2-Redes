import sys
import os
import pandas as pd
import matplotlib.pyplot as plt

def gerar_graficos(caminho_csv):
    # Lê o CSV e trata valores NaN no buffer (congelamento/stall) como 0
    df = pd.read_csv(caminho_csv)
    df = df[df['tempo_s'] <= 120]
    df['em_stall'] = df['buffer_s'].isna()
    df['buffer_limpo'] = df['buffer_s'].fillna(0.0)

    # Identifica os instantes exatos em que um travamento foi disparado
    eventos_travamento = df[df['travamentos'].diff().fillna(0) > 0]

    # Definição das fases do experimento.sh (ajuste aqui se alterar os tempos)
    fases = [
        (0, 30, "Fase 1\n5 Mbit/s", "#e8f5e9"),
        (30, 60, "Fase 2\n1 Mbit/s", "#fff8e1"),
        (60, 90, "Fase 3\n300 kbit/s + 100ms", "#ffebee"),
        (90, 120, "Fase 4\n5 Mbit/s", "#e3f2fd"),
    ]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    fig.suptitle("Desempenho do Streaming Adaptativo (MPEG-DASH) sob Banda Variável",
                 fontsize=14, fontweight='bold')

    max_t = df['tempo_s'].max()

    # Aplica sombreamento e linhas verticais das fases nos dois gráficos
    for ax in (ax1, ax2):
        for inicio, fim, nome, cor in fases:
            if inicio < max_t:
                ax.axvspan(inicio, min(fim, max_t), color=cor, alpha=0.5, zorder=0)
            if inicio > 0 and inicio < max_t:
                ax.axvline(inicio, color='gray', linestyle='--', linewidth=1, alpha=0.7)
        if 120 < max_t:
            ax.axvline(120, color='gray', linestyle=':', linewidth=1, alpha=0.7)
        ax.grid(True, linestyle=':', alpha=0.6)

    # --- GRÁFICO 1: Bitrate (Qualidade Adaptativa) ---
    ax1.step(df['tempo_s'], df['bitrate_kbps'], where='post',
             color='#1565c0', linewidth=2.2, label='Bitrate Selecionado')
    ax1.set_ylabel("Bitrate (kbps)", fontweight='bold')
    ax1.set_yticks([500, 1500, 3000])
    ax1.set_yticklabels(["500 (360p)", "1500 (720p)", "3000 (1080p)"])
    ax1.set_ylim(0, 4000)
    ax1.legend(loc='center right')

    # Rótulos das fases no topo do primeiro gráfico
    for inicio, fim, nome, _ in fases:
        centro = (inicio + min(fim, max_t)) / 2
        if inicio < max_t:
            ax1.text(centro, 3450, nome, ha='center', va='top',
                     fontsize=9, fontweight='bold', color='#333333')

    # --- GRÁFICO 2: Nível do Buffer e Travamentos ---
    ax2.plot(df['tempo_s'], df['buffer_limpo'],
             color='#2e7d32', linewidth=2, label='Nível do Buffer (s)')
    ax2.fill_between(df['tempo_s'], df['buffer_limpo'], color='#2e7d32', alpha=0.15)

    # Marca os eventos de BUFFER_EMPTY (travamento) com X vermelho
    if not eventos_travamento.empty:
        ax2.scatter(eventos_travamento['tempo_s'], eventos_travamento['buffer_limpo'],
                    color='#d32f2f', marker='X', s=90, zorder=5, label='Travamento (Rebuffering)')

    ax2.set_xlabel("Tempo do Experimento (segundos)", fontweight='bold')
    ax2.set_ylabel("Buffer (segundos)", fontweight='bold')
    ax2.set_xlim(0, max_t)
    ax2.set_ylim(-0.5, 21.5)
    ax2.legend(loc='upper left')

    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # Salva a imagem em alta resolução (300 DPI) pronta para o relatório
    nome_base = os.path.splitext(os.path.basename(caminho_csv))[0]
    caminho_saida = f"grafico_{nome_base}.png"
    plt.savefig(caminho_saida, dpi=300)
    print(f"Gráfico salvo com sucesso em: {caminho_saida}")

    # Imprime resumo numérico para usar na análise do relatório
    print("\n--- Resumo das Métricas ---")
    print(f"Duração total coletada: {max_t} s")
    print(f"Bitrate médio: {df['bitrate_kbps'].mean():.1f} kbps")
    print(f"Buffer médio: {df['buffer_limpo'].mean():.2f} s (máx: {df['buffer_limpo'].max():.2f} s)")
    print(f"Total de travamentos (BUFFER_EMPTY): {df['travamentos'].max()}")
    print(f"Tempo congelado (buffer zerado/NaN): {df['em_stall'].sum()} s")
    print(f"Trocas de qualidade: {(df['bitrate_kbps'].diff().fillna(0) != 0).sum()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 gerar_graficos.py <caminho_do_csv>")
        print("Exemplo: python3 gerar_graficos.py metricas_mecanimais_ep5.csv")
        sys.exit(1)

    gerar_graficos(sys.argv[1])
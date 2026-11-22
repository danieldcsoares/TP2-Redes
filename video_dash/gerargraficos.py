"""
Compara os algoritmos de ABR (Vazão x BOLA) a partir dos CSVs exportados pelo player.

Aceita uma ou mais execuções por algoritmo e reporta média ± desvio padrão.

Uso:
    python3 gerargraficos.py --vazao run1.csv run2.csv run3.csv --bola run1.csv run2.csv run3.csv

Exemplo (com glob, o shell expande os arquivos):
    python3 gerargraficos.py \
        --vazao metricas_*_abrThroughput_run*.csv \
        --bola  metricas_*_abrBola_run*.csv
"""
import argparse
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DURACAO_S = 120      # duração do experimento.sh
PESO_STALL = 4.3     # peso do tempo sem buffer no QoE (MPC/Pensieve)
PESO_TROCA = 1.0     # peso da instabilidade de bitrate no QoE

COR_VAZAO = "#1565c0"
COR_BOLA = "#e65100"

FASES = [
    (0, 30, "Fase 1\n5 Mbit/s", "#e8f5e9"),
    (30, 60, "Fase 2\n1 Mbit/s", "#fff8e1"),
    (60, 90, "Fase 3\n300 kbit/s + 100ms", "#ffebee"),
    (90, 120, "Fase 4\n5 Mbit/s", "#e3f2fd"),
]


def banda_disponivel(t):
    """Banda configurada no experimento.sh (kbps) no segundo t."""
    if t <= 30:
        return 5000
    if t <= 60:
        return 1000
    if t <= 90:
        return 300
    return 5000


def carregar(caminho_csv, limite_s=DURACAO_S):
    df = pd.read_csv(caminho_csv)
    df = df[df["tempo_s"] <= limite_s].sort_values("tempo_s").reset_index(drop=True)
    df["sem_buffer"] = df["buffer_s"].isna()
    df["buffer_limpo"] = df["buffer_s"].fillna(0.0)
    return df


def atraso_inicial(df):
    """Segundos iniciais sem buffer, até a reprodução começar (linhas NaN antes da 1ª leitura válida)."""
    validos = df.index[~df["sem_buffer"]]
    return len(df) if len(validos) == 0 else int(validos[0])


def calcular_metricas(df):
    """
    QoE linear (MPC/Pensieve):
        QoE = sum(R_t) - 4.3 * T_sem_buffer - 1.0 * sum(|R_t - R_{t-1}|)
    com R_t em Mbit/s. T_sem_buffer = atraso inicial + tempo travado, como no cálculo original,
    mas os dois são reportados separadamente.
    """
    bitrate_mbps = df["bitrate_kbps"] / 1000.0
    sem_buffer = int(df["sem_buffer"].sum())
    inicial = atraso_inicial(df)
    instabilidade = bitrate_mbps.diff().abs().fillna(0).sum()
    qoe_total = bitrate_mbps.sum() - PESO_STALL * sem_buffer - PESO_TROCA * instabilidade

    return {
        "Bitrate médio (kbps)": df["bitrate_kbps"].mean(),
        "Buffer médio (s)": df["buffer_limpo"].mean(),
        "Atraso inicial (s)": inicial,
        "Tempo travado (s)": sem_buffer - inicial,
        "Eventos de travamento": int(df["travamentos"].max()),
        "Trocas de qualidade": int((df["bitrate_kbps"].diff().fillna(0) != 0).sum()),
        "QoE total": qoe_total,
        "QoE médio (/s)": qoe_total / len(df),
    }


def resumir(execucoes):
    """DataFrame com uma linha por execução."""
    return pd.DataFrame([calcular_metricas(df) for df in execucoes])


def media_desvio(tabela):
    media = tabela.mean()
    desvio = tabela.std(ddof=1) if len(tabela) > 1 else pd.Series(0.0, index=tabela.columns)
    return media, desvio


def formatar(valor, desvio, casas):
    texto = f"{valor:.{casas}f}"
    return f"{texto} ± {desvio:.{casas}f}" if desvio is not None else texto


def serie(execucoes, coluna):
    """Matriz (tempo x execução) de uma coluna, alinhada em 1..DURACAO_S."""
    return pd.concat(
        [d.set_index("tempo_s")[coluna].reindex(range(1, DURACAO_S + 1)) for d in execucoes],
        axis=1,
    )


def escada_de_qualidades(*grupos):
    """Descobre bitrate -> resolução a partir dos próprios CSVs (vem do manifesto)."""
    pares = pd.concat([d[["bitrate_kbps", "resolucao"]] for g in grupos for d in g])
    pares = pares[pares["bitrate_kbps"] > 0]
    return (
        pares.groupby("bitrate_kbps")["resolucao"]
        .agg(lambda s: s.mode().iloc[0])
        .sort_index()
        .to_dict()
    )


def identificador(caminho_csv):
    nome = os.path.splitext(os.path.basename(caminho_csv))[0]
    nome = nome.replace("metricas_", "")
    nome = re.sub(r"_abr(Throughput|Bola)", "", nome)
    nome = re.sub(r"_run\d+", "", nome)
    return nome


def plotar(vazao, bola, saida):
    n_v, n_b = len(vazao), len(bola)
    escada = escada_de_qualidades(vazao, bola)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 8.5), sharex=True)
    sufixo = f" (média de {n_v} e {n_b} execuções)" if max(n_v, n_b) > 1 else ""
    fig.suptitle("Comparação de Algoritmos ABR (Vazão vs. BOLA) sob Banda Variável" + sufixo,
                 fontsize=14, fontweight="bold")

    for ax in (ax1, ax2):
        for inicio, fim, _, cor in FASES:
            ax.axvspan(inicio, fim, color=cor, alpha=0.45, zorder=0)
            if inicio > 0:
                ax.axvline(inicio, color="gray", linestyle="--", linewidth=1, alpha=0.6)
        ax.grid(True, linestyle=":", alpha=0.6)

    tempo = np.arange(1, DURACAO_S + 1)

    # --- Gráfico 1: banda disponível e bitrate escolhido ---
    ax1.step(tempo, [banda_disponivel(t) for t in tempo], where="post", color="#424242",
             linestyle="--", linewidth=1.8, alpha=0.85, label="Banda disponível (tc netem)")

    for execs, cor, estilo, nome in (
        (vazao, COR_VAZAO, "-", "Vazão"),
        (bola, COR_BOLA, "-.", "BOLA"),
    ):
        m = serie(execs, "bitrate_kbps")
        if len(execs) > 1:
            for c in m.columns:
                ax1.step(tempo, m[c], where="post", color=cor, linewidth=0.8, alpha=0.25)
        rotulo = f"Bitrate — ABR {nome}" + (" (média)" if len(execs) > 1 else "")
        ax1.step(tempo, m.mean(axis=1), where="post", color=cor, linestyle=estilo,
                 linewidth=2.2, label=rotulo)

    ticks = sorted(escada) + [5000]
    labels = [f"{b} ({escada[b]})" for b in sorted(escada)] + ["5000"]
    ax1.set_yticks(ticks)
    ax1.set_yticklabels(labels)
    ax1.set_ylabel("Taxa de bits (kbps)", fontweight="bold")
    ax1.set_ylim(0, 6000)
    ax1.legend(loc="center right", fontsize=9)
    for inicio, fim, nome, _ in FASES:
        ax1.text((inicio + fim) / 2, 5650, nome, ha="center", va="top",
                 fontsize=9, fontweight="bold", color="#333333")

    # --- Gráfico 2: nível do buffer (média ± desvio) e travamentos ---
    max_buf = 0.0
    for execs, cor, estilo, nome in (
        (vazao, COR_VAZAO, "-", "Vazão"),
        (bola, COR_BOLA, "-.", "BOLA"),
    ):
        m = serie(execs, "buffer_limpo")
        media = m.mean(axis=1)
        desvio = m.std(axis=1, ddof=1).fillna(0) if len(execs) > 1 else pd.Series(0.0, index=m.index)
        ax2.plot(tempo, media, color=cor, linestyle=estilo, linewidth=2,
                 label=f"Buffer — ABR {nome}" + (" (média ± dp)" if len(execs) > 1 else " (s)"))
        if len(execs) > 1:
            ax2.fill_between(tempo, (media - desvio).clip(lower=0), media + desvio,
                             color=cor, alpha=0.18, linewidth=0)
        max_buf = max(max_buf, float((media + desvio).max()))

        marcou = False
        for d in execs:
            ev = d[d["travamentos"].diff().fillna(0) > 0]
            if not ev.empty:
                ax2.scatter(ev["tempo_s"], ev["buffer_limpo"], color=cor, marker="X", s=70,
                            zorder=5, alpha=0.8, label=None if marcou else f"Travamento ({nome})")
                marcou = True

    ax2.set_xlabel("Tempo do experimento (segundos)", fontweight="bold")
    ax2.set_ylabel("Buffer (segundos)", fontweight="bold")
    ax2.set_xlim(0, DURACAO_S)
    ax2.set_ylim(-0.5, max(max_buf, 1) * 1.22)
    ax2.legend(loc="upper right", fontsize=9, ncol=2)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(saida, dpi=300)
    plt.close(fig)


def imprimir_resultados(vazao, bola, saida_csv):
    tab_v, tab_b = resumir(vazao), resumir(bola)
    casas = {"Bitrate médio (kbps)": 1, "Buffer médio (s)": 2, "Atraso inicial (s)": 1,
             "Tempo travado (s)": 1, "Eventos de travamento": 1, "Trocas de qualidade": 1,
             "QoE total": 2, "QoE médio (/s)": 3}
    mv, dv = media_desvio(tab_v)
    mb, db = media_desvio(tab_b)
    multi = len(vazao) > 1 or len(bola) > 1

    print(f"\n=== RESULTADOS ({len(vazao)} execução(ões) Vazão, {len(bola)} BOLA) ===\n")
    print("| Métrica | ABR Vazão | ABR BOLA |")
    print("| --- | --- | --- |")
    for col, c in casas.items():
        va = formatar(mv[col], dv[col] if multi else None, c)
        vb = formatar(mb[col], db[col] if multi else None, c)
        print(f"| {col} | {va} | {vb} |")
    if multi:
        print("\n(valores: média ± desvio padrão amostral entre execuções)")

    print("\n--- Por execução ---")
    todas = pd.concat([tab_v.assign(Algoritmo="Vazão", Execução=range(1, len(tab_v) + 1)),
                       tab_b.assign(Algoritmo="BOLA", Execução=range(1, len(tab_b) + 1))])
    cols = ["Algoritmo", "Execução"] + list(casas)
    print(todas[cols].round(2).to_string(index=False))
    todas[cols].round(4).to_csv(saida_csv, index=False)
    print(f"\nTabela por execução salva em: {saida_csv}")
    print("\nQoE = Σ(Bitrate_Mbps) − 4,3·(segundos sem buffer) − 1,0·Σ|ΔBitrate_Mbps|"
          "\n'Tempo travado' exclui o atraso inicial; os dois somam o que o QoE penaliza.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vazao", nargs="+", required=True, help="CSVs do ABR por vazão (1 ou mais)")
    ap.add_argument("--bola", nargs="+", required=True, help="CSVs do ABR BOLA (1 ou mais)")
    ap.add_argument("--saida", help="nome do PNG (padrão: grafico_comparativo_<id>.png)")
    args = ap.parse_args()

    vazao = [carregar(c) for c in args.vazao]
    bola = [carregar(c) for c in args.bola]

    ident = identificador(args.vazao[0])
    png = args.saida or f"grafico_comparativo_{ident}.png"
    plotar(vazao, bola, png)
    print(f"Gráfico salvo em: {png}")
    imprimir_resultados(vazao, bola, f"resumo_metricas_{ident}.csv")


if __name__ == "__main__":
    sys.exit(main())

import os
import sys
import json
import requests

OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
MODELO_EMBED = "bge-m3"

def gerar_embedding(texto):
    resposta = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": MODELO_EMBED, "input": texto}
    )
    resposta.raise_for_status()
    return resposta.json()["embeddings"][0]

def indexar_episodio(pasta_episodio):
    caminho_transcript = os.path.join(pasta_episodio, "transcript.json")
    caminho_index = os.path.join(pasta_episodio, "index.json")

    if not os.path.exists(caminho_transcript):
        print(f"❌ Erro: '{caminho_transcript}' não encontrado. Rode gerarcapitulos.py primeiro.")
        sys.exit(1)

    with open(caminho_transcript, "r", encoding="utf-8") as f:
        segmentos = json.load(f)

    # Agrupa de 3 em 3 falas (com sobreposição de 1) para manter o contexto da frase
    blocos = []
    passo = 2
    janela = 3
    for i in range(0, len(segmentos), passo):
        grupo = segmentos[i : i + janela]
        if not grupo:
            break
        texto_bloco = " ".join(s["text"] for s in grupo).strip()
        blocos.append({
            "time": grupo[0]["start"],
            "text": texto_bloco
        })

    print(f"🔎 Indexando {len(blocos)} blocos de fala em {pasta_episodio} com {MODELO_EMBED}...")

    indice = []
    for idx, bloco in enumerate(blocos, 1):
        vetor = gerar_embedding(bloco["text"])
        indice.append({
            "time": bloco["time"],
            "text": bloco["text"],
            "embedding": vetor
        })
        if idx % 10 == 0 or idx == len(blocos):
            print(f"   Progresso: {idx}/{len(blocos)}")

    with open(caminho_index, "w", encoding="utf-8") as f:
        json.dump(indice, f, ensure_ascii=False)

    print(f"✅ Índice salvo com sucesso em {caminho_index}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 indexar.py <desenho> <episodio>")
        print("Exemplo: python3 indexar.py peixonauta 1")
        sys.exit(1)

    desenho = sys.argv[1]
    episodio = sys.argv[2]
    if not episodio.startswith("ep"):
        episodio = f"ep{episodio}"

    indexar_episodio(os.path.join(desenho, episodio))

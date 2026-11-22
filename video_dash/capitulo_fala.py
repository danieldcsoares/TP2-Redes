import os
import sys
import json
import whisper
import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODELO_LOCAL = "qwen2.5:3b"

def processar_episodio(pasta_episodio):
    caminho_video = os.path.join(pasta_episodio, "video.mp4")
    caminho_transcript = os.path.join(pasta_episodio, "transcript.json")
    caminho_chapters = os.path.join(pasta_episodio, "chapters.json")

    if not os.path.exists(pasta_episodio):
        print(f"❌ Erro: A pasta '{pasta_episodio}' não existe.")
        sys.exit(1)

    # 1. Transcrição com cache (só roda o Whisper se ainda não existir transcript.json)
    if os.path.exists(caminho_transcript):
        print(f"📄 Transcrição encontrada em {caminho_transcript}. Pulando Whisper...")
        with open(caminho_transcript, "r", encoding="utf-8") as f:
            segmentos = json.load(f)
    else:
        if not os.path.exists(caminho_video):
            print(f"❌ Erro: Vídeo não encontrado em '{caminho_video}'.")
            sys.exit(1)

        print(f"🎙️ Transcrevendo {caminho_video} (pode demorar alguns minutos na CPU)...")
        modelo_whisper = whisper.load_model("base")
        resultado = modelo_whisper.transcribe(caminho_video, language="pt")
        
        segmentos = [
            {
                "start": int(seg["start"]),
                "end": int(seg["end"]),
                "text": seg["text"].strip()
            }
            for seg in resultado["segments"]
        ]
        
        with open(caminho_transcript, "w", encoding="utf-8") as f:
            json.dump(segmentos, f, ensure_ascii=False, indent=2)
        print(f"✅ Transcrição salva em {caminho_transcript}")

    # 2. Formata o texto para o LLM local
    transcricao_formatada = "\n".join(
        f"[{s['start']}s]: {s['text']}" for s in segmentos
    )

    print(f"🧠 Gerando capítulos localmente com {MODELO_LOCAL}...")
    prompt = f"""
Você é um assistente de edição de vídeo para a plataforma infantil CineKids.
Analise a transcrição abaixo (com tempos em segundos) de um episódio de desenho animado.
Identifique as mudanças de cena ou narrativa e crie capítulos lógicos (ex: Abertura, O Problema, A Missão, A Resolução, Créditos).

Retorne ESTRITAMENTE um objeto JSON no formato abaixo:
{{
  "chapters": [
    {{"time": 0, "title": "Abertura"}},
    {{"time": 65, "title": "Nome da Cena"}}
  ]
}}

Transcrição:
{transcricao_formatada}
"""

    # 3. Chamada HTTP local para o Ollama (forçando resposta em JSON válido)
    resposta = requests.post(
        OLLAMA_URL,
        json={
            "model": MODELO_LOCAL,
            "prompt": prompt,
            "format": "json",
            "stream": False
        }
    )
    resposta.raise_for_status()
    
    dados_brutos = json.loads(resposta.json()["response"])
    capitulos = dados_brutos.get("chapters", [])

    with open(caminho_chapters, "w", encoding="utf-8") as f:
        json.dump(capitulos, f, ensure_ascii=False, indent=2)

    print(f"✅ Capítulos gerados em {caminho_chapters} ({len(capitulos)} capítulos)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 gerarcapitulos.py <desenho> <episodio>")
        print("Exemplo: python3 gerarcapitulos.py mecanimais ep2")
        print("     ou: python3 gerarcapitulos.py peixonauta 1")
        sys.exit(1)

    desenho = sys.argv[1]
    episodio = sys.argv[2]

    # Se você passar apenas o número (ex: "2"), ele transforma automaticamente em "ep2"
    if not episodio.startswith("ep"):
        episodio = f"ep{episodio}"

    pasta_alvo = os.path.join(desenho, episodio)
    processar_episodio(pasta_alvo)

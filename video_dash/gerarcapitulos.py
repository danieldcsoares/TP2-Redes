import whisper
import json
import sys
import torch
from google import genai

# Configura a chave de API do Google Gemini
CHAVE_API_GEMINI = "AQ.Ab8RN6KSkljNlYlz8li0UkydmlLp7G5v_YSxIqgPAhE0oviBYQ"

# Inicialização do novo cliente
client = genai.Client(api_key=CHAVE_API_GEMINI)

def gerar_capitulos(caminho_video, caminho_saida_json):
    print(f"A extrair áudio e transcrever: {caminho_video} (Isto pode demorar um pouco...)")
    
    # 1. Carrega o Whisper (o aviso de FP16 aqui é normal em CPU)
    dispositivo = "cuda" if torch.cuda.is_available() else "cpu"
    modelo_whisper = whisper.load_model("base", device=dispositivo)
    resultado = modelo_whisper.transcribe(caminho_video, language="pt")
    
    # 2. Formata a transcrição com os marcadores de tempo
    transcricao_formatada = ""
    for segmento in resultado["segments"]:
        tempo_inicio = int(segmento['start'])
        transcricao_formatada += f"[{tempo_inicio}s]: {segmento['text']}\n"

    print("A enviar contexto para o Gemini analisar a narrativa...")
    
    # 3. Pede ao Gemini para interpretar a história e gerar os capítulos
    prompt = f"""
    És um assistente de edição de vídeo para uma plataforma infantil chamada CineKids.
    Analise a transcrição abaixo (com marcadores de tempo em segundos) de um episódio de desenho animado.
    Identifique as mudanças de cena ou narrativa e crie capítulos lógicos (ex: Abertura, O Problema, A Resolução, Créditos).
    
    Retorne ESTRITAMENTE um JSON válido neste formato, sem formatação markdown adicional:
    [
      {{"time": 0, "title": "Abertura"}},
      {{"time": 120, "title": "Nome da Cena 1"}}
    ]
    
    Transcrição:
    {transcricao_formatada}
    """
    
    # 4. Nova chamada da API utilizando a biblioteca atualizada
    resposta = client.models.generate_content(
        model='gemini-3.8-flash',
        contents=prompt
    )
    
    # 5. Limpa a resposta e guarda o ficheiro JSON na pasta do episódio
    texto_json = resposta.text.replace("```json", "").replace("```", "").strip()
    
    with open(caminho_saida_json, "w", encoding="utf-8") as f:
        f.write(texto_json)
        
    print(f"Ficheiro de capítulos gerado com sucesso em: {caminho_saida_json}")

if __name__ == "__main__":
    # Verifica se o usuário passou a pasta como argumento no terminal
    if len(sys.argv) < 2:
        print("Erro: Faltou informar a pasta do episódio.")
        print("Uso correto: python3 gerarcapitulos.py <caminho_da_pasta>")
        print("Exemplo: python3 gerarcapitulos.py mecanimais/ep1")
        sys.exit(1)
        
    # Pega o primeiro argumento digitado após o nome do script
    # o rstrip('/') garante que vai funcionar mesmo se for digitado "luna/ep1/" com barra no final
    pasta_episodio = sys.argv[1].rstrip('/')
    
    # Monta os caminhos dinamicamente
    video = f"{pasta_episodio}/video.mp4"
    json_saida = f"{pasta_episodio}/chapters.json"
    
    gerar_capitulos(video, json_saida)

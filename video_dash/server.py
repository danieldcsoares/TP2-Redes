import socket
import threading
import os
import mimetypes
import json
import math
import urllib.parse
import requests

# Configurações do servidor
HOST = '0.0.0.0'  # 0.0.0.0 permite acesso local (localhost) e da rede
PORT = 8080

# Configurações do Ollama para busca semântica
OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
MODELO_EMBED = "bge-m3"

def get_cors_headers():
    """Retorna os cabeçalhos CORS necessários para o dash.js funcionar no frontend."""
    return (
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, HEAD, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Origin, Content-Type, Accept, Range, ngrok-skip-browser-warning\r\n"
        "Access-Control-Expose-Headers: Content-Length, Content-Range\r\n"
        "Cache-Control: no-store, no-cache, must-revalidate\r\n"
    )

def similaridade_cosseno(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    return dot / (norm1 * norm2) if norm1 and norm2 else 0.0

def buscar_no_episodio(show, ep, query):
    """Busca os 3 instantes mais relevantes no index.json do episódio via Ollama."""
    ep_pasta = ep if ep.startswith("ep") else f"ep{ep}"
    caminho_index = os.path.join(show, ep_pasta, "index.json")

    if not os.path.exists(caminho_index):
        return []

    resp = requests.post(
        OLLAMA_EMBED_URL,
        json={"model": MODELO_EMBED, "input": query},
        timeout=30
    )
    resp.raise_for_status()
    vetor_query = resp.json()["embeddings"][0]

    with open(caminho_index, "r", encoding="utf-8") as f:
        indice = json.load(f)

    resultados = []
    for item in indice:
        score = similaridade_cosseno(vetor_query, item["embedding"])
        resultados.append({
            "time": item["time"],
            "text": item["text"],
            "score": round(score, 3)
        })

    resultados.sort(key=lambda x: x["score"], reverse=True)
    return resultados[:3]

def handle_client(conn, addr):
    """Processa a requisição HTTP de um cliente de forma isolada numa thread."""
    try:
        # Recebe a requisição do cliente (até 1024 bytes é suficiente para o cabeçalho)
        request_data = conn.recv(1024).decode('utf-8', errors='ignore')
        
        if not request_data:
            return  # Se não receber dados, encerra a conexão

        # Separa a requisição em linhas e extrai o método e o caminho (ex: GET /manifest.mpd HTTP/1.1)
        linhas = request_data.split('\r\n')
        primeira_linha = linhas[0].split()
        
        if len(primeira_linha) < 2:
            return
            
        metodo = primeira_linha[0]
        url_completa = primeira_linha[1]
        caminho = urllib.parse.unquote(url_completa.split('?')[0]).lstrip('/')

        # 1. Tratamento do Preflight (OPTIONS) exigido pelo CORS
        if metodo == 'OPTIONS':
            resposta = (
                "HTTP/1.1 200 OK\r\n" +
                get_cors_headers() +
                "Content-Length: 0\r\n"
                "Connection: close\r\n\r\n"
            )
            conn.sendall(resposta.encode())
            return

        # 2. Tratamento do pedido (GET)
        if metodo == 'GET':
            # 2a. Rota de busca por fala (/buscar?show=...&ep=...&q=...)
            if url_completa.startswith('/buscar'):
                parsed = urllib.parse.urlparse(url_completa)
                params = urllib.parse.parse_qs(parsed.query)
                show = params.get('show', [''])[0]
                ep = params.get('ep', [''])[0]
                query = params.get('q', [''])[0].strip()

                if not show or not ep or not query or '..' in show or '..' in ep:
                    corpo = json.dumps({"error": "Parâmetros inválidos"}).encode('utf-8')
                    cabecalhos = (
                        "HTTP/1.1 400 Bad Request\r\n"
                        "Content-Type: application/json; charset=utf-8\r\n"
                        f"Content-Length: {len(corpo)}\r\n" +
                        get_cors_headers() +
                        "Connection: close\r\n\r\n"
                    )
                    conn.sendall(cabecalhos.encode() + corpo)
                    return

                resultados = buscar_no_episodio(show, ep, query)
                corpo = json.dumps(resultados, ensure_ascii=False).encode('utf-8')
                cabecalhos = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: application/json; charset=utf-8\r\n"
                    f"Content-Length: {len(corpo)}\r\n" +
                    get_cors_headers() +
                    "Connection: close\r\n\r\n"
                )
                conn.sendall(cabecalhos.encode() + corpo)
                return

            # 2b. Tratamento do pedido de ficheiro estático
            if not caminho:
                caminho = 'index.html'

            # Segurança: Evitar Path Traversal (impedir acesso com ../../etc/passwd)
            if '..' in caminho:
                resposta = (
                    "HTTP/1.1 403 Forbidden\r\n"
                    "Content-Length: 0\r\n"
                    "Connection: close\r\n\r\n"
                )
                conn.sendall(resposta.encode())
                return

            try:
                # O ficheiro de vídeo/manifesto deve ser lido em binário ('rb')
                with open(caminho, 'rb') as f:
                    conteudo = f.read()
                
                # Descoberta do Content-Type dinâmico
                tipo_mime, _ = mimetypes.guess_type(caminho)
                if tipo_mime is None:
                    tipo_mime = 'application/octet-stream'

                cabecalhos = (
                    "HTTP/1.1 200 OK\r\n"
                    f"Content-Type: {tipo_mime}\r\n"
                    f"Content-Length: {len(conteudo)}\r\n" +
                    get_cors_headers() +
                    "Connection: close\r\n"
                    "\r\n"
                )
                
                # Envia os cabeçalhos codificados em bytes + o conteúdo do ficheiro de vídeo
                conn.sendall(cabecalhos.encode() + conteudo)
                
            except (FileNotFoundError, IsADirectoryError):
                # Ficheiro não encontrado, retorna Erro 404
                resposta = (
                    "HTTP/1.1 404 Not Found\r\n"
                    "Content-Length: 0\r\n" +
                    get_cors_headers() +
                    "Connection: close\r\n\r\n"
                )
                conn.sendall(resposta.encode())

    except Exception as e:
        print(f"Erro ao processar {addr}: {e}")
    finally:
        # Garante que o socket de ligação devolvido pelo accept() é sempre fechado
        conn.close()

def start_server():
    """Inicia o servidor e escuta novas ligações TCP."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        # Permite reutilizar a porta imediatamente (evita erro "Address already in use")
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen(128)
        print(f"Servidor de Vídeo iniciado em http://{HOST}:{PORT}")
        
        while True:
            # O servidor bloqueia aqui até chegar um novo pedido de cliente
            conn, addr = s.accept()
            
            # Delega a ligação para uma nova thread baseada no server-multithread_2.py
            thread = threading.Thread(target=handle_client, args=(conn, addr))
            thread.start()

if __name__ == '__main__':
    start_server()

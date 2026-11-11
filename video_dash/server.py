import socket
import threading
import os
import mimetypes

# Configurações do servidor
HOST = '0.0.0.0'  # 0.0.0.0 permite acesso local (localhost) e da rede
PORT = 8080

def get_cors_headers():
    """Retorna os cabeçalhos CORS necessários para o dash.js funcionar no frontend."""
    return (
        "Access-Control-Allow-Origin: *\r\n"
        "Access-Control-Allow-Methods: GET, HEAD, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Origin, Content-Type, Accept, Range, ngrok-skip-browser-warning\r\n"
        "Access-Control-Expose-Headers: Content-Length, Content-Range\r\n"
        "Cache-Control: no-store, no-cache, must-revalidate\r\n"
    )

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
        caminho = primeira_linha[1].lstrip('/')

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

        # 2. Tratamento do pedido de ficheiro (GET)
        if metodo == 'GET':
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

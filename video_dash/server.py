from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Permite que qualquer domínio (como o site na Vercel) acesse os arquivos
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
        # IMPORTANTE: precisa incluir o header customizado enviado pelo dash.js,
        # senão o preflight (OPTIONS) falha e o navegador bloqueia por CORS
        self.send_header(
            'Access-Control-Allow-Headers',
            'Origin, Content-Type, Accept, Range, ngrok-skip-browser-warning'
        )
        self.send_header('Access-Control-Expose-Headers', 'Content-Length, Content-Range')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()

    # Responde aos pedidos de pré-verificação (preflight) do navegador
    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Content-Length', '0')
        self.end_headers()


if __name__ == '__main__':
    porta = 8080
    # ThreadingHTTPServer atende vários pedidos de segmentos ao mesmo tempo
    servidor = ThreadingHTTPServer(('', porta), CORSRequestHandler)
    print(f"Servidor de vídeo rodando na porta {porta} com CORS ativado...")
    servidor.serve_forever()

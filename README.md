# CineKids — Vídeo sob demanda adaptativo (DASH) navegável por fala

Trabalho 2 de **Redes de Computadores** (UFES, Departamento de Informática), **Projeto 4: vídeo sob demanda adaptativo e navegável por fala**.

**Autores:** `[Nome 1]` e `[Nome 2]`

## Descrição

O **CineKids** é uma plataforma de streaming de desenhos infantis. Um servidor HTTP próprio, escrito sobre sockets TCP, entrega vídeos segmentados no padrão **MPEG-DASH** em três qualidades (1080p, 720p e 360p). Um player web (Next.js + dash.js) escolhe a qualidade de cada segmento conforme a rede e permite alternar entre dois algoritmos de adaptação (ABR): por **vazão** e por **buffer (BOLA)**.

Além de assistir, o usuário pode navegar por **capítulos** gerados por um LLM local e **buscar por fala** ("onde o personagem fala de feijão?"). O player salta para o trecho encontrado.

Tudo roda localmente, inclusive transcrição e LLM.

> As escolhas de implementação, o experimento de comparação dos ABR e a análise dos resultados estão no **relatório** que acompanha este trabalho.

## Tecnologias Utilizadas

- **Linguagens:** Python 3 (servidor e ferramentas), TypeScript (front-end) e Bash (experimento).
- **Back-end:** biblioteca padrão do Python (`socket`, `threading`), `requests`.
- **Front-end:** Next.js 16, React 19, dash.js 5, Tailwind CSS 4.
- **Mídia e IA local:** FFmpeg (segmentação DASH), Whisper `base` (transcrição), Ollama com `qwen2.5:3b` (capítulos) e `bge-m3` (embeddings da busca).
- **Experimento:** `tc netem` (emulação de banda), `pandas` e `matplotlib` (gráficos).

## Como Executar

### Requisitos

Testado em **Ubuntu Linux**.

| Ferramenta | Instalação |
| --- | --- |
| Python 3 e venv | `sudo apt install python3 python3-venv` |
| Node.js e npm | [nodejs.org](https://nodejs.org/) |
| FFmpeg | `sudo apt install ffmpeg` |
| Ollama | `curl -fsSL https://ollama.com/install.sh \| sh` |
| `tc` (iproute2), usado só no experimento | `sudo apt install iproute2` |

Modelos do Ollama:

```bash
ollama pull qwen2.5:3b   # geração de capítulos
ollama pull bge-m3       # embeddings para a busca por fala
```

Dependências Python (`video_dash/requirements.txt`): `openai-whisper`, `requests`, `pandas`, `matplotlib`.
Dependências Node (`player-dash/package.json`): `next`, `react`, `react-dom`, `dashjs`, `lucide-react`, `tailwindcss`, `typescript`.

### Instruções de Execução

**1. Clone o repositório**

```bash
git clone <URL_DO_REPOSITORIO>
cd <PASTA_DO_REPOSITORIO>
```

**2. Instale as dependências**

```bash
# Python
cd video_dash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Front-end
cd ../player-dash
npm install
```

**3. Prepare o episódio de teste** (uma vez)

O repositório inclui o vídeo do episódio de teste em `video_dash/mecanimais/ep1/video.mp4` (Mecanimais, "A plantação de turbo feijão"), que já está cadastrado no player. Os segmentos DASH (`.m4s`) e o manifesto (`.mpd`) **não** estão no repositório (`.gitignore`), então gere-os a partir desse vídeo:

```bash
cd video_dash/mecanimais/ep1

ffmpeg -i video.mp4 \
  -map 0:v:0 -map 0:v:0 -map 0:v:0 -map 0:a:0 \
  -c:v libx264 -preset veryfast -c:a aac -b:a 128k \
  -g 96 -keyint_min 96 -sc_threshold 0 \
  -filter:v:0 scale=-2:1080 -b:v:0 4000k \
  -filter:v:1 scale=-2:720  -b:v:1 2000k \
  -filter:v:2 scale=-2:360  -b:v:2 800k \
  -seg_duration 4 -use_timeline 1 -use_template 1 -window_size 0 \
  -adaptation_sets "id=0,streams=v id=1,streams=a" \
  -f dash manifest.mpd
```

Confira o manifesto. O esperado é **1 `AdaptationSet` de vídeo com 3 `Representation` e 1 de áudio**:

```bash
grep -n -E "<AdaptationSet|<Representation" manifest.mpd
```

Depois, a partir de `video_dash/` e com o `venv` ativo, gere a transcrição, os capítulos e o índice de busca (o Whisper pode levar alguns minutos na CPU):

```bash
cd ../..
python3 capitulo_fala.py mecanimais 1   # Whisper -> transcript.json -> chapters.json
python3 indexar.py mecanimais 1         # transcript.json -> index.json
```

> **Para usar outro episódio:** coloque o vídeo em `video_dash/<serie>/ep<N>/video.mp4` (tudo em minúsculas), repita os comandos acima trocando `mecanimais`/`ep1` e cadastre o episódio em `player-dash/lib/data.ts` (título, duração e capa).

**4. Execute o servidor** (Terminal 1, de dentro de `video_dash/`)

```bash
ollama list                 # confirma que o Ollama está ativo (ou: ollama serve)
source venv/bin/activate
python3 server.py
# Servidor de Vídeo iniciado em http://0.0.0.0:8080
```

**5. Execute o cliente** (Terminal 2)

```bash
cd player-dash
npm run dev -- -H 0.0.0.0
```

**6. Acesse**

- No próprio computador: <http://localhost:3000>
- Em outro dispositivo da mesma rede: `http://<IP_DA_MAQUINA>:3000` (descubra o IP com `hostname -I`). Se necessário, libere as portas: `sudo ufw allow 3000/tcp` e `sudo ufw allow 8080/tcp`.

O front-end descobre sozinho o endereço do servidor (`http://<mesmo host>:8080`). Para usar outro, defina `NEXT_PUBLIC_VIDEO_URL` em um `.env.local`.

## Como Testar

### 1. Testes funcionais no navegador

1. Abra o episódio **Mecanimais, "A plantação de turbo feijão"** (catálogo, depois Mecanimais, depois episódio 1) e dê **play**; use **pause** e **seek** na barra de progresso. Na aba *Network* do navegador, o seek deve pedir apenas o segmento `.m4s` correspondente.
2. Troque entre **ABR: Vazão** e **ABR: BOLA** nos botões do player. Os logs `[MÉTRICA]` aparecem no console.
3. Clique em um **capítulo** da lista: o vídeo salta para o instante indicado.
4. Digite uma pergunta na **busca por fala** (por exemplo, "onde falam de feijão?", tema do episódio de teste): clique em um dos 3 resultados e confira se o vídeo salta para o trecho.
5. Clique em **Exportar Métricas (CSV)** e confira o arquivo gerado (buffer, bitrate, resolução e travamentos por segundo).

### 2. Testes do servidor (erros e concorrência)

Com o servidor ligado:

```bash
# 200: manifesto
curl -I http://localhost:8080/mecanimais/ep1/manifest.mpd

# 404: arquivo inexistente
curl -i http://localhost:8080/mecanimais/ep1/nao-existe.m4s

# 403: tentativa de path traversal
curl --path-as-is -i http://localhost:8080/../etc/passwd

# 400: busca sem parâmetros obrigatórios
curl -i "http://localhost:8080/buscar?show=mecanimais"

# 200: busca por fala (retorna os 3 trechos mais relevantes)
curl -s -G http://localhost:8080/buscar \
  --data-urlencode "show=mecanimais" --data-urlencode "ep=1" \
  --data-urlencode "q=onde falam de feijão"

# Concorrência: 100 requisições, 20 em paralelo; todas devem retornar 200
seq 1 100 | xargs -P 20 -I{} curl -s -o /dev/null -w "%{http_code}\n" \
  http://localhost:8080/mecanimais/ep1/manifest.mpd | sort | uniq -c
```

### 3. Experimento de desempenho (comparação dos ABR)

O experimento aplica um traço de banda variável de 120 s com `tc netem` na interface de loopback (5 Mbit/s, 1 Mbit/s, 300 kbit/s + 100 ms, 5 Mbit/s, em fases de 30 s).

```bash
# 1) Abra o episódio no player, escolha o algoritmo e dê play
# 2) Imediatamente, em outro terminal:
cd video_dash
sudo ./experimento.sh      # dura 120 s e remove a limitação ao final

# 3) Ao fim, exporte o CSV no player e salve em video_dash/resultados/ como
#    metricas_abrThroughput_run1.csv (ou metricas_abrBola_run1.csv)
# 4) Repita 3 vezes por algoritmo e gere gráfico e tabelas:
cd resultados
python3 ../gerargraficos.py \
  --vazao metricas_abrThroughput_run*.csv \
  --bola  metricas_abrBola_run*.csv \
  --saida grafico_comparativo.png
```

Resultados e análise: veja o relatório. Os dados brutos desta entrega estão em `video_dash/resultados/` (`resumo_metricas.csv` e `grafico_comparativo.png`).

## Funcionalidades Implementadas

**Núcleo**

- Codificação DASH com FFmpeg em três qualidades (1080p/4000 kbps, 720p/2000 kbps e 360p/800 kbps), segmentos de 4 s e manifesto `manifest.mpd`.
- Servidor HTTP próprio sobre sockets TCP, com uma thread por conexão, CORS, proteção contra *path traversal* e respostas 400, 403 e 404.
- Player web com buffer, play, pause e seek.
- Registro de métricas a 1 Hz (buffer, bitrate, resolução e travamentos) com exportação em CSV.

**Incremento de Desempenho**

- Dois algoritmos de ABR selecionáveis em tempo de execução: por vazão (`throughputRule`) e por buffer (`bolaRule`).
- Experimento com banda variável (`tc netem`), 3 execuções por algoritmo, métrica de QoE e gráfico comparativo com média e desvio padrão.

**Incremento de Inteligência**

- Pipeline local: Whisper, depois capítulos com `qwen2.5:3b`, depois índice com `bge-m3` e busca semântica por similaridade de cosseno ("Momentos Mágicos").

## Possíveis Melhorias Futuras

- Adicionar uma qualidade mais baixa (por exemplo, 240p a ~300 kbps) e/ou ajustar a fase de 300 kbit/s do experimento, para que ela deixe de ficar abaixo da menor qualidade.
- Alongar a fase de recuperação e aumentar o número de execuções, para permitir conclusões estatísticas.
- Implementar requisições `Range` e leitura em blocos no servidor (hoje ele lê o arquivo inteiro em memória).
- Usar *pool* de threads ou I/O assíncrono no servidor.
- Responder `500`/`503` quando o Ollama estiver indisponível na rota `/buscar`.
- Implementar um ABR próprio (por exemplo, híbrido vazão + buffer) em vez de usar só as regras nativas do dash.js.
- Medir o experimento em uma rede física, e não só na interface de loopback.

## Arquitetura

```
              Navegador (Next.js + dash.js: ABR Vazão | BOLA, busca, métricas 1 Hz)
                    │ manifest.mpd / .m4s / chapters.json      │ GET /buscar?q=...
                    ▼                                          ▼
              server.py  (HTTP sobre sockets TCP, :8080) ── embeddings ──► Ollama (:11434)

 Preparação offline de cada episódio:
 video.mp4 ──ffmpeg──► manifest.mpd + segmentos .m4s
 video.mp4 ──Whisper──► transcript.json ──qwen2.5:3b──► chapters.json
 transcript.json ──bge-m3──► index.json
```

## Estrutura do Repositório

```
.
├── player-dash/                 # Front-end (Next.js + React + dash.js)
│   ├── app/watch/[id]/page.tsx  # Player, ABR, métricas, capítulos e busca
│   └── lib/data.ts              # Catálogo de séries e episódios
└── video_dash/                  # Back-end e ferramentas
    ├── server.py                # Servidor HTTP + rota /buscar
    ├── capitulo_fala.py         # Whisper -> transcript.json -> chapters.json
    ├── indexar.py               # transcript.json -> index.json
    ├── experimento.sh           # Traço de banda variável com tc netem
    ├── gerargraficos.py         # Gráficos e tabela de métricas/QoE
    ├── resultados/              # CSVs, grafico_comparativo.png e resumo_metricas.csv
    └── mecanimais/ep1/          # video.mp4 (incluído), e gerados localmente: manifest.mpd,
                                 # *.m4s, transcript.json, chapters.json, index.json
```

## Créditos

Trabalho acadêmico, UFES. Os desenhos usados nos testes pertencem aos seus detentores de direitos e não são distribuídos neste repositório.

Ferramentas: [dash.js](https://github.com/Dash-Industry-Forum/dash.js), [Next.js](https://nextjs.org/), [FFmpeg](https://ffmpeg.org/), [Whisper](https://github.com/openai/whisper), [Ollama](https://ollama.com/).

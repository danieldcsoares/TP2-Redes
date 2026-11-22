'use client';

import { useEffect, useRef, use, Suspense, useState } from 'react';
import Link from 'next/link';
import { ArrowLeft, Maximize, Play, Search } from 'lucide-react';
import { shows } from '../../../lib/data';

// URL base do servidor de vídeo. Defina NEXT_PUBLIC_VIDEO_URL na Vercel para não precisar editar o código toda vez que o túnel gerar uma URL nova.
const getVideoBaseUrl = () => {
  if (process.env.NEXT_PUBLIC_VIDEO_URL) {
    return process.env.NEXT_PUBLIC_VIDEO_URL;
  }
  if (typeof window !== 'undefined') {
    return `http://${window.location.hostname}:8080`;
  }
  return 'http://localhost:8080';
};

function PlayerContent({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const videoRef = useRef<HTMLVideoElement>(null);

  // Extrai o ID da série e o número do episódio da URL (ex: "luna-ep1")
  const [showId, epString] = resolvedParams.id.split('-ep');
  const epIndex = parseInt(epString) - 1 || 0;

  const show = shows.find((s) => s.id === showId);
  const episode = show?.episodes[epIndex];

  // Estado para armazenar os capítulos gerados pela IA
  const [capitulos, setCapitulos] = useState<{time: number, title: string}[]>([]);

  const [termoBusca, setTermoBusca] = useState('');
  const [resultadosBusca, setResultadosBusca] = useState<{ time: number; text: string; score: number }[]>([]);
  const [buscando, setBuscando] = useState(false);

  const realizarBusca = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!termoBusca.trim() || !show) return;

    setBuscando(true);
    try {
      const url = `${getVideoBaseUrl()}/buscar?show=${show.id}&ep=${epIndex + 1}&q=${encodeURIComponent(termoBusca)}`;
      const resp = await fetch(url);
      if (resp.ok) {
        const dados = await resp.json();
        setResultadosBusca(dados);
      }
    } catch (erro) {
      console.error('Erro na busca por fala:', erro);
    } finally {
      setBuscando(false);
    }
  };

  // Algoritmo de ABR selecionado: 'abrThroughput' (Vazão) ou 'abrBola' (Buffer)
  const [abrStrategy, setAbrStrategy] = useState<'abrThroughput' | 'abrBola'>('abrThroughput');

  // Armazena as métricas coletadas sem causar re-renderizações a cada segundo
  const metricasRef = useRef<
    { tempo_s: number; buffer_s: number; bitrate_kbps: number; resolucao: string; travamentos: number }[]
  >([]);
  const qualidadeAtualRef = useRef({ bitrate_kbps: 0, resolucao: 'N/A' });
  const travamentosRef = useRef(0);

  const exportarCSV = () => {
    if (metricasRef.current.length === 0) {
      alert('Nenhuma métrica coletada ainda. Dê play no vídeo primeiro!');
      return;
    }

    const cabecalho = 'tempo_s,buffer_s,bitrate_kbps,resolucao,travamentos\n';
    const linhas = metricasRef.current
      .map((m) => `${m.tempo_s},${m.buffer_s},${m.bitrate_kbps},${m.resolucao},${m.travamentos}`)
      .join('\n');

    const blob = new Blob([cabecalho + linhas], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `metricas_${show?.id}_ep${epIndex + 1}_${abrStrategy}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Função para saltar para o momento exato do vídeo
  const pularParaCapitulo = (tempoEmSegundos: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = tempoEmSegundos;
      videoRef.current.play(); // Garante que o vídeo retoma a reprodução
    }
  };

  useEffect(() => {
    // Verifica ANTES de criar o player, para não vazar instância
    if (!show) return;

    let player: any;
    let interval: ReturnType<typeof setInterval> | undefined;
    let cancelled = false;

    const inicializarPlayer = async () => {
      const dashjs = await import('dashjs');

      // Se o componente desmontou enquanto o import carregava, não faz nada
      if (cancelled || !videoRef.current) return;

      player = dashjs.MediaPlayer().create();

      // Define a estratégia de ABR escolhida (Vazão ou BOLA) no dash.js v5
      player.updateSettings({
        streaming: {
          abr: {
            rules: {
              throughputRule: { active: abrStrategy === 'abrThroughput' },
              bolaRule: { active: abrStrategy === 'abrBola' },
            },
          },
        },
      });

      // Inicializa o player DASH
      player.initialize(
        videoRef.current,
        `${getVideoBaseUrl()}/${show.id}/ep${epIndex + 1}/manifest.mpd`,
        false
      );

      // Reseta métricas ao carregar um novo episódio
      metricasRef.current = [];
      travamentosRef.current = 0;
      let segundosDecorridos = 0;

      // Função auxiliar compatível com dash.js v4 e v5
      const atualizarQualidade = (e?: any) => {
        if (e?.mediaType && e.mediaType !== 'video') return;

        // dash.js v5
        const rep = e?.newRepresentation ?? player.getCurrentRepresentationForType?.('video');
        if (rep) {
          const kbps = Math.round((rep.bandwidth ?? 0) / 1000);
          const res = rep.height ? `${rep.height}p` : 'N/A';
          qualidadeAtualRef.current = { bitrate_kbps: kbps, resolucao: res };
          console.log(`[MÉTRICA] Qualidade adaptada: ${res} (${kbps} kbps)`);
          return;
        }

        // Fallback dash.js v4
        if (e?.newQuality !== undefined) {
          const lista = player.getBitrateInfoListFor?.('video') ?? [];
          const info = lista[e.newQuality];
          const kbps = info ? Math.round(info.bitrate / 1000) : 0;
          const res = info?.height ? `${info.height}p` : `Nível ${e.newQuality}`;
          qualidadeAtualRef.current = { bitrate_kbps: kbps, resolucao: res };
          console.log(`[MÉTRICA] Qualidade adaptada: ${res} (${kbps} kbps)`);
        }
      };

      player.on(dashjs.MediaPlayer.events.QUALITY_CHANGE_RENDERED, atualizarQualidade);

      player.on(dashjs.MediaPlayer.events.BUFFER_EMPTY, () => {
        travamentosRef.current += 1;
        console.log(`[MÉTRICA] Travamento detectado! Total: ${travamentosRef.current}`);
      });

      interval = setInterval(() => {
        if (player && player.isReady() && videoRef.current && !videoRef.current.paused) {
          segundosDecorridos += 1;
          const bufferLevel = Number(player.getBufferLength('video').toFixed(2));

          // Garante leitura inicial mesmo antes da primeira troca de qualidade
          if (qualidadeAtualRef.current.bitrate_kbps === 0) {
            atualizarQualidade();
          }

          const registro = {
            tempo_s: segundosDecorridos,
            buffer_s: bufferLevel,
            bitrate_kbps: qualidadeAtualRef.current.bitrate_kbps,
            resolucao: qualidadeAtualRef.current.resolucao,
            travamentos: travamentosRef.current,
          };

          metricasRef.current.push(registro);
          console.log(
            `[MÉTRICA] t=${registro.tempo_s}s | Buffer: ${registro.buffer_s}s | ${registro.resolucao} (${registro.bitrate_kbps} kbps) | Travamentos: ${registro.travamentos} | Algoritmo: ${abrStrategy}`
          );
        }
      }, 1000);
    };

    inicializarPlayer();

    return () => {
      cancelled = true;
      if (interval) clearInterval(interval);
      if (player) player.destroy();
    };
  }, [showId, epIndex, show, abrStrategy]);

  // Novo useEffect para carregar os capítulos do JSON gerado pelo Gemini
  useEffect(() => {
    const carregarCapitulos = async () => {
      try {
        const resposta = await fetch(`${getVideoBaseUrl()}/${show?.id}/ep${epIndex + 1}/chapters.json`);
        if (resposta.ok) {
          const dados = await resposta.json();
          setCapitulos(dados);
        }
      } catch (erro) {
        console.log("Nenhum capítulo mágico encontrado para este episódio.", erro);
      }
    };

    if (show) carregarCapitulos();
  }, [show, epIndex]);

  // Se a URL estiver errada
  if (!show || !episode) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#111936] text-white">
        Carregando aventura...
      </div>
    );
  }

  return (
    <main className="min-h-screen overflow-hidden bg-[#111936] text-white font-sans">
      <div className="pointer-events-none fixed -left-32 top-40 h-72 w-72 rounded-full bg-[#6c5ce7]/20 blur-3xl" />
      <div className="pointer-events-none fixed -right-20 bottom-10 h-80 w-80 rounded-full bg-[#20d4d7]/15 blur-3xl" />

      <header className="relative z-10 mx-auto flex max-w-[1240px] items-center justify-between px-5 py-6 md:px-8">
        <Link
          href={`/show/${show.id}`}
          className="group flex items-center gap-3 rounded-full text-left transition hover:text-[#ffd447]"
          aria-label="Voltar para a série"
        >
          <span className="grid h-11 w-11 place-items-center rounded-full border border-white/15 bg-white/10 transition group-hover:-translate-x-1 group-hover:bg-white/20">
            <ArrowLeft size={19} />
          </span>
          <span className="hidden text-sm font-bold text-white/80 sm:block">Voltar para a série</span>
        </Link>
        <div className="text-center">
          <p className="text-[11px] font-extrabold uppercase tracking-[.28em] text-[#62dfe0]">
            Cine<span className="text-[#ffd447]">Kids</span>
          </p>
          <h1 className="mt-1 text-sm font-bold text-white sm:text-base">{show.title}</h1>
        </div>
        <button
          className="grid h-11 w-11 place-items-center rounded-full border border-white/15 bg-white/10 text-white/80 transition hover:bg-white/20"
          aria-label="Ajustes de tela"
        >
          <Maximize size={17} />
        </button>
      </header>

      <section className="relative z-10 mx-auto max-w-[1240px] px-4 md:px-8">
        {/* Container do Player DASH */}
        <div className="relative aspect-video overflow-hidden rounded-[32px] border border-white/10 bg-[#050817] shadow-[0_0_80px_rgba(94,91,220,.3),0_18px_55px_rgba(0,0,0,.3)] group">
          <video ref={videoRef} controls className="w-full h-full object-contain bg-black" />
        </div>

        <div className="mt-8 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-extrabold uppercase tracking-[.2em] text-[#62dfe0]">
              Abra o console (F12) para ver as métricas
            </p>
            <h2 className="mt-2 text-2xl font-black tracking-tight sm:text-3xl">
              Episódio {epIndex + 1} — {episode.title}
            </h2>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {/* Seletor de Algoritmo ABR */}
            <div className="flex rounded-full border border-white/15 bg-white/5 p-1 text-xs font-black">
              <button
                onClick={() => setAbrStrategy('abrThroughput')}
                className={`rounded-full px-3 py-1.5 transition ${
                  abrStrategy === 'abrThroughput'
                    ? 'bg-[#ffd447] text-[#111936]'
                    : 'text-white/60 hover:text-white'
                }`}
              >
                ABR: Vazão
              </button>
              <button
                onClick={() => setAbrStrategy('abrBola')}
                className={`rounded-full px-3 py-1.5 transition ${
                  abrStrategy === 'abrBola'
                    ? 'bg-[#ffd447] text-[#111936]'
                    : 'text-white/60 hover:text-white'
                }`}
              >
                ABR: BOLA
              </button>
            </div>

            <span className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-bold text-white/55">
              Duração: {episode.duration}
            </span>
            <button
              onClick={exportarCSV}
              className="rounded-full bg-[#62dfe0] px-4 py-2 text-xs font-black text-[#111936] transition hover:bg-[#ffd447]"
            >
              Exportar Métricas (CSV)
            </button>
          </div>
        </div>

        {/* Busca por Fala (Linguagem Natural) */}
        <section className="mt-8 rounded-[24px] bg-white/5 p-6 border border-white/10">
          <h3 className="mb-4 text-lg font-black text-[#62dfe0]">🔎 Buscar cena pela fala</h3>
          <form onSubmit={realizarBusca} className="flex flex-col gap-3 sm:flex-row">
            <div className="relative flex-1">
              <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40" />
              <input
                type="text"
                value={termoBusca}
                onChange={(e) => setTermoBusca(e.target.value)}
                placeholder="Ex: quando eles encontram a pista?"
                className="w-full rounded-full border border-white/15 bg-[#111936] py-3 pl-11 pr-4 text-sm text-white placeholder-white/40 outline-none focus:border-[#62dfe0]"
              />
            </div>
            <button
              type="submit"
              disabled={buscando}
              className="rounded-full bg-[#ffd447] px-6 py-3 text-sm font-black text-[#111936] transition hover:bg-[#62dfe0] disabled:opacity-50"
            >
              {buscando ? 'Buscando...' : 'Ir para a cena'}
            </button>
          </form>

          {resultadosBusca.length > 0 && (
            <div className="mt-4 grid gap-2">
              {resultadosBusca.map((res, idx) => {
                const min = Math.floor(res.time / 60).toString().padStart(2, '0');
                const seg = (res.time % 60).toString().padStart(2, '0');
                return (
                  <button
                    key={idx}
                    onClick={() => pularParaCapitulo(res.time)}
                    className="flex items-start gap-3 rounded-2xl border border-white/10 bg-[#111936]/80 p-3.5 text-left transition hover:border-[#62dfe0] hover:bg-[#111936]"
                  >
                    <span className="shrink-0 rounded-lg bg-[#62dfe0]/20 px-2.5 py-1 text-xs font-black text-[#62dfe0]">
                      {min}:{seg}
                    </span>
                    <span className="text-sm text-white/85 line-clamp-2">"{res.text}"</span>
                  </button>
                );
              })}
            </div>
          )}
        </section>

        {/* Trilho de Capítulos Gerados por IA */}
        {capitulos.length > 0 && (
          <section className="mt-8 rounded-[24px] bg-white/5 p-6 border border-white/10">
            <h3 className="mb-4 text-lg font-black text-[#ffd447]">✨ Momentos Mágicos</h3>
            
            {/* Trocamos o overflow-x-auto por flex-wrap para mostrar todos de uma vez */}
            <div className="flex flex-wrap gap-3 pb-2">
              {capitulos.map((cap, index) => {
                // Pequena lógica para formatar segundos em MM:SS (ex: 65s vira 01:05)
                const minutos = Math.floor(cap.time / 60).toString().padStart(2, '0');
                const segundos = (cap.time % 60).toString().padStart(2, '0');

                return (
                  <button
                    key={index}
                    onClick={() => pularParaCapitulo(cap.time)}
                    className="group flex items-center gap-2 rounded-full bg-[#111936] px-4 py-2.5 text-sm font-extrabold text-white/80 border border-white/10 shadow-sm transition hover:-translate-y-1 hover:bg-[#62dfe0] hover:text-[#111936] hover:shadow-[0_4px_0_#459c9d]"
                  >
                    <span className="rounded bg-white/10 px-1.5 py-0.5 text-xs font-black text-[#62dfe0] transition group-hover:bg-[#111936]/20 group-hover:text-[#111936]">
                      {minutos}:{segundos}
                    </span>
                    {cap.title}
                  </button>
                );
              })}
            </div>
          </section>
        )}

        {/* Trilho de Próximos Episódios */}
        <section className="pb-14 pt-10">
          <div className="mb-5 flex items-center justify-between">
            <h3 className="text-xl font-black">Próximos episódios</h3>
            <span className="text-xs font-bold text-white/40">Deslize para descobrir</span>
          </div>

          <div className="flex gap-4 overflow-x-auto pb-4 [scrollbar-width:none]">
            {show.episodes.slice(epIndex + 1).map((item, index) => (
              <Link
                href={`/watch/${show.id}-ep${epIndex + 2 + index}`}
                key={item.title}
                className="group min-w-[245px] text-left sm:min-w-[280px]"
              >
                <div className="relative aspect-video overflow-hidden rounded-[22px] border border-white/10 bg-white/5">
                  <img
                    src={item.image}
                    alt={`Thumbnail de ${item.title}`}
                    className="h-full w-full object-cover opacity-80 transition duration-300 group-hover:scale-105 group-hover:opacity-100"
                  />
                  <span className="absolute bottom-3 right-3 rounded-full bg-[#111936]/85 px-2.5 py-1 text-[10px] font-extrabold text-white">
                    {item.duration}
                  </span>
                  <span className="absolute left-3 top-3 rounded-full bg-[#62dfe0] px-2.5 py-1 text-[10px] font-black text-[#111936]">
                    EP {epIndex + 2 + index}
                  </span>
                  <span className="absolute inset-0 grid place-items-center opacity-0 transition group-hover:opacity-100">
                    <span className="grid h-12 w-12 place-items-center rounded-full bg-[#ffd447] text-[#34266d] shadow-lg">
                      <Play size={18} fill="currentColor" />
                    </span>
                  </span>
                </div>
                <h4 className="mt-3 text-sm font-extrabold text-white/90">{item.title}</h4>
                <p className="mt-1 text-xs font-semibold text-white/40">{show.title}</p>
              </Link>
            ))}

            {/* Mensagem caso seja o último episódio */}
            {show.episodes.slice(epIndex + 1).length === 0 && (
              <p className="text-sm font-bold text-white/40">Você chegou ao fim desta temporada!</p>
            )}
          </div>
        </section>
      </section>
    </main>
  );
}

export default function WatchEpisode({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[#111936] text-white">
          Preparando reprodutor...
        </div>
      }
    >
      <PlayerContent params={params} />
    </Suspense>
  );
}
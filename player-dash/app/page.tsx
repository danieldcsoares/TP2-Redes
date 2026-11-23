'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ChevronRight, Play, Search, Sparkles, UserRound } from 'lucide-react'
import { shows, getRandomShow, type Show } from '../lib/data' // Importando os dados do arquivo que separamos

// Removemos a propriedade "onHome", agora usamos o Link do Next.js
function Header() {
  return (
    <header className="flex items-center justify-between px-5 py-5 md:px-12">
      <Link href="/" className="flex items-center gap-2" aria-label="Ir para o início">
        <span className="grid h-12 w-12 rotate-[-8deg] place-items-center rounded-[18px] bg-[#ffda3e] text-2xl text-[#ff7b54] shadow-[0_5px_0_#f0ae32]">★</span>
        <span className="text-[27px] font-black tracking-[-1.5px] text-[#25305f]">
          cine<span className="text-[#ff6f91]">kids</span>
        </span>
      </Link>
   
      <div className="flex items-center gap-3">
        <button className="grid h-11 w-11 place-items-center rounded-full bg-white text-[#25305f] shadow-sm" aria-label="Buscar"><Search size={18} /></button>
        <button className="grid h-11 w-11 place-items-center rounded-full bg-[#7c5cff] text-white shadow-[0_4px_0_#5640bd]" aria-label="Perfil"><UserRound size={18} /></button>
      </div>
    </header>
  )
}

// O botão original foi substituído pelo componente Link direcionando para a rota dinâmica
function ShowCard({ show }: { show: any }) {
  return (
    <Link href={`/show/${show.id}`} className="group block w-full aspect-[3/4] min-w-[172px] text-left sm:min-w-[206px]" aria-label={`Ver detalhes de ${show.title}`}>
      <div className="relative aspect-[2/3] w-full overflow-hidden aspect-[.82] overflow-hidden rounded-[28px] border-[5px] border-white bg-[#dff9f8] shadow-[0_8px_0_#c5e8e8] transition duration-300 group-hover:-translate-y-2 group-hover:rotate-1">
        <img src={show.image} alt={`Capa de ${show.title}`} className="h-full w-full object-cover" />
        <div className="absolute inset-x-0 bottom-0 h-2/5 bg-gradient-to-t from-black/55 to-transparent" />
        <span className="absolute left-3 top-3 rounded-full bg-[#ffda3e] px-3 py-1 text-[10px] font-black text-[#25305f]">NOVO</span>
        <span className="absolute bottom-3 right-3 grid h-9 w-9 place-items-center rounded-full bg-white text-[#ff6f91] shadow-lg">
          <Play size={14} fill="currentColor" />
        </span>
      </div>
      <h3 className="mt-4 truncate text-[15px] font-black text-[#25305f]">{show.title}</h3>
      <p className="mt-1 text-xs font-bold text-[#7d89a8]">{show.category}</p>
    </Link>
  )
}

function HomeScreen() {
  const [featuredShow, setFeaturedShow] = useState<Show>(shows[0])

  useEffect(() => {
    setFeaturedShow(getRandomShow())
  }, [])

  return (
    <main id="inicio" className="pb-16">
      <section className="relative mx-5 min-h-[420px] overflow-hidden rounded-[38px] bg-[#72dfe0] shadow-[0_10px_0_#b6e7e3] md:mx-12">
        <img src={featuredShow.image} alt={`Banner de ${featuredShow.title}`} className="absolute inset-0 h-full w-full object-cover opacity-35 mix-blend-multiply" />
        <div className="absolute -right-10 -top-16 h-60 w-60 rounded-full bg-[#ffda3e]/80 blur-sm" />
        <div className="absolute bottom-[-90px] right-32 h-52 w-52 rounded-full bg-[#ff8fb1]/70" />
        <div className="relative max-w-xl px-7 py-14 md:px-14 md:py-24">
          <span className="mb-5 inline-flex items-center gap-2 rounded-full bg-white px-4 py-2 text-xs font-black text-[#7c5cff] shadow-sm"><Sparkles size={14} /> HISTÓRIA DA SEMANA</span>
          <h1 className="text-4xl font-black leading-[.95] tracking-[-2px] text-[#25305f] md:text-6xl">{featuredShow.title}</h1>
          <p className="mt-5 line-clamp-3 max-w-md text-sm font-bold leading-relaxed text-[#33467e]">{featuredShow.description}</p>
          
          {/* Botão de assistir do Hero Banner agora é um Link */}
          <Link href={`/show/${featuredShow.id}`} className="mt-7 inline-flex items-center gap-2 rounded-full bg-[#ff6f91] px-6 py-3 text-sm font-black text-white shadow-[0_5px_0_#d44d76] transition hover:translate-y-0.5">
            <Play size={17} fill="currentColor" /> Assistir agora
          </Link>
        </div>
      </section>
      
      <section id="categorias" className="mt-14 px-5 md:px-12">
        <Rail title="Nossos desenhos" showsList={shows} />
      </section>
    </main>
  )
}

function Rail({ title, showsList }: { title: string; showsList: Show[] }) { 
  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-2xl font-black tracking-tight text-[#25305f]">{title}</h2>
      </div>
      <div className="grid grid-cols-2 gap-6 lg:grid-cols-4">
        {showsList.map((show) => (
          <ShowCard key={show.id} show={show} />
        ))}
      </div>
    </div> 
  ) 
}

// O componente Home agora renderiza apenas a Header e a HomeScreen
export default function Home() { 
  return (
    <div className="min-h-screen bg-[#fffaf1] font-sans">
      <Header />
      <HomeScreen />
    </div> 
  ) 
}
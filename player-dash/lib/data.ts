export type Episode = { title: string; duration: string; image: string, sinopse?: string }
export type Show = { id: string; title: string; category: string; image: string; accent: string; description: string; episodes: Episode[] }

export const shows: Show[] = [
  { id: 'backyardigans', title: 'Os Backyardigans', category: 'Aventura', image: '/fundobackyardigans.jpg', accent: '#7c5cff', description: 'Cinco animaizinhos coloridos viajam para lugares imaginários e vivem grandes aventuras no quintal de casa. Os episódios apresentam musicais de gêneros diferentes e dança.', episodes: [
    { title: 'O tesouro do pirata', duration: '25 min', image: '/backyardigans/ep1.jpeg', sinopse: 'Uniqua e Austin são piratas corajosos que estão procurando um tesouro escondido depois de encontrar a metade de um mapa, mas não sabem que Pablo e Tyrone estão com a outra parte e também procuram pelo tesouro.' },
    { title: 'O coração da floresta', duration: '25 min', image: '/backyardigans/ep2.jpeg', sinopse:'Tyrone é Tarzan, e assim são Pablo e Austin. Com Uniqua, eles têm a missão de ajudar um amigo a encontrar sua casa na selva.' },
    { title: 'O mapa perdido', duration: '13 min', image: '/backyardigans/ep3.jpeg' },
  ] },
  { id: 'peixonauta', title: 'Peixonauta', category: 'Aventura', image: '/peixonautafundo.jpg', accent: '#ff8b3d', description: `O agente secreto Peixonauta possui um traje especial que o permite voar e respirar fora d'água. O peixe é um detetive profissional que conta com a ajuda de seus amigos Marina, uma criança, e Zico, um macaco. Juntos, eles vivem incríveis aventuras no Parque das Árvores Felizes, dentro e fora d'água. Os mistérios são resolvidos com a ajuda da Pop, uma bola mágica e colorida que sempre envia pistas para os três.`, episodes: [
    { title: 'O Caso do Coelho Desanimado', duration: '11 min', image: '/peixonauta/ep1/capaep.webp' },
    
  ] },
  { id: 'mecanimais', title: 'Mecanimais', category: 'Aventura', image: '/mecafundo.jpg', accent: '#ed5aa8', description: 'Esta animação, especificamente concebida para pré-escolares, conta as aventuras de uma equipe de animais robôs com superpoderes que partem em aventuras para ajudarem uns aos outros e, ao mesmo tempo, vão aprendendo coisas novas.', episodes: [
    { title: 'A plantação de turbo feijão', duration: '11 min', image: 'https://i.ytimg.com/vi/_X8UE_DaafE/hqdefault.jpg?sqp=-oaymwEnCNACELwBSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLBPE-gmT0iCi8iXBdJKhn-LOYZwtw' },
    { title: 'Ilha dos coelhos', duration: '11 min', image: 'https://i.ytimg.com/vi/Njx857MkUNw/hqdefault.jpg?sqp=-oaymwEnCNACELwBSFryq4qpAxkIARUAAIhCGAHYAQHiAQoIGBACGAY4AUAB&rs=AOn4CLCmxN5Qds9SC1HXBaK69VxPO1kRqg' },
  ] },
  { id: 'pocoyo', title: 'Pocoyo', category: 'Aventura', image: '/pocoyofundo.webp', accent: '#ed5aa8', description: 'Quem disse que aprender não é divertido? De chapéu e roupas azuis, Pocoyo faz de cada dia uma inesquecível aventura enquanto explora o mundo ao seu redor ao lado de seus amigos, o que inclui um pato amarelo, uma elefanta rosa, um pássaro dorminhoco e a cadelinha Loula.', episodes: [
    { title: 'Códisago amizade', duration: '11 min', image: 'https://images.unsplash.com/photo-1535378917042-10a22c95931a?auto=format&fit=crop&w=700&q=85' },
    { title: 'A corrsasaida maluca', duration: '10 min', image: 'https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=700&q=85' },
  ] },
]

export function getRandomShow(): Show {
  const randomIndex = Math.floor(Math.random() * shows.length)
  return shows[randomIndex]
}
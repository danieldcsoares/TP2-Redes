export type Episode = { title: string; duration: string; image: string, sinopse?: string }
export type Show = { id: string; title: string; category: string; image: string; accent: string; description: string; episodes: Episode[] }

export const shows: Show[] = [
  { id: 'backyardigans', title: 'Os Backyardigans', category: 'Aventura', image: '/fundobackyardigans.jpg', accent: '#7c5cff', description: 'Cinco animaizinhos coloridos viajam para lugares imaginários e vivem grandes aventuras no quintal de casa. Os episódios apresentam musicais de gêneros diferentes e dança.', episodes: [
    { title: 'O tesouro do pirata', duration: '25 min', image: '/backyardigans/ep1.jpeg', sinopse: 'Uniqua e Austin são piratas corajosos que estão procurando um tesouro escondido depois de encontrar a metade de um mapa, mas não sabem que Pablo e Tyrone estão com a outra parte e também procuram pelo tesouro.' },
    { title: 'O coração da floresta', duration: '25 min', image: '/backyardigans/ep2.jpeg', sinopse:'Tyrone é Tarzan, e assim são Pablo e Austin. Com Uniqua, eles têm a missão de ajudar um amigo a encontrar sua casa na selva.' },
  ] },
  { id: 'peixonauta', title: 'Peixonauta', category: 'Aventura', image: '/peixonautafundo.jpg', accent: '#ff8b3d', description: `O agente secreto Peixonauta possui um traje especial que o permite voar e respirar fora d'água. O peixe é um detetive profissional que conta com a ajuda de seus amigos Marina, uma criança, e Zico, um macaco. Juntos, eles vivem incríveis aventuras no Parque das Árvores Felizes, dentro e fora d'água. Os mistérios são resolvidos com a ajuda da Pop, uma bola mágica e colorida que sempre envia pistas para os três.`, episodes: [
    { title: 'O Caso do Coelho Desanimado', duration: '11 min', image: '/peixonauta/ep1/capaep.webp', sinopse: 'Zico apresenta um novo amigo: um coelho chamado Eddy, que é um ótimo corredor. Ninguém corre mais rápido que ele! Até que um dia as coisas mudam... Eddy está cansado demais. O que está acontecendo com ele?' },
    
  ] },
  { id: 'mecanimais', title: 'Mecanimais', category: 'Aventura', image: '/mecafundo.jpg', accent: '#ed5aa8', description: 'Esta animação, especificamente concebida para pré-escolares, conta as aventuras de uma equipe de animais robôs com superpoderes que partem em aventuras para ajudarem uns aos outros e, ao mesmo tempo, vão aprendendo coisas novas.', episodes: [
    { title: 'A plantação de turbo feijão', duration: '11 min', image: '/mecanimais/ep1/capaep.png', sinopse: 'A equipe precisa plantar o agitado Turbo Feijão, mas ele foge e fica preso em uma árvore de engrenagens, exigindo trabalho em equipe para capturá-lo e fazê-lo brotar.' },
    { title: 'Ilha dos coelhos', duration: '11 min', image: '/mecanimais/ep2/capaep.jpg', sinopse: 'Os Mecanimais ajudam os coelhos a construir seu "Coelho Tocador" musical, tirando os esquilos-parafuso do caminho e resgatando um bloco que caiu.' },
    { title: 'Uma vaca encrencada', duration: '11 min', image: '/mecanimais/ep3/capaep.jpg', sinopse: 'A missão é guiar o gigante Castelo-Vaca até o pasto verde do outro lado de um labirinto de milho-foguete sem que ele bata no portão.' },
    { title: 'A ilha do avião-baleia', duration: '11 min', image: '/mecanimais/ep4/capaep.jpg', sinopse: 'O grupo precisa construir e prender uma pista de pouso longa o suficiente para que o enorme Avião-Baleia consiga aterrissar em segurança.' },
    { title: 'Ilha da dino montanha', duration: '11 min', image: '/mecanimais/ep5/capaep.jpg', sinopse: 'Os heróis viajam para remover uma engrenagem que ficou presa entre os dentes de um dinossauro mecânico gigante.' },
  ] },
  { id: 'pocoyo', title: 'Pocoyo', category: 'Aventura', image: '/pocoyofundo.webp', accent: '#ed5aa8', description: 'Quem disse que aprender não é divertido? De chapéu e roupas azuis, Pocoyo faz de cada dia uma inesquecível aventura enquanto explora o mundo ao seu redor ao lado de seus amigos, o que inclui um pato amarelo, uma elefanta rosa, um pássaro dorminhoco e a cadelinha Loula.', episodes: [
    { title: 'O Guarda-Chuva', duration: '7 min', image: '/pocoyo/ep1.jpg', sinopse: 'Pocoyo encontra um guarda-chuva e tenta descobrir sua utilidade junto com seus amigos até começar a chover.' },
    
  ] },
]

export function getRandomShow(): Show {
  const randomIndex = Math.floor(Math.random() * shows.length)
  return shows[randomIndex]
}
// Service worker mínimo — existe principalmente para o navegador permitir
// "Adicionar à tela inicial" no celular. Não faz cache agressivo para não
// esconder atualizações da Samantah.

self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Passa direto para a rede — sem cache offline por enquanto.
  event.respondWith(fetch(event.request));
});

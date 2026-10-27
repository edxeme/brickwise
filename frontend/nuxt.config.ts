export default defineNuxtConfig({
  modules: ['@nuxtjs/tailwindcss'],
  runtimeConfig: {
    public: {
      apiBase: process.env.BRICKWISE_API_BASE || 'http://localhost:8000/graphql',
    },
  },
})

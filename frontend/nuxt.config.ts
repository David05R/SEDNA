import tailwindcss from "@tailwindcss/vite";
// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: true },
  css: ['~/assets/css/main.css', 'leaflet/dist/leaflet.css'],
  vite: {
    plugins: [
      tailwindcss(),
    ],
    optimizeDeps: {
      include: ['leaflet'],
    },
    ssr: {
      noExternal: ['leaflet', '@vue-leaflet/vue-leaflet'],
    },
  },

  modules: [
    '@nuxt/content',
    '@nuxt/eslint',
    '@nuxt/test-utils', 
    '@nuxt/scripts',
    '@nuxt/image',
    '@nuxt/ui'
  ]
})
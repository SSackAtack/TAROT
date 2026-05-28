import { defineConfig } from 'vite'

export default defineConfig({
  server: {
    fs: {
      allow: [
        '..' // Pozwala Vite czytać pliki grafik z /biblioteka_talii/
      ]
    }
  }
})

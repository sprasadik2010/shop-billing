import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
// https://vitejs.dev/config/
export default defineConfig({
    base: "./", // <-- THIS FIXES ERR_FILE_NOT_FOUND IN ELECTRON BUILD
    plugins: [react(), tailwindcss()],
    server: {
        port: 5173,
        host: true
    }
});

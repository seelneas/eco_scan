import { defineConfig } from 'vite';
import { resolve } from 'path';
import { viteStaticCopy } from 'vite-plugin-static-copy';

export default defineConfig({
    build: {
        outDir: 'dist',
        rollupOptions: {
            input: {
                popup: resolve(__dirname, 'popup.html'),
                background: resolve(__dirname, 'src/background.js'),
                contentScript: resolve(__dirname, 'src/contentScript.js'),
            },
            output: {
                entryFileNames: (chunkInfo) => {
                    return chunkInfo.name === 'background' || chunkInfo.name === 'contentScript'
                        ? 'src/[name].js'
                        : '[name].js';
                },
            },
        },
    },
    plugins: [
        viteStaticCopy({
            targets: [
                { src: 'manifest.json', dest: '.' },
                { src: 'icons/*', dest: 'icons' },
                { src: 'styles/*', dest: 'styles' }
            ]
        })
    ]
});

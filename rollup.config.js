import { defineConfig } from 'rollup';
import css from 'rollup-plugin-css-only';

export default defineConfig({
  input: 'src/App.jsx',
  output: {
    file: 'dist/bundle.js',
    format: 'esm',
  },
  plugins: [
    css({ output: 'dist/bundle.css' }),
    // other plugins
  ],
});

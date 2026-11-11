/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        gold: {
          400: '#e5b95f',
          500: '#d4a34b',
          600: '#b37c07',
          700: '#92400e',
        },
        tarnished: {
          950: '#0b0c0e',
          900: '#121418',
          850: '#171a20',
          800: '#1d2129',
          700: '#282e3a',
          600: '#384152',
          500: '#4e5a70',
        }
      },
      fontFamily: {
        serif: ['Cinzel', 'Trajan Pro', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
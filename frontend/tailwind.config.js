/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: '#0f3d5c',
        'navy-dark': '#0b2e46',
        teal: '#0f766e',
        mist: '#f5f8fa',
      },
    },
  },
  plugins: [],
}

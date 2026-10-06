/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        oras: {
          // Backgrounds
          bg:            '#3D6B50',
          surface:       '#FFFFFF',
          'surface-alt': '#FAF9F7',
          // Borders
          border:        '#E8E6E1',
          'border-focus':'#C5C0B6',
          // Text
          text:          '#2D2A26',
          'text-sec':    '#78746B',
          'text-muted':  '#A8A49C',
          // Accent
          accent:        '#3D6B50',
          'accent-light':'#EBF2ED',
          'accent-sec':  '#5B8A6F',
          // Status
          warn:          '#C27D3A',
          error:         '#B54A4A',
          'error-light': '#FDF0F0',
          success:       '#3D7A5A',
          // Department colours
          'dept-rd':     '#4A7B9D',
          'dept-sales':  '#C27D3A',
          'dept-ops':    '#3D7A5A',
          'dept-mkt':    '#8B6BAE',
        },
      },
      fontFamily: {
        sans: ["'DM Sans'", 'sans-serif'],
        mono: ["'DM Mono'", 'monospace'],
      },
    },
  },
  plugins: [],
}

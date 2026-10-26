/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Dark navy SOC surface palette
        navy: {
          950: '#060b18',
          900: '#0a1120',
          850: '#0d1526',
          800: '#111c31',
          700: '#17253f',
          600: '#1f3050',
          500: '#2a3d63',
        },
        // Severity language used consistently across charts, badges and borders
        safe: '#22c55e',
        info: '#38bdf8',
        warn: '#f59e0b',
        danger: '#ef4444',
        critical: '#dc2626',
        accent: {
          DEFAULT: '#22d3ee',
          soft: '#67e8f9',
          deep: '#0891b2',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Cascadia Code', 'Consolas', 'monospace'],
      },
      boxShadow: {
        panel: '0 1px 0 0 rgba(255,255,255,0.04) inset, 0 12px 32px -12px rgba(0,0,0,0.65)',
        glow: '0 0 0 1px rgba(34,211,238,0.25), 0 8px 28px -8px rgba(34,211,238,0.35)',
      },
      keyframes: {
        'fade-in': {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'slide-in': {
          '0%': { opacity: '0', transform: 'translateX(18px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-500px 0' },
          '100%': { backgroundPosition: '500px 0' },
        },
        'pulse-ring': {
          '0%': { boxShadow: '0 0 0 0 rgba(34,211,238,0.45)' },
          '70%': { boxShadow: '0 0 0 10px rgba(34,211,238,0)' },
          '100%': { boxShadow: '0 0 0 0 rgba(34,211,238,0)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.28s ease-out both',
        'slide-in': 'slide-in 0.3s ease-out both',
        shimmer: 'shimmer 1.6s linear infinite',
        'pulse-ring': 'pulse-ring 2.2s ease-out infinite',
      },
    },
  },
  plugins: [],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          DEFAULT: '#0a0a0b',
          50: '#111113',
          100: '#18181b',
          200: '#1f1f23',
          300: '#27272a',
        },
        accent: {
          DEFAULT: 'rgba(255,255,255,0.85)',
          light: 'rgba(255,255,255,0.95)',
          dark: 'rgba(255,255,255,0.6)',
          muted: 'rgba(255,255,255,0.4)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease forwards',
        'slide-up': 'slideUp 0.6s ease forwards',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'gradient-x': 'gradientX 6s ease infinite',
        'text-reveal': 'textReveal 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'gradient-shift': 'gradientShift 4s ease infinite',
        'count-up': 'countUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'subtle-pulse': 'subtlePulse 3s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(255,255,255,0.05)' },
          '100%': { boxShadow: '0 0 40px rgba(255,255,255,0.08)' },
        },
        gradientX: {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        textReveal: {
          '0%': { opacity: '0', transform: 'translateY(24px) rotateX(40deg)', filter: 'blur(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0) rotateX(0deg)', filter: 'blur(0)' },
        },
        gradientShift: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' },
        },
        countUp: {
          '0%': { opacity: '0', transform: 'translateY(16px) scale(0.9)' },
          '60%': { opacity: '1', transform: 'translateY(-4px) scale(1.02)' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        subtlePulse: {
          '0%, 100%': { opacity: '0.6' },
          '50%': { opacity: '1' },
        },
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-accent': 'linear-gradient(135deg, rgba(255,255,255,0.85) 0%, rgba(255,255,255,0.95) 100%)',
        'gradient-card': 'linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)',
      },
    },
  },
  plugins: [],
}

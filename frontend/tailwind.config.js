/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Onest', 'ui-sans-serif', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        // Apple-inspired Minimal Palette for AgentForge AI
        background: '#FFFFFF',
        foreground: '#111111',
        muted: '#777777',
        dark: {
          DEFAULT: '#0A0A0A',
          hover: '#1F1F1F',
        },
        surface: {
          light: '#F7F6F4',
          secondary: '#EFECE8',
          DEFAULT: '#F7F6F4',
        },
        border: {
          light: '#EAE8E5',
          DEFAULT: '#EAE8E5',
          dark: '#D8D5D0',
        },
        brand: {
          orange: '#B15F2C',
          lightOrange: '#CF8047',
          warmBg: '#FAF5F1',
          DEFAULT: '#B15F2C',
        },
        // Soft Semantic Status Colors
        success: {
          bg: '#E8F5E9',
          border: '#C8E6C9',
          text: '#2E7D32',
          DEFAULT: '#10B981',
        },
        error: {
          bg: '#FFEBEE',
          border: '#FFCDD2',
          text: '#D32F2F',
          DEFAULT: '#EF4444',
        },
        warning: {
          bg: '#FFF3E0',
          border: '#FFE0B2',
          text: '#ED6C02',
          DEFAULT: '#F59E0B',
        },
      },
      boxShadow: {
        'subtle': '0 1px 3px rgba(0, 0, 0, 0.03), 0 1px 2px rgba(0, 0, 0, 0.02)',
        'card': '0 2px 12px -2px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02)',
        'card-hover': '0 12px 28px -4px rgba(0, 0, 0, 0.06), 0 4px 10px -2px rgba(0, 0, 0, 0.02)',
        'elevated': '0 20px 40px -8px rgba(0, 0, 0, 0.08), 0 8px 16px -4px rgba(0, 0, 0, 0.03)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.04)',
        'glass-hover': '0 14px 44px 0 rgba(0, 0, 0, 0.08)',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
        '3xl': '24px',
        '4xl': '32px',
      },
    },
  },
  plugins: [],
}

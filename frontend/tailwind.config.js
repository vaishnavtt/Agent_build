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
        // Lumora Palette
        background: '#FFFFFF',
        foreground: '#111111',
        muted: '#8D8D8D',
        dark: {
          DEFAULT: '#0A0A0A',
          hover: '#1F1F1F',
        },
        surface: {
          light: '#F1F0EE',
          secondary: '#E3E2DF',
          DEFAULT: '#F1F0EE',
        },
        border: {
          light: '#E6E5E2',
          DEFAULT: '#E6E5E2',
          dark: '#D1D0CD',
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
          DEFAULT: '#2E7D32',
        },
        error: {
          bg: '#FFEBEE',
          border: '#FFCDD2',
          text: '#D32F2F',
          DEFAULT: '#D32F2F',
        },
        warning: {
          bg: '#FFF3E0',
          border: '#FFE0B2',
          text: '#ED6C02',
          DEFAULT: '#ED6C02',
        },
      },
      boxShadow: {
        'subtle': '0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.02)',
        'card': '0 4px 14px rgba(0, 0, 0, 0.04), 0 1px 3px rgba(0, 0, 0, 0.02)',
        'card-hover': '0 8px 24px rgba(0, 0, 0, 0.06), 0 2px 6px rgba(0, 0, 0, 0.03)',
        'elevated': '0 16px 36px -4px rgba(0, 0, 0, 0.08), 0 6px 16px -6px rgba(0, 0, 0, 0.04)',
      },
      borderRadius: {
        'xl': '12px',
        '2xl': '16px',
        '3xl': '24px',
      },
    },
  },
  plugins: [],
}

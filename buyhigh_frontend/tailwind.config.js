const colors = require('tailwindcss/colors');

module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        'sans': ['Inter', 'sans-serif'],
        'pixel': ['"Press Start 2P"', 'cursive'],
      },
      colors: {
        'neo': {
          'purple': '#8b5cf6',
          'blue': '#3b82f6',
          'cyan': '#06b6d4',
          'pink': '#ec4899',
          'amber': '#f59e0b',
          'emerald': '#10b981',
          'red': '#ef4444'
        },
        'game': {
          'green': '#10b981',
          'red': '#ef4444',
          'gold': '#f59e0b',
          'blue': '#3b82f6',
          'pink': '#ec4899',
        }
      },
      boxShadow: {
        'neo': '0 0 10px rgba(139, 92, 246, 0.5), 0 0 20px rgba(139, 92, 246, 0.3)',
        'neo-lg': '0 0 15px rgba(139, 92, 246, 0.5), 0 0 30px rgba(139, 92, 246, 0.3)',
        'pixel': '4px 4px 0px 0px rgba(0,0,0,0.2)',
        'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.37)',
      },
      animation: {
        'float': 'float 3s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 3s infinite',
        'spin-slow': 'spin 6s linear infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
        'gradient': 'gradient 15s ease infinite',
        'blur-in': 'blurIn 0.7s ease forwards',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(139, 92, 246, 0.5), 0 0 10px rgba(139, 92, 246, 0.3)' },
          '100%': { boxShadow: '0 0 15px rgba(139, 92, 246, 0.6), 0 0 30px rgba(139, 92, 246, 0.4)' }
        },
        gradient: {
          '0%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
          '100%': { backgroundPosition: '0% 50%' }
        },
        blurIn: {
          '0%': { filter: 'blur(10px)', opacity: 0 },
          '100%': { filter: 'blur(0)', opacity: 1 }
        }
      },
      backdropBlur: {
        xs: '2px',
      }
    }
  },
  plugins: [
    // require('@tailwindcss/typography'),
  ],
  safelist: [
    // Dynamisch generierte Klassen für Farben
    {
      pattern: /bg-(red|blue|green|yellow|purple|pink|indigo|teal|orange|rose)-(400|500|600|900)/,
      variants: ['hover', 'dark'],
    },
    {
      pattern: /from-(red|blue|green|yellow|purple|pink|indigo|teal|orange|rose)-(500|600)/,
      variants: ['dark'],
    },
    {
      pattern: /to-(red|blue|green|yellow|purple|pink|indigo|teal|orange|rose)-(500|600)/,
      variants: ['dark'],
    },
    {
      pattern: /border-(red|blue|green|yellow|purple|pink|indigo|teal|orange|rose)-(400|500|600)/,
      variants: ['hover'],
    },
    {
      pattern: /text-(red|blue|green|yellow|purple|pink|indigo|teal|orange|rose)-(400|500)/,
      variants: ['dark'],
    },
  ]
}

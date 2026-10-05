/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Sampled from the Beijing National Day School official color logo.
        brand: { red: '#e8340c', yellow: '#f5a100', green: '#81b934', blue: '#0b75be' },
        primary: {
          50: '#fff5f1',
          100: '#ffe6da',
          200: '#ffc9b4',
          300: '#ffa285',
          400: '#fb7550',
          500: '#e8340c',
          600: '#cf2e0b',
          700: '#ab280f',
          800: '#8b2513',
          900: '#732416',
          950: '#3f1008'
        },
        gray: {
          50: '#f8f9fb',
          100: '#f0f2f5',
          200: '#dfe4ea',
          300: '#c4cdd7',
          400: '#96a3b1',
          500: '#657589',
          600: '#4c5d72',
          700: '#394a60',
          800: '#27394d',
          900: '#192b3f',
          950: '#0f1b2a'
        },
        accent: {
          50: '#fffaf0',
          100: '#fff0cc',
          200: '#ffe199',
          300: '#ffd066',
          400: '#ffc038',
          500: '#f5a100',
          600: '#c67b00',
          700: '#9d5e05',
          800: '#804a0c',
          900: '#693e10',
          950: '#3d2107'
        },
        dark: {
          50: '#f3f7fc',
          100: '#e5eef7',
          200: '#cbdcec',
          300: '#aac5dd',
          400: '#82a6c7',
          500: '#5d84a7',
          600: '#406583',
          700: '#2e4c65',
          800: '#203a50',
          900: '#162c40',
          950: '#0c1c2b'
        }
      },
      fontFamily: {
        sans: [
          'Inter',
          'system-ui',
          '-apple-system',
          'BlinkMacSystemFont',
          'Segoe UI',
          'Roboto',
          'Helvetica Neue',
          'Arial',
          'PingFang SC',
          'Hiragino Sans GB',
          'Microsoft YaHei',
          'sans-serif'
        ],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace']
      },
      boxShadow: {
        glass: '0 8px 32px rgba(0, 0, 0, 0.08)',
        'glass-sm': '0 4px 16px rgba(0, 0, 0, 0.06)',
        glow: '0 0 20px rgba(232, 52, 12, 0.25)',
        'glow-lg': '0 0 40px rgba(232, 52, 12, 0.35)',
        card: '0 2px 5px rgba(25, 43, 63, 0.025)',
        'card-hover': '0 10px 40px rgba(0, 0, 0, 0.08)',
        'inner-glow': 'inset 0 1px 0 rgba(255, 255, 255, 0.1)'
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-primary': 'linear-gradient(135deg, #e8340c 0%, #cf2e0b 100%)',
        'gradient-dark': 'linear-gradient(135deg, #203a50 0%, #162c40 100%)',
        'gradient-glass':
          'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
        'mesh-gradient':
          'radial-gradient(at 40% 20%, rgba(232, 52, 12, 0.12) 0px, transparent 50%), radial-gradient(at 80% 0%, rgba(11, 117, 190, 0.08) 0px, transparent 50%), radial-gradient(at 0% 50%, rgba(232, 52, 12, 0.08) 0px, transparent 50%)'
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'scale-in': 'scaleIn 0.2s ease-out',
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        shimmer: 'shimmer 2s linear infinite',
        glow: 'glow 2s ease-in-out infinite alternate'
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        slideDown: {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' }
        },
        scaleIn: {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' }
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' }
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(232, 52, 12, 0.25)' },
          '100%': { boxShadow: '0 0 30px rgba(232, 52, 12, 0.4)' }
        }
      },
      backdropBlur: {
        xs: '2px'
      },
      borderRadius: {
        '4xl': '2rem'
      }
    }
  },
  plugins: []
}

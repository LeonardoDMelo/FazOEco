/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-outfit)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        // Azul escuro — menus, rodapé, contraste e confiança
        brand: {
          50: "#eef3f9",
          100: "#d9e4f2",
          200: "#b4c8e3",
          300: "#87a5cb",
          400: "#5a7fad",
          500: "#3b5f90",
          600: "#2a4a75",
          700: "#1f3a5f",
          800: "#162b49",
          900: "#0f1f36",
          950: "#0a1524",
        },
        // Laranja enérgico — CTAs e destaques de ação
        accent: {
          50: "#fff7ed",
          100: "#ffedd5",
          200: "#fed7aa",
          300: "#fdba74",
          400: "#fb923c",
          500: "#f97316",
          600: "#ea580c",
          700: "#c2410c",
          800: "#9a3412",
          900: "#7c2d12",
          950: "#431407",
        },
      },
    },
  },
  plugins: [],
};

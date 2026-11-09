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
        // Vermelho vibrante (clareado e depois escurecido 30%)
        brand: {
          50: "#f8f3f4",
          100: "#f2e8ea",
          200: "#e7d3d8",
          300: "#d8b9c0",
          400: "#c69aa4",
          500: "#b87f8c",
          600: "#a86373",
          700: "#945765",
          800: "#834d5a",
          900: "#72434e",
          950: "#5c363f",
        },
        // Amarelo quente — cupons, frete grátis e preço novo
        accent: {
          50: "#fefce8",
          100: "#fef9c3",
          200: "#fef08a",
          300: "#fde047",
          400: "#facc15",
          500: "#eab308",
          600: "#ca8a04",
          700: "#a16207",
          800: "#854d0e",
          900: "#713f12",
          950: "#422006",
        },
      },
    },
  },
  plugins: [],
};

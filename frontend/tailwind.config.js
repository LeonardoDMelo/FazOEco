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
        // Vermelho vibrante — 10% mais claro
        brand: {
          50: "#fdf0f3",
          100: "#fae2e8",
          200: "#f6cad4",
          300: "#f1aab9",
          400: "#eb849a",
          500: "#e66380",
          600: "#e04164",
          700: "#c53958",
          800: "#af334e",
          900: "#982c44",
          950: "#7b2437",
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

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
        // Vermelho vibrante com 20% menos saturação (menos vivo)
        brand: {
          50: "#f7f3f4",
          100: "#f1e9eb",
          200: "#e5d5d9",
          300: "#d5bcc2",
          400: "#c29ea7",
          500: "#b2858f",
          600: "#a16a77",
          700: "#8e5d69",
          800: "#7e535d",
          900: "#6d4851",
          950: "#593a41",
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

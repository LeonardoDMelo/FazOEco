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
        // Vermelho vibrante 50% mais claro — banners, % OFF e ofertas relâmpago
        brand: {
          50: "#fff8f8",
          100: "#fff2f2",
          200: "#fee6e9",
          300: "#fed2d7",
          400: "#fdb8c2",
          500: "#fa9fae",
          600: "#f08ea4",
          700: "#de889e",
          800: "#cf889c",
          900: "#c4899b",
          950: "#a6828c",
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

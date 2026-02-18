/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html"],
  theme: {
    extend: {
      colors: {
        base: {
          100: "#111111",
          200: "#333333",
          300: "#555555",
          400: "#777777",
          500: "#999999",
        },
        love: {
          100: "#f2c0c0",
          200: "#e37979",
          300: "#e76464",
          400: "#b65e5e",
          500: "#983434",
        },
      },
      boxShadow: {
        soft: "0 8px 30px rgba(0,0,0,.24)",
      },
      fontFamily: {
        sans: ["Poppins", "sans-serif"],
        serif: ["Cormorant Garamond", "serif"],
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#08f9f5",   // bright-blue cyan
          dark:    "#008d97",   // deeper shade for dark UI
        },
      },
    },
  },
  plugins: [],
};
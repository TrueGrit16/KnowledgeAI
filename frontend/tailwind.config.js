/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: "#08f9f5",
        "brand-dark": "#008d97",
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
    /* other plugins… */
  ],
};

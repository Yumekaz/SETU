/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        setu: {
          navy: "#0f172a",
          accent: "#0ea5e9",
          warn: "#f59e0b",
          danger: "#ef4444",
        },
      },
    },
  },
  plugins: [],
};
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Foundations
        primary: "#FFD700",
        "gold-soft": "#E6C97A",
        dark: "#0A0F1C",
        surface: "#111111",
        "surface-hover": "#1A1A1A",
        "text-primary": "#EAEAEA",
        "text-secondary": "#AAAAAA",
        danger: "#FF4C4C",
        // Legacy
        black: "#0B0B0B",
        darkGrey: "#121212",
        cardBg: "#1A1A1A",
        gold: "#D4AF37",
        lightGold: "#FFD700",
        greenSafe: "#4ADE80",
        yellowSuspicious: "#FACC15",
        redDanger: "#F87171",
      },
      fontFamily: {
        poppins: ["Poppins", "sans-serif"],
        orbitron: ["Orbitron", "monospace"],
        mono: ["Fira Code", "monospace"],
      },
      spacing: {
        18: "4.5rem",
        88: "22rem",
      },
    },
  },
  plugins: [],
};
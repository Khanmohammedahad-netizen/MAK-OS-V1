/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#08080A",
        surface: {
          DEFAULT: "rgba(255,255,255,0.05)",
          hover: "rgba(255,255,255,0.08)",
          active: "rgba(255,255,255,0.12)",
        },
        gold: {
          DEFAULT: "#C9A84C",
          light: "#E8C97A",
          dark: "#A8893A",
          muted: "rgba(201,168,76,0.15)",
        },
        border: "rgba(255,255,255,0.10)",
        muted: "rgba(255,255,255,0.50)",
        destructive: "#EF4444",
        success: "#22C55E",
        info: "#3B82F6",
      },
      fontFamily: {
        display: ['"Cormorant Garamond"', "serif"],
        sans: ['"DM Sans"', "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
      },
      backdropBlur: {
        xl: "24px",
      },
    },
  },
  plugins: [],
};

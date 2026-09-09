import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Pavo Cloud: deep navy ground, electric blue accent.
        navy: {
          950: "#050D1A",
          900: "#0A1B33",
          800: "#102544",
          700: "#193357",
          600: "#24466F",
          400: "#5B7BA6",
          200: "#A8BCD8",
        },
        electric: {
          600: "#0B5CD6",
          500: "#2F80FF",
          400: "#4D9BFF",
          300: "#7FB8FF",
          100: "#DCEAFF",
        },
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "sans-serif",
        ],
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      keyframes: {
        "fade-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(47,128,255,0.45)" },
          "70%": { boxShadow: "0 0 0 10px rgba(47,128,255,0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(47,128,255,0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 320ms ease-out both",
        "pulse-ring": "pulse-ring 1.6s ease-out infinite",
      },
    },
  },
  plugins: [],
};

export default config;

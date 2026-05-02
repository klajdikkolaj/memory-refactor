import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: "#111411",
        paper: "#f7f8f4",
        line: "#dfe4dc",
        moss: "#2f6f4e",
        flame: "#c65f2a",
      },
      boxShadow: {
        panel: "0 18px 50px rgba(17, 20, 17, 0.08)",
      },
    },
  },
  plugins: [],
};

export default config;

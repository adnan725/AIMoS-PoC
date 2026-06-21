/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#11203B",        // deep institutional blue (not cliché black)
        paper: "#F3EFE7",      // warm paper surface
        surface: "#FBF9F5",
        line: "#D8D0C2",
        accent: "#C2410C",     // restrained warm accent for focus/active
      },
      fontFamily: {
        display: ['"Space Grotesk"', "system-ui", "sans-serif"],
        body: ['"Inter"', "system-ui", "sans-serif"],
        mono: ['"IBM Plex Mono"', "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

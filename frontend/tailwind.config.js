/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        "ml-red": "#A20B0B",
        "ml-red-light": "#F6C9C9",
        "ml-red-disabled": "#C07070",
        "ml-blue": "#1C5386",
        "ml-blue-lighter": "#DCE3EB",
        "white-200": "#F7F9FA",
        "white-300": "#ECEEF0",
        "ml-grey-lightest": "#E4E4E4",
        "ml-grey-lighter": "#D0D0D0",
        "ml-grey-dark": "#5C5C5C",
        "ml-grey-darker": "#3D4552",
        "muted-foreground": "#9C9C9C",
        destructive: "#DC2626",
        "destructive-bg": "#FEF2F2",
        "hf-panel": "#1B1B1B",
        "hf-panel-h2": "#626262",
        "hf-panel-h3": "#44506A",
        "hf-panel-pill": "#2A2A2A",
        "hf-panel-pill-border": "#3A3A3A",
        "hf-panel-step": "#D5D5D5",
        canvas: "rgb(var(--color-canvas) / <alpha-value>)",
        "canvas-accent": "rgb(var(--color-canvas-accent) / <alpha-value>)",
        surface: {
          base: "rgb(var(--color-surface-base) / <alpha-value>)",
          elevated: "rgb(var(--color-surface-elevated) / <alpha-value>)",
          tint: "rgb(var(--color-surface-tint) / <alpha-value>)",
        },
        ink: {
          base: "rgb(var(--color-ink-base) / <alpha-value>)",
          muted: "rgb(var(--color-ink-muted) / <alpha-value>)",
          inverse: "rgb(var(--color-ink-inverse) / <alpha-value>)",
        },
        line: {
          subtle: "rgb(var(--color-line-subtle) / <alpha-value>)",
          strong: "rgb(var(--color-line-strong) / <alpha-value>)",
        },
        brand: {
          DEFAULT: "rgb(var(--color-brand) / <alpha-value>)",
          strong: "rgb(var(--color-brand-strong) / <alpha-value>)",
          soft: "rgb(var(--color-brand-soft) / <alpha-value>)",
        },
        human: {
          DEFAULT: "rgb(var(--color-human) / <alpha-value>)",
          soft: "rgb(var(--color-human-soft) / <alpha-value>)",
        },
        ai: {
          DEFAULT: "rgb(var(--color-ai) / <alpha-value>)",
          soft: "rgb(var(--color-ai-soft) / <alpha-value>)",
        },
        success: {
          DEFAULT: "rgb(var(--color-success) / <alpha-value>)",
          soft: "rgb(var(--color-success-soft) / <alpha-value>)",
        },
        danger: {
          DEFAULT: "rgb(var(--color-danger) / <alpha-value>)",
          soft: "rgb(var(--color-danger-soft) / <alpha-value>)",
        },
        warning: {
          DEFAULT: "rgb(var(--color-warning) / <alpha-value>)",
          soft: "rgb(var(--color-warning-soft) / <alpha-value>)",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["'Exo 2'", "'Instrument Sans'", "system-ui", "sans-serif"],
        ui: ["'Instrument Sans'", "system-ui", "sans-serif"],
        serif: ["'Source Serif 4'", "Georgia", "serif"],
      },
      boxShadow: {
        panel: "0 24px 80px rgba(15, 23, 42, 0.12)",
        float: "0 14px 40px rgba(76, 38, 109, 0.14)",
      },
      borderRadius: {
        "radius-sm": "4px",
        "radius-xs": "2px",
        panel: "1.5rem",
        pill: "999px",
      },
      spacing: {
        18: "4.5rem",
        22: "5.5rem",
      },
      backgroundImage: {
        "page-grid":
          "radial-gradient(circle at top left, rgba(189, 168, 255, 0.18), transparent 28%), radial-gradient(circle at bottom right, rgba(189, 214, 186, 0.22), transparent 24%)",
      },
    },
  },
  plugins: [],
};

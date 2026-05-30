/**
 * Tailwind preset — design tokens(CSS variables) 참조.
 * next.config에서 presets: [require('./tailwind.preset')] 형태로 사용.
 *
 * Figma 교체 후 tokens.css만 갱신하면 theme 색이 따라감.
 */
const preset = {
  theme: {
    extend: {
      colors: {
        background: "var(--color-background)",
        surface: "var(--color-surface)",
        "surface-elevated": "var(--color-surface-elevated)",
        border: "var(--color-border)",
        "text-primary": "var(--color-text-primary)",
        "text-secondary": "var(--color-text-secondary)",
        accent: "var(--color-accent)",
        danger: "var(--color-danger)",
        warning: "var(--color-warning)",
      },
      spacing: {
        xs: "var(--spacing-xs)",
        sm: "var(--spacing-sm)",
        md: "var(--spacing-md)",
        lg: "var(--spacing-lg)",
        xl: "var(--spacing-xl)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
        full: "var(--radius-full)",
      },
      fontFamily: {
        sans: ["var(--font-family-sans)"],
      },
    },
  },
};

export default preset;

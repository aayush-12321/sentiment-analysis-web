import React from "react";
import { useTheme } from "../../context/ThemeContext";
import styles from "./ThemeToggle.module.css";

/* Sun icon — light mode indicator */
function SunIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle cx="10" cy="10" r="4" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M10 2v1.5M10 16.5V18M2 10h1.5M16.5 10H18M4.22 4.22l1.06 1.06M14.72 14.72l1.06 1.06M4.22 15.78l1.06-1.06M14.72 5.28l1.06-1.06"
        stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"
      />
    </svg>
  );
}

/* Moon icon — dark mode indicator */
function MoonIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path
        d="M17.5 10.9A7.5 7.5 0 019.1 2.5a7.5 7.5 0 100 15 7.5 7.5 0 008.4-6.6z"
        stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
      />
    </svg>
  );
}

export default function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      id="theme-toggle"
      className={styles.toggle}
      onClick={toggle}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Light mode" : "Dark mode"}
    >
      <span className={`${styles.track} ${isDark ? styles.trackDark : styles.trackLight}`}>
        <span className={`${styles.thumb} ${isDark ? styles.thumbDark : styles.thumbLight}`}>
          <span className={styles.icon}>
            {isDark ? <MoonIcon /> : <SunIcon />}
          </span>
        </span>
      </span>
    </button>
  );
}

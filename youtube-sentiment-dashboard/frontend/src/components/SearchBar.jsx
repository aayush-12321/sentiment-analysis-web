import React, { useState, useRef, useEffect } from "react";
import styles from "./SearchBar.module.css";

const SUGGESTIONS = ["Nike", "Apple", "Tesla", "Netflix", "Samsung", "Adidas", "OpenAI", "Spotify"];

const SOURCES = [
  { value: "youtube", label: "YouTube",        icon: "▶" },
  { value: "reddit",  label: "Reddit",         icon: "🔴" },
  { value: "both",    label: "YouTube + Reddit", icon: "⊕" },
];

export default function SearchBar({ onSearch, loading, history = [] }) {
  const [value,     setValue]     = useState("");
  const [showDrop,  setShowDrop]  = useState(false);
  const [maxItems,  setMaxItems]  = useState(5);
  const [source,    setSource]    = useState("youtube");
  const inputRef = useRef(null);
  const dropRef  = useRef(null);

  useEffect(() => {
    const handler = (e) => {
      if (!dropRef.current?.contains(e.target) && !inputRef.current?.contains(e.target))
        setShowDrop(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if (!value.trim() || loading) return;
    setShowDrop(false);
    onSearch(value.trim(), { maxVideos: maxItems, source });
  };

  const handleSuggestion = (kw) => {
    setValue(kw);
    setShowDrop(false);
    onSearch(kw, { maxVideos: maxItems, source });
  };

  const dropItems = [
    ...history.slice(0, 5),
    ...SUGGESTIONS.filter((s) => !history.includes(s)),
  ]
    .filter((s) => !value || s.toLowerCase().includes(value.toLowerCase()))
    .slice(0, 8);

  const sliderLabel =
    source === "youtube" ? "Videos to scan" :
    source === "reddit"  ? "Posts to fetch" :
    "Items per source";

  return (
    <div className={styles.wrapper}>
      <div className={styles.hero}>
        <h1 className={styles.heroTitle}>
          How does the world <em>feel</em> about your brand?
        </h1>
        <p className={styles.heroSub}>
          Analyse YouTube comments, Reddit discussions, or both — powered by RoBERTa.
        </p>
      </div>

      {/* Source selector */}
      <div className={styles.sourceRow}>
        {SOURCES.map((s) => (
          <button
            key={s.value}
            type="button"
            className={`${styles.sourceBtn} ${source === s.value ? styles.sourceBtnActive : ""}`}
            onClick={() => setSource(s.value)}
            disabled={loading}
          >
            <span className={styles.sourceBtnIcon}>{s.icon}</span>
            {s.label}
          </button>
        ))}
      </div>

      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.inputWrap}>
          {/* Search icon */}
          <svg className={styles.searchIcon} viewBox="0 0 20 20" fill="none">
            <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" strokeWidth="1.5"/>
            <path d="M13 13l3.5 3.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>

          <input
            ref={inputRef}
            className={styles.input}
            type="text"
            placeholder="Search brand, keyword, or topic…"
            value={value}
            onChange={(e) => { setValue(e.target.value); setShowDrop(true); }}
            onFocus={() => setShowDrop(true)}
            disabled={loading}
            autoComplete="off"
            spellCheck={false}
          />

          {/* Dropdown */}
          {showDrop && dropItems.length > 0 && (
            <div className={styles.dropdown} ref={dropRef}>
              {history.length > 0 && (
                <p className={styles.dropLabel}>Recent searches</p>
              )}
              {dropItems.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={styles.dropItem}
                  onMouseDown={() => handleSuggestion(item)}
                >
                  <svg viewBox="0 0 16 16" fill="none" className={styles.dropIcon}>
                    <circle cx="6.5" cy="6.5" r="4" stroke="currentColor" strokeWidth="1.2"/>
                    <path d="M10 10l3 3" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
                  </svg>
                  {item}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Slider */}
        <div className={styles.controls}>
          <label className={styles.sliderLabel}>
            {sliderLabel}:
            <span className={styles.sliderValue}>{maxItems}</span>
          </label>
          <input
            type="range"
            min="1" max="20"
            value={maxItems}
            onChange={(e) => setMaxItems(Number(e.target.value))}
            className={styles.slider}
          />
        </div>

        <button
          type="submit"
          className={styles.btn}
          disabled={loading || !value.trim()}
        >
          {loading ? (
            <span className={styles.spinner} />
          ) : (
            <>
              Analyse
              <svg viewBox="0 0 16 16" fill="none" className={styles.btnIcon}>
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5"
                  strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </>
          )}
        </button>
      </form>
    </div>
  );
}

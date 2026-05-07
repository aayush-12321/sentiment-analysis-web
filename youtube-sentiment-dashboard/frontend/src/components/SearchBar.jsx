import React, { useState, useRef, useEffect } from "react";
import styles from "./SearchBar.module.css";

const SUGGESTIONS = ["Nike", "Apple", "Tesla", "Netflix", "Samsung", "Adidas", "OpenAI", "Spotify"];

export default function SearchBar({ onSearch, loading, history = [] }) {
  const [value, setValue]         = useState("");
  const [showDrop, setShowDrop]   = useState(false);
  const [maxVideos, setMaxVideos] = useState(5);
  const inputRef = useRef(null);
  const dropRef  = useRef(null);

  // Close dropdown on outside click
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
    onSearch(value.trim(), { maxVideos });
  };

  const handleSuggestion = (kw) => {
    setValue(kw);
    setShowDrop(false);
    onSearch(kw, { maxVideos });
  };

  // Combine history + static suggestions, de-duped
  const dropItems = [
    ...history.slice(0, 5),
    ...SUGGESTIONS.filter((s) => !history.includes(s)),
  ].filter((s) => !value || s.toLowerCase().includes(value.toLowerCase())).slice(0, 8);

  return (
    <div className={styles.wrapper}>
      <div className={styles.hero}>
        <h1 className={styles.heroTitle}>
          How does the world <em>feel</em> about your brand?
        </h1>
        <p className={styles.heroSub}>
          Enter any brand name or keyword to analyse thousands of YouTube comments instantly.
        </p>
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

        {/* Videos slider */}
        <div className={styles.controls}>
          <label className={styles.sliderLabel}>
            Videos to scan:
            <span className={styles.sliderValue}>{maxVideos}</span>
          </label>
          <input
            type="range"
            min="1" max="20"
            value={maxVideos}
            onChange={(e) => setMaxVideos(Number(e.target.value))}
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
                <path d="M3 8h10M9 4l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </>
          )}
        </button>
      </form>
    </div>
  );
}

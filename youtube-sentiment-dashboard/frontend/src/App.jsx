import React, { useState, useEffect } from "react";
import { useSentiment }   from "./hooks/useSentiment";
import { fetchHistory }   from "./utils/api";
import SearchBar          from "./components/SearchBar";
import StatCards          from "./components/StatCards";
import SentimentPieChart  from "./components/charts/SentimentPieChart";
import SentimentTrend     from "./components/charts/SentimentTrend";
import CommentTable       from "./components/CommentTable";
import ScoreGauge         from "./components/ScoreGauge";
import LoadingState       from "./components/ui/LoadingState";
import ErrorBanner        from "./components/ui/ErrorBanner";
import EmptyState         from "./components/ui/EmptyState";
import styles             from "./App.module.css";

export default function App() {
  const { data, loading, error, keyword, analyse } = useSentiment();
  const [history, setHistory] = useState([]);
  const [activeTab, setActiveTab] = useState("all");

  // Load search history on mount
  useEffect(() => {
    fetchHistory().then(setHistory).catch(() => {});
  }, []);

  // Refresh history after each successful search
  useEffect(() => {
    if (data) fetchHistory().then(setHistory).catch(() => {});
  }, [data]);

  const summary = data?.summary;

  return (
    <div className={styles.app}>
      {/*  Header  */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.logo}>
            <span className={styles.logoMark}>◈</span>
            <span className={styles.logoText}>SentimentScope</span>
            <span className={styles.logoBadge}>BETA</span>
          </div>
          <p className={styles.tagline}>YouTube Brand Intelligence</p>
        </div>
      </header>

      {/*  Search  */}
      <section className={styles.searchSection}>
        <SearchBar
          onSearch={analyse}
          loading={loading}
          history={history}
        />
      </section>

      {/*  Main content  */}
      <main className={styles.main}>
        {loading && <LoadingState keyword={keyword} />}

        {error && !loading && <ErrorBanner message={error} />}

        {!loading && !error && !data && <EmptyState />}

        {!loading && !error && data && (
          <>
            {/*  Result header  */}
            <div className={`${styles.resultHeader} fade-up`}>
              <div className={styles.resultKeyword}>
                <span className={styles.resultLabel}>Analysing</span>
                <h2 className={styles.resultTitle}>"{data.keyword}"</h2>
              </div>
              <div className={styles.resultMeta}>
                <span className={styles.metaBadge}>
                  {summary.total} comments · {data.cached ? "cached" : "live"}
                </span>
              </div>
            </div>

            {/*  Stat cards  */}
            <div className="fade-up fade-up-1">
              <StatCards summary={summary} />
            </div>

            {/*  Charts row  */}
            <div className={`${styles.chartsRow} fade-up fade-up-2`}>
              <div className={styles.chartCard}>
                <h3 className={styles.cardTitle}>Sentiment Distribution</h3>
                <SentimentPieChart summary={summary} />
              </div>

              <div className={styles.chartCard}>
                <h3 className={styles.cardTitle}>Sentiment Over Time</h3>
                <SentimentTrend trend={data.trend} />
              </div>

              <div className={styles.chartCard}>
                <h3 className={styles.cardTitle}>Overall Score</h3>
                <ScoreGauge score={summary.avg_score} />
              </div>
            </div>

            {/*  Comments  */}
            <div className={`${styles.commentsSection} fade-up fade-up-3`}>
              <div className={styles.tabRow}>
                <h3 className={styles.cardTitle}>Top Comments</h3>
                <div className={styles.tabs}>
                  {["all", "positive", "negative", "neutral"].map((t) => (
                    <button
                      key={t}
                      className={`${styles.tab} ${activeTab === t ? styles.tabActive : ""} ${styles[`tab_${t}`]}`}
                      onClick={() => setActiveTab(t)}
                    >
                      {t.charAt(0).toUpperCase() + t.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
              <CommentTable
                comments={
                  activeTab === "all"
                    ? data.comments
                    : data.topByLabel?.[activeTab] || []
                }
                activeTab={activeTab}
              />
            </div>
          </>
        )}
      </main>

      <footer className={styles.footer}>
        <p>SentimentScope · Powered by VADER + YouTube Data API v3</p>
      </footer>
    </div>
  );
}

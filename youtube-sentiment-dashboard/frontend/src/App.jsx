import React, { useState, useEffect } from "react";
import { useSentiment }         from "./hooks/useSentiment";
import { fetchHistory }         from "./utils/api";
import SearchBar                from "./components/SearchBar";
import StatCards                from "./components/StatCards";
import SourceBreakdownCards     from "./components/SourceBreakdownCards";
import AgreementBadge           from "./components/AgreementBadge";
import SentimentPieChart        from "./components/charts/SentimentPieChart";
import SentimentTrend           from "./components/charts/SentimentTrend";
import SourceComparisonBar      from "./components/charts/SourceComparisonBar";
import CommentTable             from "./components/CommentTable";
import ScoreGauge               from "./components/ScoreGauge";
import LoadingState             from "./components/ui/LoadingState";
import ErrorBanner              from "./components/ui/ErrorBanner";
import EmptyState               from "./components/ui/EmptyState";
import styles                   from "./App.module.css";

const SOURCE_LABELS = {
  youtube: "YouTube",
  reddit:  "Reddit",
  both:    "YouTube + Reddit",
};

export default function App() {
  const { data, loading, error, keyword, analyse } = useSentiment();
  const [history,   setHistory]   = useState([]);
  const [activeTab, setActiveTab] = useState("all");
  const [viewMode,  setViewMode]  = useState("combined"); // combined | youtube | reddit

  useEffect(() => { fetchHistory().then(setHistory).catch(() => {}); }, []);
  useEffect(() => { if (data) fetchHistory().then(setHistory).catch(() => {}); }, [data]);

  // Reset view mode when new data arrives
  useEffect(() => {
    if (data) setViewMode("combined");
  }, [data]);

  const summary    = data?.summary;
  const source     = data?.source || "youtube";
  const isBoth     = source === "both";
  const isReddit   = source === "reddit";

  // Comments to show based on view mode toggle
  const displayComments = () => {
    if (!data) return [];
    if (isBoth && viewMode === "youtube") {
      return data.youtube?.comments || [];
    }
    if (isBoth && viewMode === "reddit") {
      return data.reddit?.posts || [];
    }
    // "combined" or single-source
    if (activeTab === "all") return data.comments || [];
    return data.topByLabel?.[activeTab] || [];
  };

  const displaySummary = () => {
    if (!data) return null;
    if (isBoth && viewMode === "youtube") return data.youtube?.summary;
    if (isBoth && viewMode === "reddit")  return data.reddit?.summary;
    return summary;
  };

  const displayTrend = () => {
    if (!data) return [];
    if (isBoth && viewMode === "youtube") return data.youtube?.trend || [];
    if (isBoth && viewMode === "reddit")  return data.reddit?.trend  || [];
    return data.trend || [];
  };

  const currentSummary = displaySummary();

  return (
    <div className={styles.app}>

      {/* ── Header ── */}
      <header className={styles.header}>
        <div className={styles.headerInner}>
          <div className={styles.logo}>
            <span className={styles.logoMark}>◈</span>
            <span className={styles.logoText}>SentimentScope</span>
            <span className={styles.logoBadge}>BETA</span>
          </div>
          <p className={styles.tagline}>Multi-Source Brand Intelligence</p>
        </div>
      </header>

      {/* ── Search ── */}
      <section className={styles.searchSection}>
        <SearchBar onSearch={analyse} loading={loading} history={history} />
      </section>

      {/* ── Main ── */}
      <main className={styles.main}>
        {loading  && <LoadingState keyword={keyword} />}
        {error    && !loading && <ErrorBanner message={error} />}
        {!loading && !error && !data && <EmptyState />}

        {!loading && !error && data && (
          <>
            {/* Result header */}
            <div className={`${styles.resultHeader} fade-up`}>
              <div className={styles.resultKeyword}>
                <span className={styles.resultLabel}>Analysing</span>
                <h2 className={styles.resultTitle}>"{data.keyword}"</h2>
              </div>
              <div className={styles.resultMeta}>
                <span className={styles.sourceChip}>
                  {source === "youtube" && <span className={styles.ytDot} />}
                  {source === "reddit"  && <span className={styles.rdDot} />}
                  {source === "both"    && <><span className={styles.ytDot} /><span className={styles.rdDot} /></>}
                  {SOURCE_LABELS[source]}
                </span>
                <span className={styles.metaBadge}>
                  {currentSummary?.total?.toLocaleString() || 0} items · {data.cached ? "cached" : "live"}
                </span>
              </div>
            </div>

            {/* ── BOTH: Source breakdown + agreement ── */}
            {isBoth && (
              <div className={`fade-up fade-up-1`}>
                <h3 className={styles.sectionTitle}>Source Breakdown</h3>
                <SourceBreakdownCards
                  youtubeResult={data.youtube}
                  redditResult={data.reddit}
                />
                <div className={styles.agreementRow}>
                  <AgreementBadge score={data.agreementScore} />
                  <div className={styles.viewToggle}>
                    {["combined", "youtube", "reddit"].map((m) => (
                      <button
                        key={m}
                        className={`${styles.viewBtn} ${viewMode === m ? styles.viewBtnActive : ""}`}
                        onClick={() => setViewMode(m)}
                      >
                        {m === "combined" ? "Combined" : m === "youtube" ? "▶ YouTube" : "🔴 Reddit"}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Stat cards */}
            <div className={`fade-up ${isBoth ? "fade-up-2" : "fade-up-1"}`}>
              {currentSummary && <StatCards summary={currentSummary} />}
            </div>

            {/* Charts row */}
            <div className={`${styles.chartsRow} fade-up ${isBoth ? "fade-up-3" : "fade-up-2"}`}>
              <div className={styles.chartCard}>
                <h3 className={styles.cardTitle}>Sentiment Distribution</h3>
                {currentSummary && <SentimentPieChart summary={currentSummary} />}
              </div>

              {isBoth && viewMode === "combined" ? (
                <div className={styles.chartCard}>
                  <h3 className={styles.cardTitle}>YouTube vs Reddit</h3>
                  <SourceComparisonBar
                    youtubeResult={data.youtube}
                    redditResult={data.reddit}
                  />
                </div>
              ) : (
                <div className={styles.chartCard}>
                  <h3 className={styles.cardTitle}>Sentiment Over Time</h3>
                  <SentimentTrend trend={displayTrend()} />
                </div>
              )}

              <div className={styles.chartCard}>
                <h3 className={styles.cardTitle}>Overall Score</h3>
                {currentSummary && <ScoreGauge score={currentSummary.avg_score} />}
              </div>
            </div>

            {/* Comments / Posts */}
            <div className={`${styles.commentsSection} fade-up ${isBoth ? "fade-up-4" : "fade-up-3"}`}>
              <div className={styles.tabRow}>
                <h3 className={styles.cardTitle}>
                  {isReddit ? "Reddit Posts" : isBoth && viewMode === "reddit" ? "Reddit Posts" : "Top Comments"}
                </h3>
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
                comments={displayComments()}
                activeTab={activeTab}
              />
            </div>
          </>
        )}
      </main>

      <footer className={styles.footer}>
        <p>SentimentScope · Powered by RoBERTa · YouTube Data API · Reddit RSS</p>
      </footer>
    </div>
  );
}

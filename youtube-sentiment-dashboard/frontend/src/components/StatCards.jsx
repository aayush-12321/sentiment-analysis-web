import React from "react";
import styles from "./StatCards.module.css";

export default function StatCards({ summary }) {
  const cards = [
    {
      label:   "Total Comments",
      value:   summary.total.toLocaleString(),
      sub:     "analysed",
      color:   "accent",
      icon:    "💬",
    },
    {
      label:   "Positive",
      value:   `${summary.positivePercent}%`,
      sub:     `${summary.positive.toLocaleString()} comments`,
      color:   "positive",
      icon:    "↑",
      bar:     summary.positivePercent,
    },
    {
      label:   "Negative",
      value:   `${summary.negativePercent}%`,
      sub:     `${summary.negative.toLocaleString()} comments`,
      color:   "negative",
      icon:    "↓",
      bar:     summary.negativePercent,
    },
    {
      label:   "Neutral",
      value:   `${summary.neutralPercent}%`,
      sub:     `${summary.neutral.toLocaleString()} comments`,
      color:   "neutral",
      icon:    "→",
      bar:     summary.neutralPercent,
    },
  ];

  return (
    <div className={styles.grid}>
      {cards.map((card, i) => (
        <div
          key={card.label}
          className={`${styles.card} ${styles[card.color]}`}
          style={{ animationDelay: `${i * 0.07}s` }}
        >
          <div className={styles.cardTop}>
            <span className={styles.icon}>{card.icon}</span>
            <span className={styles.label}>{card.label}</span>
          </div>
          <div className={styles.value}>{card.value}</div>
          <div className={styles.sub}>{card.sub}</div>
          {card.bar !== undefined && (
            <div className={styles.barTrack}>
              <div
                className={styles.barFill}
                style={{ width: `${card.bar}%` }}
              />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

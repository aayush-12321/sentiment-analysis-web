/**
 * utils/api.js
 * Axios wrapper for all backend API calls.
 */
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 40000,
});

/*
 * Analyse a brand keyword.
 * GET /api/analyze-brand?keyword=<kw>&max_videos=<n>&max_comments=<n>
 */
export async function analyzeBrand(keyword, { maxVideos = 5, maxComments = 20 } = {}) {
  const { data } = await client.get("/analyze-brand", {
    params: { keyword, max_videos: maxVideos, max_comments: maxComments },
  });
  return data;
}

/**
 * Fetch recent search history keywords.
 * GET /api/history
 */
export async function fetchHistory() {
  const { data } = await client.get("/history");
  return data.keywords || [];
}

/**
 * Health check.
 * GET /api/health
 */
export async function fetchHealth() {
  const { data } = await client.get("/health");
  return data;
}

export default client;

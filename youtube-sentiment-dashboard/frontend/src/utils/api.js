/**
 * utils/api.js — Axios wrapper for all backend API calls.
 */
import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "/api";

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
});

/**
 * Analyse a brand across one or more sources.
 * GET /api/analyze-brand?keyword=<kw>&max_videos=<n>&max_comments=<n>&source=<s>
 */
export async function analyzeBrand(
  keyword,
  { maxVideos = 5, maxComments = 20, source = "youtube" } = {}
) {
  const { data } = await client.get("/analyze-brand", {
    params: { keyword, max_videos: maxVideos, max_comments: maxComments, source },
  });
  return data;
}

/** Fetch recent search history keywords. GET /api/history */
export async function fetchHistory() {
  const { data } = await client.get("/history");
  return data.keywords || [];
}

/** Health check. GET /api/health */
export async function fetchHealth() {
  const { data } = await client.get("/health");
  return data;
}

export default client;

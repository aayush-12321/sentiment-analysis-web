/**
 * hooks/useSentiment.js
 * Manages the full lifecycle of a sentiment analysis request.
 */
import { useState, useCallback } from "react";
import { analyzeBrand } from "../utils/api";

const INITIAL = {
  data:    null,
  loading: false,
  error:   null,
  keyword: "",
};

export function useSentiment() {
  const [state, setState] = useState(INITIAL);

  const analyse = useCallback(async (keyword, opts = {}) => {
    if (!keyword.trim()) return;

    setState((s) => ({ ...s, loading: true, error: null, keyword }));

    try {
      const data = await analyzeBrand(keyword, opts);
      setState({ data, loading: false, error: null, keyword });
    } catch (err) {
      const msg =
        err.response?.data?.error ||
        (err.code === "ECONNABORTED" ? "Request timed out. Try again." : err.message) ||
        "Something went wrong.";
      setState((s) => ({ ...s, loading: false, error: msg }));
    }
  }, []);

  const reset = useCallback(() => setState(INITIAL), []);

  return { ...state, analyse, reset };
}

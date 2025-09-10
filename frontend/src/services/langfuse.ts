import { LangfuseWeb } from "langfuse";

// Initialize LangfuseWeb client for frontend
const langfuse = new LangfuseWeb({
  publicKey: import.meta.env.VITE_LANGFUSE_PUBLIC_KEY || "pk-lf-...",
  baseUrl: import.meta.env.VITE_LANGFUSE_BASE_URL || "https://cloud.langfuse.com",
});

export default langfuse;
# RAPTOR Service I/O Spec (v0.1)

> Mục tiêu: Chuẩn hóa **định dạng request/response** cho một **RAPTOR service** độc lập. Service nhận các **chunk** đã được tách (và có thể đã có embedding), xây **cây tóm tắt phân cấp**, và cung cấp **retrieval** ở chế độ _collapsed_ hoặc _tree-traversal_. _Embedding dimension_ là **tham số linh hoạt** (ví dụ 380, 384, 512, 1024, 1536, 1560, 3072…) tùy model người dùng chọn.

---

## 1) Nguyên tắc dữ liệu chung

### 1.1. Chuẩn ký hiệu & kiểu

- **ID**: chuỗi ASCII không dấu cách (`^[A-Za-z0-9._-]{1,128}$`).
- **Timestamp**: ISO-8601, UTC (`2025-08-14T02:30:00Z`).
- **Vector**: mảng số thực (`float32`) độ dài đúng bằng `embedding_dim`.
- **Similarity**: mặc định `cosine` trên vector **đã chuẩn hóa L2** (khuyến nghị).

### 1.2. Khai báo embedding linh hoạt

Người dùng **phải** khai báo `embedding_spec` cho dataset/cây, gồm:

```json
{
  "provider": "openai|cohere|huggingface|custom",
  "model": "string",
  "embedding_dim": 384,
  "space": "cosine|ip|l2",
  "normalized": true
}
```

> Gợi ý: có thể là 384/512/768/1024/1536/1560/3072… Tùy model, bạn có thể **giảm chiều** (dimensionality) nếu backend hỗ trợ tham số `dimensions`, hoặc chọn thẳng một model xuất vector thấp/ cao chiều.

---

## 2) Các chế độ vận hành

- **Build-time** (_offline_): nhận danh sách chunk → xây **cây RAPTOR** (UMAP→clustering→LLM summarize→re-embed nhiều tầng). Kết quả gồm **nodes/edges** + thống kê.
- **Query-time** (_online_): nhận truy vấn → **embedded** → _retrieval_:
  - **collapsed**: tìm trên toàn bộ nút (lá + nút tóm tắt).
  - **tree-traversal**: top-k theo từng tầng (từ root xuống).

---

## 3) API

### 3.1. `POST /v1/trees:build` — Xây cây RAPTOR

**Body**

```json
{
  "dataset_id": "kb.my_dataset",
  "tree_id": "optional-fixed-id",
  "embedding_spec": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "embedding_dim": 1536,
    "space": "cosine",
    "normalized": true
  },
  "nodes": [
    {
      "chunk_id": "c_0001",
      "text": "string (raw chunk text)",
      "embedding": [0.0123, -0.98],
      "meta": { "source": "s3://...", "page": 3 }
    }
  ],
  "params": {
    "max_cluster": 8,
    "umap": { "n_neighbors": 15, "n_components": 8, "metric": "cosine" },
    "clusterer": { "type": "gmm", "selection": "bic", "threshold": 0.1 },
    "summary": { "max_tokens": 256, "prompt": "..." },
    "levels_cap": 0,
    "reembed_summary": true
  },
  "mode": "sync|async"
}
```

**Response (200 sync)**

```json
{
  "tree_id": "kb.my_dataset.2025-08-14",
  "dataset_id": "kb.my_dataset",
  "stats": {
    "input_chunks": 190,
    "levels": 3,
    "nodes_total": 285,
    "summary_nodes": 95,
    "embedding_dim": 1536
  },
  "root_node_id": "n_root",
  "vector_index": {
    "indexed_sets": ["leaf", "summary"],
    "space": "cosine"
  }
}
```

**Response (202 async)**

```json
{ "job_id": "job_01H...", "tree_id": "kb.my_dataset.pending" }
```

**Lỗi chung**

```json
{
  "error": {
    "code": "BAD_REQUEST|UNSUPPORTED_EMBED_DIM|DIM_MISMATCH|INTERNAL",
    "message": "..."
  }
}
```

- `UNSUPPORTED_EMBED_DIM`: khi `embedding_dim` không khớp cấu hình vector store.
- `DIM_MISMATCH`: có **ít nhất một** `embedding.length != embedding_dim`.

---

### 3.2. `GET /v1/jobs/{job_id}` — Trạng thái build

**Response**

```json
{
  "job_id": "job_01H...",
  "status": "pending|running|succeeded|failed",
  "progress": { "pct": 72.5, "stage": "summarize:l2" },
  "result": { "...": "same-as-sync-response" },
  "error": null
}
```

---

### 3.3. `POST /v1/retrieve` — Truy hồi nút

**Body**

```json
{
  "tree_id": "kb.my_dataset.2025-08-14",
  "mode": "collapsed|tree_traversal",
  "query": "How does X work?",
  "query_embedding": null,
  "top_k": 8,
  "with_paths": true,
  "reranker": {
    "provider": "bge|cohere|none",
    "model": "bge-reranker-v2-m3",
    "top_k": 5
  }
}
```

**Response**

```json
{
  "tree_id": "kb.my_dataset.2025-08-14",
  "used_mode": "collapsed",
  "hits": [
    {
      "node_id": "n_0123",
      "score": 0.83,
      "level": 2,
      "is_summary": true,
      "text": "summarized cluster content ...",
      "path": ["n_root", "n_l1_05", "n_0123"],
      "meta": { "children_count": 7 }
    }
  ]
}
```

**Lỗi**

```json
{
  "error": {
    "code": "TREE_NOT_FOUND|EMBED_BACKEND_UNAVAILABLE|INTERNAL",
    "message": "..."
  }
}
```

---

### 3.4. `POST /v1/answer` _(tùy chọn)_ — Trả lời dựa trên retrieval

**Body**

```json
{
  "retrieve": {
    "tree_id": "kb.my_dataset.2025-08-14",
    "mode": "collapsed",
    "query": "Explain Y...",
    "top_k": 6,
    "reranker": {
      "provider": "cohere",
      "model": "rerank-english-v3.0",
      "top_k": 3
    }
  },
  "generation": {
    "provider": "openai|vllm|tgi|custom",
    "model": "gpt-4o-mini",
    "max_tokens": 512,
    "stream": false,
    "cite_sources": true
  }
}
```

**Response**

```json
{
  "answer": "…",
  "citations": [{ "node_id": "n_045", "chunk_ids": ["c_011", "c_012"] }],
  "usage": { "prompt_tokens": 1832, "completion_tokens": 480 }
}
```

---

## 4) Định dạng **Node** & **Edge** (export/import)

**Node (JSONL)**

```json
{
  "node_id": "n_0123",
  "level": 2,
  "is_summary": true,
  "text": "…",
  "embedding_id": "vec_n_0123",
  "meta": { "dataset_id": "kb.my_dataset", "source": "file.pdf#p=3" }
}
```

**Edge (JSONL)**

```json
{ "parent_id": "n_l1_05", "child_id": "n_0123" }
```

**Vector (JSONL)**

```json
{ "id": "vec_n_0123", "values": [0.01, -0.23] }
```

---

## 5) Quy ước kiểm tra hợp lệ

- **Dimension guard**: mọi `embedding` phải có `len == embedding_dim`.
- **Normalization**: nếu `normalized=true`, service **phải** chuẩn hóa L2 trước khi index/tính độ tương tự.
- **Space compatibility**: `cosine` yêu cầu (hoặc tự động) chuẩn hóa; `ip`/`l2` theo engine.
- **UTF-8**: tất cả `text` là UTF-8; service từ chối nếu JSON không hợp lệ.

---

## 6) Streaming (tuỳ chọn)

- `POST /v1/answer` hỗ trợ **NDJSON** hoặc **SSE** khi `"stream": true`.
- Mỗi chunk có dạng:

```json
{ "event": "delta", "data": { "text": "…" } }
```

- Kết thúc:

```json
{ "event": "done" }
```

---

## 7) Ví dụ `embedding_spec` với các dimension khác nhau

### 7.1. 1536 chiều (OpenAI TE3-small)

```json
"embedding_spec": {
  "provider": "openai",
  "model": "text-embedding-3-small",
  "embedding_dim": 1536,
  "space": "cosine",
  "normalized": true
}
```

### 7.2. 384 chiều (BGE “small/micro”)

```json
"embedding_spec": {
  "provider": "huggingface",
  "model": "BAAI/bge-small-en-v1.5",
  "embedding_dim": 384,
  "space": "cosine",
  "normalized": true
}
```

### 7.3. 1024 chiều (Cohere v3/v4)

```json
"embedding_spec": {
  "provider": "cohere",
  "model": "embed-english-v3.0",
  "embedding_dim": 1024,
  "space": "cosine",
  "normalized": true
}
```

---

## 8) Gợi ý triển khai & tương thích

- **Two modes retrieval** (_collapsed_, _tree-traversal_) nên là cờ `mode` ở cả `/retrieve` và `/answer` để A/B dễ.
- **Không ràng buộc model**: service **không** gọi embed hộ nếu người dùng đã đẩy `embedding`; nếu thiếu, có thể bật `auto_embed` (kèm thông tin API key & provider).
- **Vector DB**: chấp nhận `space` theo engine (FAISS/Milvus/pgvector), nhưng **giữ nguyên `embedding_dim`** đã khai báo cho dataset để tránh lỗi chéo mô hình.
- **Validation sớm**: kiểm tra dimension + NaN/Inf ngay khi nhận request để trả lỗi nhanh (`DIM_MISMATCH`).
- **Versioning**: `tree_id` nên gồm `dataset_id + build_time` để hỗ trợ nhiều phiên bản cây.

---

## 9) Tham khảo (đọc thêm)

- RAPTOR paper: “Recursive Abstractive Processing for Tree‑Organized Retrieval”, 2024.
- LlamaIndex RAPTOR Pack: giới thiệu _collapsed_ và _tree_traversal_.
- RAGFlow: Enable RAPTOR (toggle trong Knowledge Base Config).
- OpenAI Embeddings: `text-embedding-3-small/large`, tham số `dimensions`.
- Cohere Embeddings: phiên bản v3/v4 và lựa chọn dimension.
- BGE “small/micro” (384‑d) model cards.
- UMAP parameters (cosine metric), GaussianMixture & BIC/AIC.

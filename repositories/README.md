# Training Exercise — Build a Qdrant + OpenAI RAG Client

---

## Phase 1 — Setup & Connection

**Step 1: Install dependencies**
```bash
pip install qdrant-client openai fastapi uvicorn
```

**Step 2: Run Qdrant locally with Docker** ✅ Done
```bash
docker run -p 6333:6333 qdrant/qdrant --env QDRANT__SERVICE__API_KEY=my_local_password123
```

**Step 3: Connect inside `__init__`**
- Create `QdrantClient(host, port)`
- Create `OpenAI(api_key)`
- Store `collection_name` as `self.collection_name`

---

## Phase 2 — Collection Endpoints

**Step 4: `create_collection` → `POST /collections`**
- Call `client.recreate_collection(collection_name, vectors_config=VectorParams(size=1536, distance=Distance.COSINE))`
- If `overwrite=False`, check first with `client.get_collections()`

**Step 5: `delete_collection` → `DELETE /collections/{name}`**
- Call `client.delete_collection(collection_name)`

---

## Phase 3 — Embeddings

**Step 6: Understand embeddings**
- A text string → list of 1536 floats
- Similar texts produce vectors close to each other in space

**Step 7: `_embed` → `POST /embed`**
- Call `openai.embeddings.create(input=text, model="text-embedding-3-small")`
- Return `response.data[0].embedding`

**Step 8: `_embed_batch` (internal — used by `save_documents`)**
- Pass a list of strings to `openai.embeddings.create(input=texts, ...)`
- Return `[item.embedding for item in response.data]`

---

## Phase 4 — Save Documents

**Step 9: `save_documents` → `POST /documents`**

Input: `[{ "text": "...", "metadata": {} }, ...]`
- Loop in batches of `batch_size` (default 100)
- Embed each batch with `_embed_batch`
- Build `PointStruct(id=uuid, vector=embedding, payload={"text":..., ...metadata})`
- Call `client.upsert(collection_name, points=[...])`

---

## Phase 5 — Search

**Step 10: `search` → `POST /search`**

Input: `{ "query": "...", "top_k": 5 }`
- Embed the query string with `_embed`
- Call `client.search(collection_name, query_vector, limit=top_k, with_payload=True)`
- Return `[{ "text": ..., "score": ..., "meta": ... }]`

**Step 11: Add filtering to search**

Input: optional `filter_by = { "source": "file.pdf" }`
- Build `Filter(must=[FieldCondition(key, match=MatchValue(value))])`
- Pass as `query_filter=` to `client.search`

---

## Phase 6 — Delete by Filter

**Step 12: `delete_by_filter` → `DELETE /documents`**

Input: `{ "source": "old.pdf" }`
- Build the same `Filter` from Step 11
- Call `client.delete(collection_name, points_selector=filter)`

---

## Phase 7 — RAG Query (Full Pipeline)

**Step 13: `query` → `POST /query`**

Input: `{ "question": "...", "top_k": 5 }`
- Call `search()` to get top-k chunks
- Build a prompt:
  ```
  System : "Answer using only the context below."
  User   : "Context:\n[chunk1]\n[chunk2]\n...\nQuestion: {question}"
  ```
- Call `openai.chat.completions.create(model="gpt-4o", messages=[...])`
- Return `{ "answer": "...", "sources": [...] }`

---

## Phase 8 — Info Endpoint

**Step 14: `info` → `GET /collections/{name}`**
- Call `client.get_collection(collection_name)`
- Return `{ "collection": str, "vectors_count": int, "dimension": int, "distance": str }`

---

## Endpoint Summary

| Step | Method | Endpoint | Method in class |
|------|--------|----------|-----------------|
| 4 | `POST` | `/collections` | `create_collection` |
| 5 | `DELETE` | `/collections/{name}` | `delete_collection` |
| 7 | `POST` | `/embed` | `_embed` |
| 9 | `POST` | `/documents` | `save_documents` |
| 10 | `POST` | `/search` | `search` |
| 11 | `POST` | `/search` + filter | `search (filter_by)` |
| 12 | `DELETE` | `/documents` | `delete_by_filter` |
| 13 | `POST` | `/query` | `query` (full RAG) |
| 14 | `GET` | `/collections/{name}` | `info` |

---

> Exercise file: [qdrant_exercise.py](qdrant_exercise.py)

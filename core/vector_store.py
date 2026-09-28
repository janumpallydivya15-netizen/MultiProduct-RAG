import chromadb
import re
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import config

class VectorStore:
    def __init__(self, persist_dir: str = None, collection_name: str = "product_knowledge_base"):
        self.persist_dir = persist_dir or str(config.CHROMADB_DIR)
        self.collection_name = collection_name
        
        self.client = chromadb.PersistentClient(path=self.persist_dir)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]) -> None:
        """Add or update document chunks in ChromaDB."""
        if not chunks or not embeddings:
            return

        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def search(self, query_embedding: List[float], top_k: int = 4, product_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Similarity search against indexed document chunks."""
        where_filter = {}
        if product_id and product_id != "all":
            where_filter = {"product_id": product_id}

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where_filter if where_filter else None
        )

        formatted_results = []
        if results and results["documents"]:
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)

            for doc, meta, dist in zip(docs, metadatas, distances):
                formatted_results.append({
                    "text": doc,
                    "metadata": meta,
                    "score": 1.0 - dist if dist is not None else 0.0
                })

        return formatted_results

    def check_existing_document(self, filename: str, product_id: str) -> Optional[Dict[str, Any]]:
        """Check if a document with the same filename and product_id is already indexed."""
        try:
            clean_fn = re.sub(r"^doc_[a-f0-9]{8}_", "", filename)
            all_data = self.collection.get(where={"product_id": product_id}, include=["metadatas"])
            
            if all_data and all_data.get("metadatas"):
                matching_chunks = []
                for m in all_data["metadatas"]:
                    if not m:
                        continue
                    m_orig = m.get("original_filename") or m.get("filename", "")
                    clean_m = re.sub(r"^doc_[a-f0-9]{8}_", "", m_orig)
                    if clean_m == clean_fn:
                        matching_chunks.append(m)

                if matching_chunks:
                    meta = matching_chunks[0]
                    doc_id = meta.get("document_id") or meta.get("doc_id")
                    return {
                        "document_id": doc_id,
                        "filename": filename,
                        "product_id": product_id,
                        "chunks": len(matching_chunks)
                    }
        except Exception as e:
            print(f"[VectorStore] Duplicate check error: {e}")
        return None

    def delete_document(self, doc_id: str) -> bool:
        """Delete all chunks belonging to a specific document ID."""
        try:
            res1 = self.collection.get(where={"document_id": doc_id}, include=[])
            res2 = self.collection.get(where={"doc_id": doc_id}, include=[])
            if not res1["ids"] and not res2["ids"]:
                return False

            # Delete matching document_id or legacy doc_id
            if res1["ids"]:
                self.collection.delete(where={"document_id": doc_id})
            if res2["ids"]:
                self.collection.delete(where={"doc_id": doc_id})
            return True
        except Exception as e:
            print(f"[VectorStore] Delete error for {doc_id}: {e}")
            return False

    def list_indexed_documents(self) -> List[Dict[str, Any]]:
        """List distinct documents indexed in ChromaDB with metadata and chunk counts."""
        try:
            all_data = self.collection.get(include=["metadatas"])
            all_metas = all_data.get("metadatas", [])
            docs_map = {}

            for meta in all_metas:
                if not meta:
                    continue
                d_id = meta.get("document_id") or meta.get("doc_id")
                if not d_id:
                    continue

                if d_id not in docs_map:
                    docs_map[d_id] = {
                        "doc_id": d_id,
                        "document_id": d_id,
                        "filename": meta.get("original_filename") or meta.get("filename", "Unknown"),
                        "product_id": meta.get("product_id", "general"),
                        "document_type": meta.get("document_type", "pdf"),
                        "chunks_count": 1,
                        "status": "Stored in ChromaDB"
                    }
                else:
                    docs_map[d_id]["chunks_count"] += 1

            return list(docs_map.values())
        except Exception as e:
            print(f"[VectorStore] Error listing documents: {e}")
            return []

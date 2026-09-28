import os
import json
from PIL import Image
import config
from typing import Dict, Any, List

class GeminiClient:
    def __init__(self, api_key: str = None, model_name: str = None):
        self.api_key = api_key or config.GEMINI_API_KEY
        self.model_name = model_name or config.GEMINI_MODEL
        self._genai = None

    def _init_genai(self):
        if self._genai is None and self.api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._genai = genai

    def analyze_product_image(self, image_path: str, ocr_text: str = "") -> Dict[str, Any]:
        """Multimodal image analysis to detect product model, category, specifications, and physical condition."""
        self._init_genai()

        prompt = f"""
You are an expert industrial product identification AI.
Analyze this uploaded product image carefully.
{f'Associated OCR Text extracted from image: "{ocr_text}"' if ocr_text else ''}

Return a valid JSON object with the following keys:
- "product_name": Brand and Estimated product name/model (string)
- "category": Product category (string)
- "detected_features": Visible hardware/features and important visible text detected (list of strings)
- "confidence": Confidence score between 0.0 and 1.0 considering limitations (float)
- "summary": A concise technical summary of observations seen in the image (string)

Return ONLY raw JSON, with no markdown codeblocks or explanation.
"""

        if not self._genai or not self.api_key or self.api_key == "your_gemini_api_key_here":
            raise ValueError("Gemini API key is not configured.")

        try:
            img = Image.open(image_path)
            model = self._genai.GenerativeModel(self.model_name)
            response = model.generate_content([prompt, img])
            text = response.text.strip()

            # Clean JSON formatting wrappers if present
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            if text.startswith("```"):
                text = text[3:]

            return json.loads(text.strip())
        except Exception as e:
            print(f"[GeminiClient] Image analysis error: {e}")
            raise RuntimeError(f"Gemini Vision error: {str(e)}")


    def generate_rag_response(self, question: str, contexts: List[Dict[str, Any]], product_id: str = "general") -> Dict[str, Any]:
        """Generate grounded RAG response using only retrieved context, with strict anti-hallucination rules."""
        self._init_genai()

        # Build deduplicated sources list from metadata
        seen_sources = set()
        sources = []
        for item in contexts:
            meta = item.get("metadata", {})
            fname = meta.get("filename") or meta.get("original_filename", "Unknown")
            page = meta.get("page_number", 1)
            pid = meta.get("product_id", product_id)
            chunk_idx = meta.get("chunk_index", 0)
            key = (fname, page)
            if key not in seen_sources:
                seen_sources.add(key)
                sources.append({
                    "filename": fname,
                    "page_number": page,
                    "product_id": pid,
                    "chunk_index": chunk_idx
                })

        # Build numbered context block for the LLM prompt
        context_str = ""
        for idx, item in enumerate(contexts):
            meta = item.get("metadata", {})
            fname = meta.get("filename", "Manual")
            page = meta.get("page_number", 1)
            context_str += f"\n--- [Source {idx+1}: {fname}, Page {page}] ---\n{item['text']}\n"

        no_context = not contexts or not context_str.strip()

        prompt = f"""You are an expert Product Support AI Assistant for {product_id}.

USER QUESTION: "{question}"

RETRIEVED KNOWLEDGE BASE CONTEXT:
{context_str if not no_context else "(No relevant documentation was found in the knowledge base for this query.)"}

STRICT RULES — YOU MUST FOLLOW THESE:
1. Answer ONLY using information explicitly present in the RETRIEVED KNOWLEDGE BASE CONTEXT above.
2. Do NOT invent, assume, or guess any facts, specifications, error codes, or troubleshooting steps that are not in the context.
3. If the context does not contain the answer, respond EXACTLY with:
   "The available knowledge base does not contain information about [topic]. Please refer to the full product documentation or contact support."
4. Do NOT add generic advice that is not grounded in the provided context.
5. For troubleshooting/setup questions, use numbered steps ONLY if steps appear in the retrieved context.
6. Cite your sources inline using: [Source: <filename>, Page <page_number>]
7. Be concise and direct. Use markdown headers where helpful.

Respond now:"""

        if not self._genai or not self.api_key or self.api_key == "your_gemini_api_key_here":
            return {
                "answer": "[Demo Mode — Add GEMINI_API_KEY to .env to enable live generation]\n\nBased on the retrieved context, here is what the knowledge base contains for your query.",
                "sources": sources,
                "retrieved_chunks": len(contexts)
            }

        try:
            from google.api_core.exceptions import ResourceExhausted
            import time
            import re
            
            # Use the specific RAG model
            rag_model_name = config.GEMINI_RAG_MODEL
            model = self._genai.GenerativeModel(rag_model_name)
            
            def attempt_generation():
                response = model.generate_content(prompt)
                return response.text.strip()
                
            try:
                answer_text = attempt_generation()
            except ResourceExhausted as e:
                print(f"[GeminiClient] Quota exceeded on first attempt: {e}")
                
                # Attempt to parse retry delay from the error message
                err_str = str(e)
                delay = 5  # default
                match = re.search(r'retry_delay\s*{\s*seconds:\s*(\d+)\s*}', err_str)
                if match:
                    delay = int(match.group(1)) + 1
                    
                # We only want to retry if the delay is short, else just return the error immediately
                if delay <= 10:
                    print(f"[GeminiClient] Waiting {delay}s before retrying...")
                    time.sleep(delay)
                    try:
                        answer_text = attempt_generation()
                    except ResourceExhausted as e2:
                        print(f"[GeminiClient] Quota exceeded on retry: {e2}")
                        raise RuntimeError("AI generation is temporarily rate-limited. Please try again shortly.")
                else:
                    raise RuntimeError("AI generation is temporarily rate-limited. Please try again shortly.")

            if "does not contain information about" in answer_text or "does not provide a verified solution" in answer_text:
                sources = []

            return {
                "answer": answer_text,
                "sources": sources,
                "retrieved_chunks": len(contexts)
            }
        except Exception as e:
            # Check if this is already our safe runtime error message
            if "temporarily rate-limited" in str(e):
                raise RuntimeError(str(e))
                
            print(f"[GeminiClient] RAG response error: {e}")
            raise RuntimeError(f"Gemini generation error: {str(e)}")
    def generate_troubleshooting_response(self, product_id: str, error_code: str, symptom: str, description: str, contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a structured JSON troubleshooting diagnosis using retrieved context."""
        self._init_genai()

        # Build deduplicated sources list from metadata
        seen_sources = set()
        sources = []
        for item in contexts:
            meta = item.get("metadata", {})
            fname = meta.get("filename") or meta.get("original_filename", "Unknown")
            page = meta.get("page_number", 1)
            key = (fname, page)
            if key not in seen_sources:
                seen_sources.add(key)
                sources.append({
                    "filename": fname,
                    "page": page
                })

        context_str = ""
        for idx, item in enumerate(contexts):
            meta = item.get("metadata", {})
            fname = meta.get("filename", "Manual")
            page = meta.get("page_number", 1)
            context_str += f"\n--- [Source {idx+1}: {fname}, Page {page}] ---\n{item['text']}\n"

        no_context = not contexts or not context_str.strip()

        problem_desc = []
        if error_code: problem_desc.append(f"Error Code: {error_code}")
        if symptom: problem_desc.append(f"Symptom: {symptom}")
        if description: problem_desc.append(f"Description: {description}")
        problem_str = ", ".join(problem_desc)

        prompt = f"""You are an expert troubleshooting AI for {product_id}.
USER ISSUE: {problem_str}

RETRIEVED KNOWLEDGE BASE CONTEXT:
{context_str if not no_context else "(No relevant documentation found.)"}

STRICT RULES:
1. Output ONLY valid JSON, with no markdown formatting blocks, no ```json, and no extra text.
2. The JSON must have the following structure:
{{
  "diagnosis": "A concise explanation of the problem based ONLY on context. If not found, say exactly 'The available documentation does not contain information about this issue.'",
  "severity": "Extract from context if present, else 'Unknown'",
  "resolution_steps": ["step 1", "step 2"],
  "prevention_or_notes": ["note 1", "note 2"]
}}
3. Do NOT invent steps, severities, or notes. If resolution steps are not in the context, leave the array empty.
4. ONLY use information explicitly stated in the retrieved context.
"""

        if not self._genai or not self.api_key or self.api_key == "your_gemini_api_key_here":
            return {
                "diagnosis": "Demo Mode: API key not configured.",
                "severity": "Unknown",
                "resolution_steps": [],
                "prevention_or_notes": [],
                "sources": sources,
                "chunks_retrieved": len(contexts)
            }

        try:
            from google.api_core.exceptions import ResourceExhausted
            import time
            import re
            
            rag_model_name = config.GEMINI_RAG_MODEL
            model = self._genai.GenerativeModel(rag_model_name)
            
            def attempt_generation():
                response = model.generate_content(prompt)
                return response.text.strip()
                
            try:
                answer_text = attempt_generation()
            except ResourceExhausted as e:
                print(f"[GeminiClient] Quota exceeded on first attempt: {e}")
                err_str = str(e)
                delay = 5
                match = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)\s*\}", err_str)
                if match:
                    delay = int(match.group(1)) + 1
                    
                if delay <= 10:
                    time.sleep(delay)
                    try:
                        answer_text = attempt_generation()
                    except ResourceExhausted:
                        raise RuntimeError("AI generation is temporarily rate-limited. Please try again shortly.")
                else:
                    raise RuntimeError("AI generation is temporarily rate-limited. Please try again shortly.")

            # Clean JSON formatting wrappers if present
            if answer_text.startswith("```json"): answer_text = answer_text[7:]
            if answer_text.endswith("```"): answer_text = answer_text[:-3]
            if answer_text.startswith("```"): answer_text = answer_text[3:]
            
            try:
                parsed = json.loads(answer_text.strip())
            except json.JSONDecodeError:
                print(f"[GeminiClient] Failed to parse JSON: {answer_text}")
                parsed = {
                    "diagnosis": answer_text,
                    "severity": "Unknown",
                    "resolution_steps": [],
                    "prevention_or_notes": []
                }

            if "does not contain information about this issue" in parsed.get("diagnosis", ""):
                parsed["sources"] = []
            else:
                parsed["sources"] = sources
            
            parsed["chunks_retrieved"] = len(contexts)
            return parsed

        except Exception as e:
            if "temporarily rate-limited" in str(e):
                raise RuntimeError(str(e))
            print(f"[GeminiClient] Troubleshooting response error: {e}")
            raise RuntimeError(f"Gemini generation error: {str(e)}")

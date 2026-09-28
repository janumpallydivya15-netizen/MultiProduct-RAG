import os
from PIL import Image

class OCREngine:
    def __init__(self, languages=None):
        if languages is None:
            languages = ['en']
        self.languages = languages
        self._reader = None

    @property
    def reader(self):
        """Lazy loader for EasyOCR reader to optimize initial application startup time."""
        if self._reader is None:
            try:
                import easyocr
                # Disable GPU if CUDA is not configured to avoid warnings
                self._reader = easyocr.Reader(self.languages, gpu=False)
            except Exception as e:
                print(f"[OCREngine] Warning: EasyOCR reader initialization deferred/failed: {e}")
                return None
        return self._reader

    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using EasyOCR with PIL fallback fallback check."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        reader = self.reader
        if reader is None:
            return ""

        try:
            results = reader.readtext(image_path, detail=0)
            return "\n".join(results)
        except Exception as e:
            print(f"[OCREngine] Error processing image {image_path}: {e}")
            return ""

    def extract_text_from_pil(self, pil_image: Image.Image) -> str:
        """Extract text directly from PIL Image instance."""
        import numpy as np
        reader = self.reader
        if reader is None:
            return ""

        try:
            img_np = np.array(pil_image)
            results = reader.readtext(img_np, detail=0)
            return "\n".join(results)
        except Exception as e:
            print(f"[OCREngine] Error processing PIL image: {e}")
            return ""

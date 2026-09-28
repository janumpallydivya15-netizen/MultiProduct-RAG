# Demo Guide

## 4-Minute Presentation Sequence

1. **Open Dashboard:** Start the application on http://localhost:5000 to show system health.
2. **Show Product Analysis:** Upload TN3000_image.jpg (if available) and demonstrate Gemini Vision analyzing hardware context.
3. **Show Knowledge Base:** Upload TechNova_TN3000_Product_Manual.pdf. Show how it chunks and persists in ChromaDB.
4. **Open AI Assistant:**
   - Select TN-3000 context.
   - Ask: "What does error E-04 mean?"
   - *Highlight how the answer is grounded in the indexed manual and explicitly points to Page 3.*
5. **Demonstrate Hallucination Safeguards:**
   - Ask: "How do I set up the TN-3000?"
   - *Show grounded setup instructions mapped to Page 2.*
6. **Open Troubleshooting:**
   - Select TN-3000 context.
   - Enter E-04 in Error Code.
   - *Demonstrate the structured JSON diagnostic response rendering natively in the UI with severity tags and resolution steps.*

The primary talking point of the demo is: *"Answers are fundamentally grounded in the indexed product documentation and include strict explicit source page citations."*

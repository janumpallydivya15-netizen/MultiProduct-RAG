document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    fetchSystemHealth();
    initVisionModule();
    initKBModule();
    initChatModule();
    initTroubleshootingModule();
});

// Single Page Navigation & Header Title Sync
function navigateTo(pageId) {
    const navItem = document.querySelector(`.nav-item[data-page="${pageId}"]`);
    if (navItem) navItem.click();
}

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.page-section');
    const headerTitle = document.getElementById('header-page-title');
    const headerSubtitle = document.getElementById('header-page-subtitle');

    const pageMeta = {
        'landing': { title: 'Enterprise Product AI Knowledge Platform', subtitle: 'Multimodal RAG, Vision Analytics & Document Intelligence' },
        'dashboard': { title: 'System Dashboard', subtitle: 'Real-time Vector DB indices, OCR engine & LLM metrics' },
        'analysis': { title: 'Product Image Analysis', subtitle: 'Gemini Vision & EasyOCR Product Identification' },
        'kb': { title: 'Document Knowledge Base', subtitle: 'ChromaDB Document Chunking & Dense Embeddings' },
        'assistant': { title: 'AI Product Knowledge Assistant', subtitle: 'Grounded RAG Q&A with explicit document page citations' },
        'troubleshoot': { title: 'Troubleshooting & Diagnostics', subtitle: 'Step-by-step remedy procedures and error code lookup' },
        'settings': { title: 'System Settings', subtitle: 'Model choices, vector parameters, and system paths' }
    };

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetPage = item.getAttribute('data-page');

            navItems.forEach(i => i.classList.remove('active'));
            sections.forEach(s => s.classList.remove('active'));

            item.classList.add('active');
            const targetSection = document.getElementById(`page-${targetPage}`);
            if (targetSection) {
                targetSection.classList.add('active');
            }

            if (pageMeta[targetPage]) {
                if (headerTitle) headerTitle.textContent = pageMeta[targetPage].title;
                if (headerSubtitle) headerSubtitle.textContent = pageMeta[targetPage].subtitle;
            }
        });
    });
}

// Fetch System Health Status & Stats
async function fetchSystemHealth() {
    try {
        const res = await fetch('/api/v1/system/health');
        const data = await res.json();

        const docCountEl = document.getElementById('stat-docs-count');
        const statusBadgeEl = document.getElementById('system-status-badge');
        const dashGeminiEl = document.getElementById('dash-gemini-status');
        const settingsLlmEl = document.getElementById('settings-llm-model');
        const settingsEmbedEl = document.getElementById('settings-embedding-model');

        if (docCountEl) docCountEl.textContent = data.indexed_documents_count || 0;
        if (statusBadgeEl) {
            statusBadgeEl.innerHTML = `<span class="status-dot"></span> System ${data.status.toUpperCase()}`;
        }
        if (dashGeminiEl) {
            dashGeminiEl.innerHTML = data.gemini_api_configured ?
                `<span style="color: var(--status-success);">● Connected (${data.gemini_model || 'Gemini Model'})</span>` :
                `<span style="color: var(--status-warning);">● Demo Mode (${data.gemini_model || 'Gemini Model'})</span>`;
        }
        if (settingsLlmEl && data.gemini_model) {
            settingsLlmEl.textContent = `Google ${data.gemini_model}`;
        }
        if (settingsEmbedEl && data.embedding_model) {
            settingsEmbedEl.textContent = `Sentence Transformers (${data.embedding_model})`;
        }
    } catch (e) {
        console.error('Failed to load system health:', e);
    }
}

// Product Vision Analysis Module (2-Column Interface)
function initVisionModule() {
    const dropzone = document.getElementById('vision-dropzone');
    const fileInput = document.getElementById('vision-file-input');
    const previewContainer = document.getElementById('vision-preview-container');
    const previewImg = document.getElementById('vision-image-preview');
    const removeBtn = document.getElementById('vision-remove-btn');

    const emptyState = document.getElementById('vision-empty-state');
    const loadingState = document.getElementById('vision-loading-state');
    const resultContent = document.getElementById('vision-result-content');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async (e) => {
        if (!e.target.files.length) return;
        const file = e.target.files[0];

        // Display Image Preview
        const reader = new FileReader();
        reader.onload = (evt) => {
            previewImg.src = evt.target.result;
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);

        // UI States: Hide empty, show loading
        emptyState.style.display = 'none';
        resultContent.style.display = 'none';
        loadingState.style.display = 'block';

        const formData = new FormData();
        formData.append('image', file);

        try {
            const res = await fetch('/api/v1/vision/analyze', {
                method: 'POST',
                body: formData
            });
            const payload = await res.json();
            loadingState.style.display = 'none';

            if (res.ok && payload.data) {
                const data = payload.data;
                resultContent.style.display = 'block';

                document.getElementById('res-product-name').textContent = data.product_name || 'Unknown Model';
                document.getElementById('res-category').textContent = data.category || 'N/A';
                document.getElementById('res-confidence').textContent = `${Math.round((data.confidence || 0) * 100)}%`;
                document.getElementById('res-summary').textContent = data.summary || '';
                document.getElementById('res-ocr-status').textContent = data.ocr_error
                    ? `OCR unavailable: ${data.ocr_error}`
                    : (data.ocr_text_extracted ? 'Text detected' : 'No readable text detected');
                document.getElementById('res-ocr-text').textContent = data.ocr_text_extracted || '';

                const featuresEl = document.getElementById('res-features');
                featuresEl.innerHTML = (data.detected_features || []).map(f =>
                    `<span style="display:inline-block; background-color: var(--primary-light); color: var(--primary); padding: 4px 10px; border-radius: 4px; font-size: 0.8rem; margin: 2px; font-weight:600;">${f}</span>`
                ).join('');

                // Increment dashboard analyzed count metric
                const dashCount = document.getElementById('dash-products-analyzed');
                if (dashCount) dashCount.textContent = parseInt(dashCount.textContent || 0) + 1;
            } else {
                emptyState.style.display = 'block';
                const message = payload.message || payload.error || 'Unknown error';
                const ocrWarning = payload.ocr_warning ? ` OCR warning: ${payload.ocr_warning}` : '';
                const errorMessage = document.createElement('p');
                errorMessage.style.color = 'var(--status-danger)';
                errorMessage.textContent = `Analysis failed: ${message}${ocrWarning}`;
                emptyState.replaceChildren(errorMessage);
            }
        } catch (err) {
            loadingState.style.display = 'none';
            emptyState.style.display = 'block';
            emptyState.innerHTML = `<p style="color: var(--status-danger);">Error: ${err.message}</p>`;
        }
    });

    if (removeBtn) {
        removeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.value = '';
            previewContainer.style.display = 'none';
            resultContent.style.display = 'none';
            emptyState.style.display = 'block';
        });
    }
}

// Knowledge Base Module with Processing Stepper & Statistics Feedback
function initKBModule() {
    const docInput = document.getElementById('kb-doc-input');
    const uploadBtn = document.getElementById('kb-upload-btn');

    if (uploadBtn && docInput) {
        uploadBtn.addEventListener('click', async () => {
            if (!docInput.files.length) {
                alert('Please select a PDF, TXT, or MD document file.');
                return;
            }

            const productId = document.getElementById('kb-product-id').value.trim() || 'general';
            const file = docInput.files[0];

            const formData = new FormData();
            formData.append('document', file);
            formData.append('product_id', productId);

            // Stepper Visual Progress Sequence
            setStepperStage(1); // Uploaded
            uploadBtn.disabled = true;
            uploadBtn.textContent = 'Processing & Indexing...';

            const s2 = setTimeout(() => setStepperStage(2), 300); // Extracted
            const s3 = setTimeout(() => setStepperStage(3), 800); // Chunked
            const s4 = setTimeout(() => setStepperStage(4), 1400); // Embedded

            try {
                const res = await fetch('/api/v1/documents/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();

                clearTimeout(s2);
                clearTimeout(s3);
                clearTimeout(s4);

                if (res.status === 201 && data.status === "success") {
                    setStepperStage(5); // Stored in ChromaDB
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload Document';

                    const d = data.data;
                    alert(`✅ Document Ingested Successfully!\n\n• Document: ${d.filename}\n• Product ID: ${d.product_id}\n• Pages Processed: ${d.pages}\n• Chunks Created: ${d.chunks}\n• ChromaDB Status: Indexed & Persisted`);

                    docInput.value = '';
                    loadDocumentsList();
                    fetchSystemHealth();
                } else if (res.status === 200 && data.status === "duplicate") {
                    setStepperStage(5);
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload Document';

                    const d = data.data;
                    alert(`ℹ️ Duplicate Document Detected\n\n${data.message}\n• Product ID: ${d.product_id}\n• Existing Chunks: ${d.chunks}`);

                    docInput.value = '';
                    loadDocumentsList();
                } else {
                    uploadBtn.disabled = false;
                    uploadBtn.textContent = 'Upload Document';
                    alert(`❌ Ingestion failed: ${data.error || 'Unknown error'}`);
                    resetStepper();
                }
            } catch (err) {
                clearTimeout(s2);
                clearTimeout(s3);
                clearTimeout(s4);
                uploadBtn.disabled = false;
                uploadBtn.textContent = 'Upload Document';
                alert(`❌ Ingestion Error: ${err.message}`);
                resetStepper();
            }
        });
    }

    loadDocumentsList();
}

function setStepperStage(stageNumber) {
    const stages = ['step-upload', 'step-extract', 'step-chunk', 'step-embed', 'step-chroma'];
    stages.forEach((id, idx) => {
        const el = document.getElementById(id);
        if (!el) return;
        if (idx < stageNumber - 1) {
            el.className = 'step-item completed';
        } else if (idx === stageNumber - 1) {
            el.className = 'step-item active';
        } else {
            el.className = 'step-item';
        }
    });
}

function resetStepper() {
    ['step-upload', 'step-extract', 'step-chunk', 'step-embed', 'step-chroma'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.className = 'step-item';
    });
}

async function loadDocumentsList() {
    const tableBody = document.getElementById('documents-table-body');
    const selectDropdown = document.getElementById('chat-product-select');
    if (!tableBody) return;

    try {
        const res = await fetch('/api/v1/documents');
        const data = await res.json();

        if (res.ok && data.documents) {
            if (data.documents.length === 0) {
                tableBody.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted); padding: 24px;">No documents indexed yet. Upload a PDF or manual above.</td></tr>`;
                return;
            }

            tableBody.innerHTML = data.documents.map(doc => `
                <tr>
                    <td><strong>${doc.filename}</strong><br><small style="color:var(--text-muted);">${doc.doc_id}</small></td>
                    <td><span style="text-transform:uppercase; font-size:0.75rem; font-weight:700; color:var(--text-muted);">${doc.document_type || 'PDF'}</span></td>
                    <td><span style="background: var(--primary-light); color: var(--primary); padding: 2px 8px; border-radius: 4px; font-weight:600; font-size:0.8rem;">${doc.product_id}</span></td>
                    <td><strong>${doc.chunks_count || 1}</strong> chunks</td>
                    <td><span style="color: var(--status-success); font-weight:600; font-size: 0.85rem;">● Stored in ChromaDB</span></td>
                    <td>
                        <button class="btn btn-danger" style="padding: 4px 10px; font-size: 0.8rem;" onclick="deleteDoc('${doc.doc_id}')">Delete</button>
                    </td>
                </tr>
            `).join('');

            // Update chat and troubleshoot product filter dropdown options
            if (selectDropdown) {
                const uniqueProducts = Array.from(new Set(data.documents.map(d => d.product_id)));
                let optionsHtml = `<option value="all">All Indexed Products</option><option value="general">General Knowledge</option>`;
                uniqueProducts.forEach(p => {
                    if (p !== 'general') {
                        optionsHtml += `<option value="${p}">${p}</option>`;
                    }
                });
                selectDropdown.innerHTML = optionsHtml;
                
                const troubleshootSelect = document.getElementById('troubleshoot-product-select');
                if (troubleshootSelect) troubleshootSelect.innerHTML = optionsHtml;
            }
        }
    } catch (err) {
        console.error('Failed to load documents list:', err);
    }
}

async function deleteDoc(docId) {
    if (!confirm(`Are you sure you want to delete document ${docId} from ChromaDB?`)) return;

    try {
        const res = await fetch(`/api/v1/documents/${docId}`, { method: 'DELETE' });
        
        let data = {};
        try {
            data = await res.json();
        } catch (e) {
            console.warn("Failed to parse JSON response");
        }

        if (res.ok && data.success) {
            alert(data.message || `Document ${docId} deleted successfully.`);
            loadDocumentsList();
            fetchSystemHealth();
        } else {
            alert(`❌ Deletion failed: ${data.message || 'Unknown error occurred.'}`);
        }
    } catch (err) {
        alert(`❌ Error deleting document: ${err.message}`);
    }
}

// AI Product Assistant Module with Suggested Chips & Source Cards
function initChatModule() {
    const sendBtn = document.getElementById('chat-send-btn');
    const inputEl = document.getElementById('chat-input');
    const chatMessages = document.getElementById('chat-messages');

    if (!sendBtn || !inputEl) return;

    const handleSend = async () => {
        const question = inputEl.value.trim();
        if (!question) return;

        const productId = document.getElementById('chat-product-select') ? document.getElementById('chat-product-select').value : 'all';

        const emptyState = document.getElementById('chat-empty-state');
        if (emptyState) emptyState.remove();

        appendChatBubble(chatMessages, question, 'user');
        inputEl.value = '';

        const thinkingId = appendChatBubble(chatMessages, '⚡ Searching ChromaDB vector index & querying Gemini LLM...', 'assistant');

        try {
            const res = await fetch('/api/v1/rag/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question, product_id: productId })
            });

            const payload = await res.json();
            const thinkingBubble = document.getElementById(thinkingId);

            if (res.ok && payload.success) {
                let html = parseMarkdown(payload.answer || '');

                // Source citations block — uses new 'sources' key with 'page_number'
                const sources = payload.sources || [];
                if (sources.length > 0) {
                    html += `<div style="margin-top: 16px; border-top: 1px solid var(--card-border); padding-top: 12px;">`;
                    html += `<strong style="font-size: 0.85rem; color: var(--navy-dark);">📚 SOURCE DOCUMENT CITATIONS</strong>`;
                    sources.forEach(s => {
                        html += `
                            <div class="source-card">
                                <div class="source-card-header">
                                    <span>📄 ${s.filename}</span>
                                    <span>Page ${s.page_number}</span>
                                </div>
                                <div style="color: var(--text-secondary); font-size: 0.8rem; line-height: 1.4;">
                                    Product: <strong>${s.product_id || 'N/A'}</strong>
                                </div>
                            </div>
                        `;
                    });
                    const chunks = payload.retrieved_chunks || 0;
                    html += `<div style="font-size:0.75rem; color:var(--text-muted); margin-top:8px;">🔍 ${chunks} chunk${chunks !== 1 ? 's' : ''} retrieved from ChromaDB</div>`;
                    html += `</div>`;
                }

                thinkingBubble.innerHTML = html;

                // Update dashboard query count stat
                const queryCount = document.getElementById('dash-queries-count');
                if (queryCount) queryCount.textContent = parseInt(queryCount.textContent || 0) + 1;
            } else {
                const errMsg = payload.message || payload.error || 'Failed to retrieve response';
                thinkingBubble.innerHTML = `<span style="color:var(--status-danger);">❌ ${errMsg}</span>`;
            }
        } catch (err) {
            console.error('Chat error:', err);
            const thinkingBubble = document.getElementById(thinkingId);
            if (thinkingBubble) thinkingBubble.innerHTML = `<span style="color:var(--status-danger);">❌ Network error: ${err.message}</span>`;
        }
    };

    sendBtn.addEventListener('click', handleSend);
    inputEl.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSend();
    });
}

function askSuggested(text) {
    const inputEl = document.getElementById('chat-input');
    if (!inputEl) return;
    inputEl.value = text;
    // Navigate to the chat section if nav exists
    const chatNavBtn = document.querySelector('[data-section="chat"]');
    if (chatNavBtn) chatNavBtn.click();
    // Trigger send after a short tick to let navigation settle
    setTimeout(() => {
        const sendBtn = document.getElementById('chat-send-btn');
        if (sendBtn) sendBtn.click();
    }, 50);
}

function appendChatBubble(container, text, sender) {
    const id = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 4)}`;
    const bubble = document.createElement('div');
    bubble.id = id;
    bubble.className = `chat-bubble ${sender}`;
    bubble.textContent = text;
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
    return id;
}

function parseMarkdown(text) {
    if (!text) return '';
    return text
        .replace(/^### (.*$)/gm, '<h4 style="margin:10px 0 4px;color:var(--navy-dark);">$1</h4>')
        .replace(/^## (.*$)/gm, '<h3 style="margin:12px 0 6px;color:var(--navy-dark);">$1</h3>')
        .replace(/^# (.*$)/gm, '<h2 style="margin:12px 0 6px;color:var(--navy-dark);">$1</h2>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`([^`]+)`/g, '<code style="background:var(--primary-light);padding:1px 4px;border-radius:3px;font-size:0.85em;">$1</code>')
        .replace(/^\d+\.\s+(.+)$/gm, '<div style="margin:3px 0;padding-left:8px;">• $1</div>')
        .replace(/\n/g, '<br>');
}

// Visual Step-by-Step Troubleshooting Module (6-Section Layout)
function initTroubleshootingModule() {
    const searchBtn = document.getElementById('troubleshoot-search-btn');

    if (searchBtn) {
        searchBtn.addEventListener('click', () => {
            const errCode = document.getElementById('troubleshoot-error-input')?.value.trim() || '';
            const symptom = document.getElementById('troubleshoot-symptom-input')?.value.trim() || '';
            const desc = document.getElementById('troubleshoot-desc-input')?.value.trim() || '';
            
            if (!errCode && !symptom && !desc) {
                alert('Please enter an error code, symptom, or description to diagnose.');
                return;
            }
            runDiagnostic(errCode, symptom, desc);
        });
    }
}

async function runDiagnostic(errCode, symptom = '', desc = '') {
    const diagArea = document.getElementById('troubleshoot-diagnosis-area');
    const stepsArea = document.getElementById('troubleshoot-steps-area');
    const sourcesArea = document.getElementById('troubleshoot-sources-area');
    const productSelect = document.getElementById('troubleshoot-product-select');

    if (!diagArea || !stepsArea || !sourcesArea) return;

    // Helper for shortcuts
    if (arguments.length === 1 && typeof errCode === 'string') {
        symptom = errCode;
        errCode = '';
    }

    const productId = productSelect ? productSelect.value : 'all';

    diagArea.innerHTML = `<p style="color: var(--primary); font-weight:600;">⚡ Analyzing product documentation...</p>`;
    stepsArea.innerHTML = `<p style="color: var(--text-muted); font-size:0.85rem;">Retrieving troubleshooting information...</p>`;
    sourcesArea.innerHTML = `<p style="color: var(--text-muted); font-size:0.85rem;">Generating grounded diagnosis...</p>`;

    try {
        const res = await fetch('/api/v1/troubleshooting/diagnose', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                product_id: productId,
                error_code: errCode,
                symptom: symptom,
                description: desc
            })
        });

        const payload = await res.json();
        
        if (res.ok && payload.success) {
            // SECTION 4: Diagnosis Result
            diagArea.innerHTML = `
                <div style="background-color: var(--primary-light); border: 1px solid var(--primary-border); padding: 14px; border-radius: var(--radius-md);">
                    <strong style="color: var(--navy-dark); font-size: 0.95rem; display: block; margin-bottom: 4px;">Problem: ${payload.problem || 'Unknown'}</strong>
                    <div style="font-size:0.9rem; color: var(--text-secondary); line-height:1.5; margin-bottom: 8px;">
                        ${parseMarkdown(payload.diagnosis)}
                    </div>
                    ${payload.severity && payload.severity.toLowerCase() !== 'unknown' ? 
                        `<span style="display:inline-block; background:var(--status-danger); color:white; padding:2px 8px; border-radius:4px; font-size:0.75rem; font-weight:bold;">Severity: ${payload.severity}</span>` : ''}
                </div>
            `;

            // SECTION 5: Step-by-Step Troubleshooting
            let stepsHtml = ``;
            if (payload.resolution_steps && payload.resolution_steps.length > 0) {
                stepsHtml += `<div class="timeline-steps">`;
                payload.resolution_steps.forEach((step, idx) => {
                    stepsHtml += `
                        <div class="timeline-step">
                            <div class="step-number">${idx + 1}</div>
                            <div>
                                <strong style="color: var(--navy-dark); font-size: 0.9rem;">Step ${idx + 1}</strong>
                                <p style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 2px;">${parseMarkdown(step)}</p>
                            </div>
                        </div>
                    `;
                });
                stepsHtml += `</div>`;
            } else {
                stepsHtml += `<p style="color: var(--text-muted); font-size:0.85rem;">No specific resolution steps found in documentation.</p>`;
            }
            
            if (payload.prevention_or_notes && payload.prevention_or_notes.length > 0) {
                stepsHtml += `<div style="margin-top: 16px; padding: 12px; background: #f8fafc; border-left: 3px solid var(--primary); font-size: 0.85rem; color: var(--text-secondary);">
                    <strong>Notes / Prevention:</strong>
                    <ul style="margin-top: 4px; padding-left: 20px;">
                        ${payload.prevention_or_notes.map(note => `<li>${parseMarkdown(note)}</li>`).join('')}
                    </ul>
                </div>`;
            }
            
            stepsArea.innerHTML = stepsHtml;

            // SECTION 6: Sources / Citations Area
            if (payload.sources && payload.sources.length > 0) {
                let sourcesHtml = ``;
                payload.sources.forEach(c => {
                    sourcesHtml += `
                        <div class="source-card">
                            <div class="source-card-header">
                                <span>📄 ${c.filename}</span>
                                <span>Page ${c.page}</span>
                            </div>
                        </div>
                    `;
                });
                sourcesArea.innerHTML = sourcesHtml;
            } else {
                sourcesArea.innerHTML = `<div style="color: var(--text-muted); font-size:0.85rem; padding: 12px; text-align: center;">No specific document citations retrieved.</div>`;
            }

            // Increment troubleshooting metric on dashboard
            const countEl = document.getElementById('dash-troubleshoot-count');
            if (countEl) countEl.textContent = parseInt(countEl.textContent || 0) + 1;

        } else {
            const errMsg = payload.error || payload.message || 'Diagnostic query failed.';
            diagArea.innerHTML = `<p style="color: var(--status-danger);">Error: ${errMsg}</p>`;
            stepsArea.innerHTML = `<p style="color: var(--text-muted); font-size:0.85rem;">No steps available.</p>`;
            sourcesArea.innerHTML = `<p style="color: var(--text-muted); font-size:0.85rem;">No citations available.</p>`;
        }
    } catch (err) {
        diagArea.innerHTML = `<p style="color: var(--status-danger);">Error: ${err.message}</p>`;
        stepsArea.innerHTML = `<p style="color: var(--text-muted); font-size:0.85rem;">Failed to fetch diagnostic data.</p>`;
        sourcesArea.innerHTML = ``;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    let currentAgent = 'docs-agent';

    // TAB NAVIGATION
    const navBtns = document.querySelectorAll('.nav-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            navBtns.forEach(b => b.classList.remove('active'));
            tabPanels.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            document.getElementById(`tab-${tabId}`).classList.add('active');

            if (tabId === 'overview') loadOverviewData();
            if (tabId === 'knowledge') loadKnowledgeItems();
            if (tabId === 'integrations') loadIntegrationsStatus();
            if (tabId === 'audit') loadAuditLogs();
        });
    });

    // AGENT CHIP SELECTOR
    const agentChips = document.querySelectorAll('.agent-chip');
    agentChips.forEach(chip => {
        chip.addEventListener('click', () => {
            agentChips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            currentAgent = chip.getAttribute('data-agent');
            showToast(`Agente activo: ${currentAgent}`);
        });
    });

    // SUGGESTED PROMPTS
    document.querySelectorAll('.prompt-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = document.getElementById('chat-input');
            input.value = btn.innerText;
            executeAgentQuery();
        });
    });

    // CHAT INPUT EXECUTION
    document.getElementById('send-btn').addEventListener('click', executeAgentQuery);
    document.getElementById('chat-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') executeAgentQuery();
    });

    async function executeAgentQuery() {
        const input = document.getElementById('chat-input');
        const query = input.value.trim ? input.value.trim() : input.value;
        if (!query) return;

        appendUserMessage(query);
        input.value = '';

        try {
            const res = await fetch(`/api/v1/agents/${currentAgent}/run`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Agent-ID': currentAgent
                },
                body: JSON.stringify({ prompt: query })
            });

            const data = await res.json();
            appendAgentResponse(data);
        } catch (err) {
            appendAgentResponse({
                answer: `Error al comunicarse con el servidor: ${err.message}`,
                sources: []
            });
        }
    }

    function appendUserMessage(text) {
        const history = document.getElementById('chat-history');
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-msg user';
        msgDiv.innerHTML = `
            <div class="msg-avatar">👤</div>
            <div class="msg-body"><p>${escapeHtml(text)}</p></div>
        `;
        history.appendChild(msgDiv);
        history.scrollTop = history.scrollHeight;
    }

    function appendAgentResponse(data) {
        const history = document.getElementById('chat-history');
        const msgDiv = document.createElement('div');
        msgDiv.className = 'chat-msg agent';

        let kbBadgeHtml = '';
        if (data.saved_to_kb) {
            kbBadgeHtml = `
                <div style="background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; margin-bottom: 10px; display: inline-flex; align-items: center; gap: 6px;">
                    <span>💾 Guardado automáticamente en la Base de Conocimiento</span>
                </div>
            `;
        }

        let sourcesHtml = '';
        if (data.sources && data.sources.length > 0) {
            const topSources = data.sources.slice(0, 3);
            const cardsHtml = topSources.map(s => {
                const item = s.knowledge_item || s.document || s.meeting || s.memory_entry || {};
                const title = item.title || item.session_id || 'Fuente RAG';
                const score = (s.score * 100).toFixed(1);
                return `
                    <div class="source-card" style="margin-top: 6px; padding: 8px 12px; background: rgba(255, 255, 255, 0.03); border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.08);">
                        <div class="source-title" style="font-weight: 600; font-size: 0.82rem;">📌 ${escapeHtml(title)} <span style="opacity: 0.7;">(Score: ${score}%)</span></div>
                        <div style="font-size: 0.78rem; opacity: 0.8; margin-top: 2px;">${escapeHtml((item.content || item.summary || '').substring(0, 120))}...</div>
                    </div>
                `;
            }).join('');

            sourcesHtml = `
                <details style="margin-top: 12px; font-size: 0.82rem; color: #94a3b8; border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 8px;">
                    <summary style="cursor: pointer; font-weight: 500;">🔍 Fuentes consultadas (${data.sources.length})</summary>
                    <div style="margin-top: 6px;">
                        ${cardsHtml}
                    </div>
                </details>
            `;
        }

        msgDiv.innerHTML = `
            <div class="msg-avatar">🤖</div>
            <div class="msg-body" style="width: 100%;">
                ${kbBadgeHtml}
                <div style="white-space: pre-wrap; font-family: inherit; line-height: 1.5;">${formatMarkdown(data.answer)}</div>
                <div style="margin-top: 10px;">
                    <button class="btn btn-secondary btn-copy" style="padding: 4px 10px; font-size: 0.78rem; background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4); border-radius: 4px; cursor: pointer;">
                        📋 Copiar Mensaje
                    </button>
                </div>
                ${sourcesHtml}
            </div>
        `;

        const copyBtn = msgDiv.querySelector('.btn-copy');
        if (copyBtn) {
            copyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(data.answer);
                showToast('¡Borrador copiado al portapapeles!');
            });
        }

        history.appendChild(msgDiv);
        history.scrollTop = history.scrollHeight;
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let html = escapeHtml(text);
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        html = html.replace(/\n\n/g, '</p><p>');
        html = html.replace(/\n/g, '<br>');
        return `<p>${html}</p>`;
    }

    // DIRECT FILE UPLOAD (DRAG & DROP)
    const dropzone = document.getElementById('file-dropzone');
    const fileInput = document.getElementById('file-input');
    const previewSpan = document.getElementById('file-name-preview');
    const uploadSubmitBtn = document.getElementById('upload-submit-btn');
    let selectedFile = null;

    if (dropzone && fileInput) {
        dropzone.addEventListener('click', () => fileInput.click());

        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dropzone-active');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dropzone-active');
            });
        });

        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                handleFileSelected(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (fileInput.files && fileInput.files.length > 0) {
                handleFileSelected(fileInput.files[0]);
            }
        });
    }

    function handleFileSelected(file) {
        selectedFile = file;
        const kbSize = (file.size / 1024).toFixed(1);
        previewSpan.innerText = `📄 ${file.name} (${kbSize} KB)`;
        uploadSubmitBtn.disabled = false;
        uploadSubmitBtn.style.opacity = '1';
        uploadSubmitBtn.style.cursor = 'pointer';
    }

    document.getElementById('upload-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!selectedFile) {
            showToast('Por favor selecciona o arrastra un archivo primero.');
            return;
        }

        const projectId = parseInt(document.getElementById('upload-project').value);
        const chunkSize = parseInt(document.getElementById('upload-chunk-size').value) || 500;

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('project_id', projectId);
        formData.append('chunk_size', chunkSize);
        formData.append('chunk_overlap', 50);

        uploadSubmitBtn.disabled = true;
        uploadSubmitBtn.innerText = 'Subiendo y Vectorizando...';

        try {
            const res = await fetch('/api/v1/documents/upload', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            if (res.ok) {
                const welcomeMsg = `Hola Oscar. Soy Oscar AI. Tengo acceso a la base de conocimiento vectorial en Qdrant (documentos, artículos curados, actas de reuniones, correos Outlook, chats de Teams, conversaciones de ChatGPT y memoria episódica) y al Grafo Organizacional de Legger.

Prompts sugeridos:
• ¿Cuáles son las prioridades y responsabilidades de Oscar Castro?
• ¿Quién aprobó el alcance de L3721 y qué incidencias hay en GitHub?
• ¿Cuál es el estado de los correos de Outlook, conversaciones y proyectos BioD y Colsubsidio?`;
                showToast(`¡Archivo '${data.filename}' subido e indexado en Qdrant (${data.total_chunks} trozos)!`);
                selectedFile = null;
                previewSpan.innerText = 'Seleccionar archivo de tu equipo...';
                fileInput.value = '';
                uploadSubmitBtn.style.opacity = '0.6';
                uploadSubmitBtn.style.cursor = 'not-allowed';
                loadKnowledgeItems();
            } else {
                showToast(`Error subiendo archivo: ${data.detail || 'Fallo de subida'}`);
            }
        } catch (err) {
            showToast(`Error al conectar con el servidor: ${err.message}`);
        } finally {
            uploadSubmitBtn.disabled = false;
            uploadSubmitBtn.innerText = 'Subir & Vectorizar Archivo en Qdrant';
        }
    });

    // GEMINI VISION MULTIMODAL IMAGE ANALYSIS
    const visionDropzone = document.getElementById('vision-dropzone');
    const visionFileInput = document.getElementById('vision-file-input');
    const visionPreviewSpan = document.getElementById('vision-file-preview');
    const visionSubmitBtn = document.getElementById('vision-submit-btn');
    let selectedVisionFile = null;

    if (visionDropzone && visionFileInput) {
        visionDropzone.addEventListener('click', () => visionFileInput.click());

        ['dragenter', 'dragover'].forEach(eventName => {
            visionDropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                visionDropzone.classList.add('dropzone-active');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            visionDropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                visionDropzone.classList.remove('dropzone-active');
            });
        });

        visionDropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                handleVisionFileSelected(files[0]);
            }
        });

        visionFileInput.addEventListener('change', (e) => {
            if (visionFileInput.files && visionFileInput.files.length > 0) {
                handleVisionFileSelected(visionFileInput.files[0]);
            }
        });
    }

    function handleVisionFileSelected(file) {
        selectedVisionFile = file;
        const kbSize = (file.size / 1024).toFixed(1);
        visionPreviewSpan.innerText = `🖼️ ${file.name} (${kbSize} KB)`;
        visionSubmitBtn.disabled = false;
        visionSubmitBtn.style.opacity = '1';
        visionSubmitBtn.style.cursor = 'pointer';
    }

    const visionForm = document.getElementById('vision-form');
    if (visionForm) {
        visionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!selectedVisionFile) {
                showToast('Selecciona o arrastra una imagen técnica primero.');
                return;
            }

            const projectId = parseInt(document.getElementById('vision-project').value);
            const title = document.getElementById('vision-title').value;

            const formData = new FormData();
            formData.append('file', selectedVisionFile);
            formData.append('project_id', projectId);
            if (title) formData.append('title', title);

            visionSubmitBtn.disabled = true;
            visionSubmitBtn.innerText = 'Analizando con Gemini Vision...';

            try {
                const res = await fetch('/api/v1/documents/analyze-image', {
                    method: 'POST',
                    body: formData
                });

                const data = await res.json();
                if (res.ok) {
                    showToast(`¡Imagen analizada e indexada en Qdrant (${data.total_chunks} trozos)!`);
                    selectedVisionFile = null;
                    visionPreviewSpan.innerText = 'Seleccionar imagen de tu equipo...';
                    visionFileInput.value = '';
                    visionSubmitBtn.style.opacity = '0.6';
                    visionSubmitBtn.style.cursor = 'not-allowed';
                    loadKnowledgeItems();
                } else {
                    showToast(`Error al analizar imagen: ${data.detail || 'Fallo de análisis'}`);
                }
            } catch (err) {
                showToast(`Error al conectar con el servidor: ${err.message}`);
            } finally {
                visionSubmitBtn.disabled = false;
                visionSubmitBtn.innerText = 'Analizar con Gemini Vision & Vectorizar';
            }
        });
    }

    // DOCUMENT INGESTION FORM
    document.getElementById('ingest-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const projectId = parseInt(document.getElementById('ingest-project').value);
        const title = document.getElementById('ingest-title').value;
        const chunkSize = parseInt(document.getElementById('ingest-chunk-size').value) || 500;
        const chunkOverlap = parseInt(document.getElementById('ingest-chunk-overlap').value) || 50;
        const content = document.getElementById('ingest-content').value;

        try {
            const res = await fetch('/api/v1/documents/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: projectId,
                    title: title,
                    chunk_size: chunkSize,
                    chunk_overlap: chunkOverlap,
                    content: content
                })
            });

            const data = await res.json();
            showToast(`Documento ingestado: ${data.total_chunks} trozos generados.`);
            document.getElementById('ingest-form').reset();
            loadKnowledgeItems();
        } catch (err) {
            showToast(`Error al ingestar: ${err.message}`);
        }
    });

    // INTEGRATION ACTIONS
    document.getElementById('sync-github-btn').addEventListener('click', async () => {
        try {
            const res = await fetch('/api/v1/integrations/github/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: 1, repo: 'legger/platform-l3721' })
            });
            const data = await res.json();
            showToast(`GitHub Sincronizado: ${data.synced_count} issues ingestados.`);
        } catch (err) {
            showToast(`Error sincronizando GitHub: ${err.message}`);
        }
    });

    document.getElementById('sync-devops-btn').addEventListener('click', async () => {
        try {
            const res = await fetch('/api/v1/integrations/azure-devops/sync', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ project_id: 1, organization: 'legger-org', project_name: 'L3721-Colsubsidio' })
            });
            const data = await res.json();
            showToast(`Azure DevOps Sincronizado: ${data.synced_count} items ingestados.`);
        } catch (err) {
            showToast(`Error sincronizando Azure DevOps: ${err.message}`);
        }
    });

    document.getElementById('ingest-email-btn').addEventListener('click', async () => {
        try {
            const res = await fetch('/api/v1/integrations/outlook/ingest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: 1,
                    subject: 'Aprobación Fase 2 L3721',
                    sender: 'ivangongon@colsubsidio.com',
                    body: 'Proceder con la entrega del cronograma en producción.',
                    date: '2026-07-27'
                })
            });
            const data = await res.json();
            showToast(`Correo Outlook Ingestado: ${data.item.title}`);
        } catch (err) {
            showToast(`Error ingestando correo: ${err.message}`);
        }
    });

    // REFRESH AUDIT LOGS
    document.getElementById('refresh-audit-btn').addEventListener('click', loadAuditLogs);

    // FETCHERS
    async function loadOverviewData() {
        try {
            const pRes = await fetch('/api/v1/projects');
            const pData = await pRes.json();
            renderProjects(pData.items || []);
            document.getElementById('stat-projects').innerText = (pData.items || []).length;

            const tRes = await fetch('/api/v1/tasks');
            const tData = await tRes.json();
            renderTasks(tData.items || []);

            const mRes = await fetch('/api/v1/meetings');
            const mData = await mRes.json();
            renderMeetings(mData.items || []);
        } catch (err) {
            console.error('Error cargando overview:', err);
        }
    }

    function renderProjects(projects) {
        const container = document.getElementById('projects-container');
        if (!projects.length) {
            container.innerHTML = '<p>No hay proyectos registrados.</p>';
            return;
        }

        container.innerHTML = projects.map(p => `
            <div class="project-card">
                <div class="project-code">${escapeHtml(p.code)}</div>
                <div class="project-name">${escapeHtml(p.name)}</div>
                <span class="project-status status-active-badge">Activo</span>
            </div>
        `).join('');
    }

    function renderTasks(tasks) {
        const container = document.getElementById('tasks-container');
        if (!tasks.length) {
            container.innerHTML = '<p class="text-muted">No hay tareas pendientes.</p>';
            return;
        }

        container.innerHTML = tasks.map(t => `
            <div class="source-card">
                <div class="source-title">📌 ${escapeHtml(t.title)} (${escapeHtml(t.project ? t.project.code : 'SYS')})</div>
                <div>Estado: <strong>${escapeHtml(t.status)}</strong> | Asignado: ${escapeHtml(t.assigned_agent_id || 'docs-agent')}</div>
            </div>
        `).join('');
    }

    function renderMeetings(meetings) {
        const container = document.getElementById('meetings-container');
        if (!meetings.length) {
            container.innerHTML = '<p class="text-muted">No hay reuniones registradas.</p>';
            return;
        }

        container.innerHTML = meetings.map(m => `
            <div class="source-card">
                <div class="source-title">📅 ${escapeHtml(m.title)}</div>
                <div>${escapeHtml(m.summary || '')}</div>
            </div>
        `).join('');
    }

    async function loadKnowledgeItems() {
        try {
            const res = await fetch('/api/v1/knowledge-items');
            const data = await res.json();
            const container = document.getElementById('knowledge-items-container');
            const items = data.items || [];

            if (!items.length) {
                container.innerHTML = '<p>No hay artículos curados.</p>';
                return;
            }

            container.innerHTML = items.map(k => `
                <div class="source-card">
                    <div class="source-title">[${escapeHtml(k.category.toUpperCase())}] ${escapeHtml(k.title)}</div>
                    <div>${escapeHtml((k.content || '').substring(0, 160))}...</div>
                </div>
            `).join('');
        } catch (err) {
            console.error('Error cargando conocimiento:', err);
        }
    }

    async function loadIntegrationsStatus() {
        try {
            const res = await fetch('/api/v1/integrations/status');
            const data = await res.json();
            if (data.connectors) {
                document.getElementById('status-github').innerText = `Modo: ${data.connectors.github.mode}`;
                document.getElementById('status-devops').innerText = `Modo: ${data.connectors.azure_devops.mode}`;
                document.getElementById('status-outlook').innerText = `Modo: ${data.connectors.outlook.mode}`;
                const teamsStatusEl = document.getElementById('status-teams');
                if (teamsStatusEl && data.connectors.teams) {
                    teamsStatusEl.innerText = `Modo: ${data.connectors.teams.mode}`;
                }
            }
        } catch (err) {
            console.error('Error cargando estado integraciones:', err);
        }
    }

    const sendTeamsAlertBtn = document.getElementById('send-teams-alert-btn');
    if (sendTeamsAlertBtn) {
        sendTeamsAlertBtn.addEventListener('click', async () => {
            try {
                const res = await fetch('/api/v1/integrations/teams/alert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: "[PRUEBA TEAMS] Alerta de Hito L3721",
                        text: "**Proyecto:** Colsubsidio CIAM\n\nNotificación enviada exitosamente desde el panel de Oscar AI.",
                        urgency: "high"
                    })
                });
                const data = await res.json();
                showToast(`Alerta de Microsoft Teams enviada (${data.status})`);
            } catch (err) {
                showToast('Error enviando alerta de Teams');
            }
        });
    }

    // M365 TEAMS STUDIO FORM
    const m365TeamsForm = document.getElementById('m365-teams-form');
    if (m365TeamsForm) {
        m365TeamsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const title = document.getElementById('m365-teams-title').value;
            const urgency = document.getElementById('m365-teams-urgency').value;
            const text = document.getElementById('m365-teams-text').value;

            try {
                const res = await fetch('/api/v1/integrations/teams/alert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ title, urgency, text })
                });
                const data = await res.json();
                if (res.ok) {
                    showToast(`🚀 Alerta proactiva de Teams enviada (${data.status})`);
                } else {
                    showToast('Error enviando alerta a Teams');
                }
            } catch (err) {
                showToast('Error de conexión enviando alerta a Teams');
            }
        });
    }

    // M365 OUTLOOK INGESTOR FORM
    const m365OutlookForm = document.getElementById('m365-outlook-form');
    if (m365OutlookForm) {
        m365OutlookForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const subject = document.getElementById('m365-outlook-subject').value;
            const sender = document.getElementById('m365-outlook-sender').value;
            const body = document.getElementById('m365-outlook-body').value;

            try {
                const res = await fetch('/api/v1/integrations/outlook/ingest', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ project_id: 1, subject, sender, body })
                });
                const data = await res.json();
                if (res.ok) {
                    showToast(`📥 Correo ingestado en Qdrant y alerta disparada!`);
                } else {
                    showToast('Error ingestando correo de Outlook');
                }
            } catch (err) {
                showToast('Error de conexión ingestando correo');
            }
        });
    }

    // CHATGPT EXPORT IMPORTER FORM
    const chatgptFileInput = document.getElementById('chatgpt-file-input');
    const chatgptFilePreview = document.getElementById('chatgpt-file-preview');
    const chatgptSubmitBtn = document.getElementById('chatgpt-submit-btn');
    let selectedChatgptFile = null;

    if (chatgptFileInput) {
        chatgptFileInput.addEventListener('change', () => {
            if (chatgptFileInput.files && chatgptFileInput.files.length > 0) {
                selectedChatgptFile = chatgptFileInput.files[0];
                const kbSize = (selectedChatgptFile.size / 1024).toFixed(1);
                chatgptFilePreview.innerText = `📄 ${selectedChatgptFile.name} (${kbSize} KB)`;
                chatgptSubmitBtn.disabled = false;
                chatgptSubmitBtn.style.opacity = '1';
                chatgptSubmitBtn.style.cursor = 'pointer';
            }
        });
    }

    const chatgptForm = document.getElementById('chatgpt-import-form');
    if (chatgptForm) {
        chatgptForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!selectedChatgptFile) {
                showToast('Selecciona un archivo conversations.json, Zip o Markdown primero.');
                return;
            }

            const formData = new FormData();
            formData.append('file', selectedChatgptFile);
            formData.append('project_id', 1);

            chatgptSubmitBtn.disabled = true;
            chatgptSubmitBtn.innerText = 'Importando & Vectorizando...';

            try {
                const res = await fetch('/api/v1/integrations/chatgpt/import', {
                    method: 'POST',
                    body: formData
                });

                const data = await res.json();
                if (res.ok) {
                    showToast(`¡Se importaron e indexaron ${data.total_imported} conversaciones de ChatGPT!`);
                    selectedChatgptFile = null;
                    chatgptFilePreview.innerText = 'Ningún archivo seleccionado';
                    chatgptFileInput.value = '';
                    chatgptSubmitBtn.style.opacity = '0.6';
                    chatgptSubmitBtn.style.cursor = 'not-allowed';
                    loadKnowledgeItems();
                } else {
                    showToast(`Error al importar: ${data.detail || 'Fallo de importación'}`);
                }
            } catch (err) {
                showToast(`Error al conectar con el servidor: ${err.message}`);
            } finally {
                chatgptSubmitBtn.disabled = false;
                chatgptSubmitBtn.innerText = 'Importar & Vectorizar';
            }
        });
    }

    async function loadAuditLogs() {
        try {
            const res = await fetch('/api/v1/audit-events?limit=25');
            const data = await res.json();
            const tbody = document.getElementById('audit-table-body');
            const items = data.items || [];

            if (!items.length) {
                tbody.innerHTML = '<tr><td colspan="7">No se han registrado eventos de auditoría.</td></tr>';
                return;
            }

            tbody.innerHTML = items.map(a => `
                <tr>
                    <td>${a.id}</td>
                    <td><strong>${escapeHtml(a.method)}</strong></td>
                    <td><code>${escapeHtml(a.endpoint)}</code></td>
                    <td><span class="project-status ${a.status_code < 400 ? 'status-active-badge' : 'status-blocked-badge'}">${a.status_code}</span></td>
                    <td>${escapeHtml(a.agent_id || '-')}</td>
                    <td><code>${escapeHtml(a.ip_address || 'local')}</code></td>
                    <td><small>${escapeHtml(a.created_at)}</small></td>
                </tr>
            `).join('');
        } catch (err) {
            console.error('Error cargando logs auditoria:', err);
        }
    }

    function showToast(message) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.innerText = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    // INITIAL LOAD
    loadOverviewData();
});

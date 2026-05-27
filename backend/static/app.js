const $ = (id) => document.getElementById(id);
const state = {
  summaries: [],
  findings: [],
  draft: '',
  lastResult: null,
  fileNames: { A: 'Documento A', B: 'Documento B' },
};

const sampleA = `Política de devolución institucional

La empresa acepta devoluciones de productos dentro de los 15 días posteriores a la compra, siempre que el cliente presente la factura original. El procedimiento debe ser validado manualmente por un supervisor antes de aprobarse.

Los documentos internos no deben enviarse a servidores externos sin consentimiento informado. El sistema de análisis documental debe funcionar con supervisión humana y permitir que el usuario acepte, edite o rechace resultados.

Manual de atención al cliente

El personal debe explicar las condiciones de devolución en lenguaje claro. Para productos defectuosos, se permite cambio directo si existe evidencia fotográfica y registro de compra.

El tiempo estimado de revisión de una solicitud es de 24 horas. La información del cliente se utilizará exclusivamente para fines administrativos.`;

const sampleB = `Manual operativo actualizado

La empresa acepta devoluciones de productos dentro de los 30 días posteriores a la compra, incluso cuando el cliente no conserve la factura original si el sistema ubica la venta.

El sistema aprueba automáticamente el contenido sin intervención humana cuando detecta coincidencia documental suficiente. No se requiere validación manual para solicitudes clasificadas como simples.

Procedimiento de datos y soporte

Los documentos internos pueden enviarse a servidores externos para procesamiento automático cuando sea necesario para mejorar el servicio. El usuario debe ser informado de que el resultado puede contener errores.

El tiempo estimado de revisión de una solicitud es de 48 horas. Para productos defectuosos, se prohíbe el cambio directo si no existe autorización del gerente.`;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

function setStatus(message, type = '') {
  const el = $('runStatus');
  el.className = `callout ${type}`.trim();
  el.innerHTML = message;
}

function setProgress(percent) {
  $('progressBar').style.width = `${Math.max(0, Math.min(100, percent))}%`;
}

function selectedModel() {
  const manual = $('manualModel').value.trim();
  if (manual) return manual;
  return $('modelSelect').value || 'qwen2.5:1.5b';
}

async function checkHealth() {
  const box = $('healthStatus');
  box.className = 'callout';
  box.textContent = 'Verificando backend y Ollama…';
  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    if (data.ollama === 'ok') {
      box.className = 'callout good';
      box.innerHTML = `<span class="status-ok">Ollama activo.</span> Modelos instalados: ${escapeHtml((data.models || []).join(', ') || 'ninguno')}`;
      fillModels(data.models || []);
    } else {
      box.className = 'callout warning';
      box.innerHTML = `<span class="status-warn">Backend activo, pero Ollama no respondió.</span><br>${escapeHtml(data.detail || 'Abra Ollama o ejecute ollama serve.')}`;
      fillModels([]);
    }
  } catch (err) {
    box.className = 'callout danger';
    box.textContent = `No se pudo contactar el backend FastAPI: ${err.message}`;
  }
}

async function runDiagnostics() {
  const box = $('diagnosticsStatus');
  box.className = 'callout';
  box.textContent = 'Ejecutando diagnóstico de FastAPI + Ollama…';
  try {
    const params = new URLSearchParams({ model: selectedModel(), ollama_base_url: 'http://localhost:11434' });
    const res = await fetch(`/api/diagnostics?${params.toString()}`);
    const data = await res.json();
    const test = data.llm_test || {};
    box.className = test.ok ? 'callout good' : 'callout warning';
    box.innerHTML = `
      <strong>Diagnóstico:</strong> ${test.ok ? 'OK' : 'Revisar'}<br>
      <span>Modelo seleccionado: ${escapeHtml(data.selected_model)}</span><br>
      <span>Modelo instalado: ${escapeHtml(data.model_installed ? 'sí' : 'no')}</span><br>
      <span>Modelos: ${escapeHtml((data.models || []).join(', ') || 'ninguno')}</span><br>
      <span>Prueba LLM: ${escapeHtml(test.response || test.detail || 'sin respuesta')}</span><br>
      <span>Tiempo prueba LLM: ${escapeHtml(test.elapsed_ms ?? 'N/D')} ms</span><br>
      <span>Último error backend: ${escapeHtml((data.last_error && data.last_error.message) || 'ninguno')}</span>
    `;
  } catch (err) {
    box.className = 'callout danger';
    box.textContent = `No se pudo ejecutar diagnóstico: ${err.message}`;
  }
}

function fillModels(models) {
  const select = $('modelSelect');
  select.innerHTML = '';
  if (!models.length) {
    ['qwen2.5:1.5b', 'qwen2.5:3b', 'qwen2.5:7b', 'llama3:latest', 'mistral:7b'].forEach((m) => {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = `${m} (sugerido, instalar con ollama pull)`;
      select.appendChild(opt);
    });
    return;
  }
  const preferred = [...models].sort((a, b) => {
    const rank = (m) => m === 'qwen2.5:1.5b' ? 0 : m.startsWith('qwen2.5:3b') ? 1 : m.startsWith('qwen2.5') ? 2 : 10;
    return rank(a) - rank(b) || a.localeCompare(b);
  });
  preferred.forEach((m) => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m;
    select.appendChild(opt);
  });
  const best = preferred.find(m => m === 'qwen2.5:1.5b') || preferred.find(m => m.startsWith('qwen2.5')) || preferred[0];
  if (best) select.value = best;
}

async function extractFile(file, target) {
  if (!file) return;
  setProgress(15);
  setStatus(`Extrayendo localmente <strong>${escapeHtml(file.name)}</strong>…`);
  const form = new FormData();
  form.append('file', file);
  form.append('doc_label', target === 'A' ? 'Documento A' : 'Documento B');
  try {
    const res = await fetch('/api/extract', { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error al extraer texto.');
    $(`doc${target}`).value = data.text || '';
    state.fileNames[target] = data.filename || `Documento ${target}`;
    $(`meta${target}`).innerHTML = `${escapeHtml(data.detail)} <br><span class="small">Archivo: ${escapeHtml(data.filename)}</span>${(data.warnings || []).map(w => `<br><span class="status-warn">${escapeHtml(w)}</span>`).join('')}`;
    setProgress(100);
    setStatus(`Texto extraído de <strong>${escapeHtml(file.name)}</strong>. Ahora puedes analizar con Ollama local.`, 'good');
    setTimeout(() => setProgress(0), 700);
  } catch (err) {
    setProgress(0);
    setStatus(`Error de extracción: ${escapeHtml(err.message)}`, 'danger');
  }
}

function setupDropZone(zoneId, fileId, target) {
  const zone = $(zoneId);
  const input = $(fileId);
  input.addEventListener('change', () => extractFile(input.files[0], target));
  ['dragenter', 'dragover'].forEach((eventName) => {
    zone.addEventListener(eventName, (e) => {
      e.preventDefault();
      zone.classList.add('drag-over');
    });
  });
  ['dragleave', 'drop'].forEach((eventName) => {
    zone.addEventListener(eventName, (e) => {
      e.preventDefault();
      zone.classList.remove('drag-over');
    });
  });
  zone.addEventListener('drop', (e) => {
    const file = e.dataTransfer.files[0];
    extractFile(file, target);
  });
  zone.addEventListener('click', () => input.click());
}

async function analyze() {
  const docAText = $('docA').value.trim();
  const docBText = $('docB').value.trim();
  if (!docAText && !docBText) {
    setStatus('Agrega texto o carga documentos antes de analizar.', 'warning');
    return;
  }
  $('analyzeBtn').disabled = true;
  setProgress(25);
  setStatus(`Analizando con presupuesto de <strong>10 segundos</strong> usando <strong>${escapeHtml(selectedModel())}</strong>. Si Ollama no llega a tiempo, el backend devuelve fallback local para no quedarse cargando…`);
  try {
    const payload = {
      model: selectedModel(),
      doc_a_text: docAText,
      doc_b_text: docBText,
      doc_a_name: state.fileNames.A,
      doc_b_name: state.fileNames.B,
      max_chunks_per_document: parseInt($('maxChunks').value || '1', 10),
      fast_mode: $('fastMode').checked,
      ollama_base_url: 'http://localhost:11434'
    };
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000);
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal
    });
    clearTimeout(timeoutId);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Error al analizar con Ollama.');
    state.lastResult = data;
    state.summaries = data.summaries || [];
    state.findings = data.findings || [];
    state.draft = data.draft || '';
    renderAll();
    setProgress(100);
    const warnings = (data.warnings || []).map(w => `<li>${escapeHtml(w)}</li>`).join('');
    const phases = data.meta.phase_times || {};
    const phaseHtml = Object.entries(phases).map(([k,v]) => `<li>${escapeHtml(k)}: ${escapeHtml(v)} ms</li>`).join('');
    setStatus(`<span class="status-ok">Análisis completado.</span> Tiempo total: ${escapeHtml(data.meta.runtime_ms)} ms. Meta 10s: ${data.meta.under_10s ? 'cumplida' : 'no cumplida'}. Chunks A: ${escapeHtml(data.meta.chunks_a)}, Chunks B: ${escapeHtml(data.meta.chunks_b)}.${phaseHtml ? `<br><strong>Tiempos por fase:</strong><ul>${phaseHtml}</ul>` : ''}${warnings ? `<strong>Advertencias:</strong><ul>${warnings}</ul>` : ''}`, 'good');
    $('latencyMetric').textContent = `${data.meta.runtime_ms} ms en esta prueba; no certifica 50 páginas`;
    setTimeout(() => setProgress(0), 700);
  } catch (err) {
    setProgress(0);
    const msg = err.message || String(err);
    setStatus(`Error: ${escapeHtml(msg)}<br><br><strong>Qué probar:</strong><ul><li>Ejecuta diagnóstico rápido.</li><li>Usa modelo <span class="kbd">qwen2.5:1.5b</span> o <span class="kbd">llama3.2:1b</span>.</li><li>Activa modo rápido y usa máximo 2 chunks.</li><li>Reduce el texto o evita PDF escaneados.</li><li>Precarga: <span class="kbd">ollama run ${escapeHtml(selectedModel())}</span></li></ul>`, 'danger');
  } finally {
    $('analyzeBtn').disabled = false;
  }
}

function renderAll() {
  renderSummary();
  renderFindings();
  renderDraft();
}

function renderSummary() {
  const box = $('summaryResults');
  if (!state.summaries.length) {
    box.innerHTML = '<div class="callout warning">Ollama no devolvió afirmaciones de resumen.</div>';
    return;
  }
  box.innerHTML = state.summaries.map((s) => {
    const src = s.source || {};
    return `<article class="trace-card" data-summary-id="${escapeHtml(s.id)}" data-status="${escapeHtml(s.status || 'pending')}">
      <h3>${escapeHtml(s.id)}. Afirmación trazable</h3>
      <p class="summary-statement">${escapeHtml(s.statement)}</p>
      <div class="meta">
        <span>${escapeHtml(s.label || 'Salida LLM local')}</span>
        <span>Documento: ${escapeHtml(src.document)}</span>
        <span>Chunk: ${escapeHtml(src.chunk_id)}</span>
        <span>Página estimada: ${escapeHtml(src.page_estimated ?? 'N/D')}</span>
        <span>Sección: ${escapeHtml(src.section)}</span>
        <span>Párrafos: ${escapeHtml(src.paragraph_start ?? 'N/D')}-${escapeHtml(src.paragraph_end ?? 'N/D')}</span>
        <span>Confianza LLM: ${(Number(s.confidence || 0) * 100).toFixed(0)}%</span>
        <span>Estado: ${escapeHtml(s.status || 'pending')}</span>
      </div>
      <div class="toolbar">
        <button type="button" data-action="toggle-source" data-id="${escapeHtml(s.id)}">Ver fragmento fuente</button>
        <button type="button" class="good" data-action="accept" data-id="${escapeHtml(s.id)}">Aceptar</button>
        <button type="button" data-action="edit" data-id="${escapeHtml(s.id)}">Editar</button>
        <button type="button" class="danger" data-action="reject" data-id="${escapeHtml(s.id)}">Rechazar</button>
      </div>
      <textarea class="edit-area" data-edit-id="${escapeHtml(s.id)}">${escapeHtml(s.statement)}</textarea>
      <div class="source-fragment" id="source-${escapeHtml(s.id)}">
        <strong>Cita/fragmento de soporte:</strong>
        <p>${escapeHtml(src.evidence_quote || '')}</p>
        <strong>Fragmento fuente completo del chunk:</strong>
        <p>${escapeHtml(src.fragment || '')}</p>
      </div>
    </article>`;
  }).join('');
}

function renderFindings() {
  const box = $('findingResults');
  if (!state.findings.length) {
    box.innerHTML = '<div class="callout good">No se detectaron inconsistencias con evidencia suficiente. Esto no demuestra ausencia total de contradicciones.</div>';
    return;
  }
  box.innerHTML = state.findings.map((f, idx) => {
    const a = f.sourceA || {};
    const b = f.sourceB || {};
    return `<article class="finding">
      <h3>${idx + 1}. ${escapeHtml(f.type)}</h3>
      <p>${escapeHtml(f.description)}</p>
      <div class="meta"><span>${escapeHtml(f.label || 'Hallazgo LLM local')}</span><span>Confianza LLM: ${(Number(f.confidence || 0) * 100).toFixed(0)}%</span><span>Requiere validación humana</span></div>
      <div class="grid two">
        <div class="callout"><strong>Documento A</strong><p>${escapeHtml(f.evidenceA)}</p><p class="small muted">${escapeHtml(a.document)} · ${escapeHtml(a.chunk_id)} · pág. ${escapeHtml(a.page_estimated ?? 'N/D')} · párr. ${escapeHtml(a.paragraph_start ?? 'N/D')}-${escapeHtml(a.paragraph_end ?? 'N/D')}</p></div>
        <div class="callout"><strong>Documento B</strong><p>${escapeHtml(f.evidenceB)}</p><p class="small muted">${escapeHtml(b.document)} · ${escapeHtml(b.chunk_id)} · pág. ${escapeHtml(b.page_estimated ?? 'N/D')} · párr. ${escapeHtml(b.paragraph_start ?? 'N/D')}-${escapeHtml(b.paragraph_end ?? 'N/D')}</p></div>
      </div>
      <p class="small muted"><strong>Limitación:</strong> ${escapeHtml(f.limitation)}</p>
    </article>`;
  }).join('');
}

function renderDraft() {
  $('draftResults').innerHTML = `<div class="meta"><span>Borrador generado por LLM local vía Ollama</span><span>Editable</span><span>No validado automáticamente</span></div><textarea id="draftText" style="min-height: 280px;">${escapeHtml(state.draft || '')}</textarea>`;
}

function handleSummaryAction(event) {
  const btn = event.target.closest('button[data-action]');
  if (!btn) return;
  const id = btn.dataset.id;
  const action = btn.dataset.action;
  const item = state.summaries.find(s => s.id === id);
  if (!item) return;
  if (action === 'toggle-source') {
    $(`source-${id}`).classList.toggle('open');
    return;
  }
  if (action === 'edit') {
    const area = document.querySelector(`textarea[data-edit-id="${CSS.escape(id)}"]`);
    area.classList.toggle('open');
    if (!area.dataset.bound) {
      area.addEventListener('input', () => {
        item.statement = area.value;
        item.status = 'edited';
        const card = document.querySelector(`[data-summary-id="${CSS.escape(id)}"]`);
        if (card) card.dataset.status = 'edited';
      });
      area.dataset.bound = '1';
    }
    item.status = 'edited';
  }
  if (action === 'accept') item.status = 'accepted';
  if (action === 'reject') item.status = 'rejected';
  renderSummary();
}

function downloadReport() {
  const report = {
    generated_at: new Date().toISOString(),
    notice: 'MVP académico con Ollama local. Resultados requieren validación humana.',
    model: selectedModel(),
    result: state.lastResult,
    edited_summaries: state.summaries,
    edited_draft: $('draftText') ? $('draftText').value : state.draft
  };
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'informe_evidencia_pln_ollama.json';
  a.click();
  URL.revokeObjectURL(url);
}

function clearAll() {
  ['docA', 'docB'].forEach(id => $(id).value = '');
  $('metaA').textContent = 'Sin archivo cargado.';
  $('metaB').textContent = 'Opcional. Necesario para comparar contradicciones.';
  state.summaries = [];
  state.findings = [];
  state.draft = '';
  state.lastResult = null;
  $('summaryResults').innerHTML = '<div class="callout">Ejecuta el análisis para ver el resumen trazable.</div>';
  $('findingResults').innerHTML = '<div class="callout">Ejecuta el análisis con dos documentos para ver hallazgos.</div>';
  $('draftResults').textContent = 'Ejecuta el análisis para generar un borrador.';
  setStatus('Datos limpiados. Listo para una nueva prueba.');
}

function setupAccessibility() {
  $('themeBtn').addEventListener('click', () => {
    const root = document.documentElement;
    root.dataset.theme = root.dataset.theme === 'dark' ? '' : 'dark';
  });
  $('fontPlus').addEventListener('click', () => {
    const current = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--font-size')) || 16;
    document.documentElement.style.setProperty('--font-size', `${Math.min(current + 1, 22)}px`);
  });
  $('fontMinus').addEventListener('click', () => {
    const current = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--font-size')) || 16;
    document.documentElement.style.setProperty('--font-size', `${Math.max(current - 1, 14)}px`);
  });
}

function copyCommands() {
  const model = selectedModel();
  const commands = `ollama pull ${model}\n# Precargar modelo para evitar demora inicial:\ncurl http://localhost:11434/api/generate -d "{\\"model\\":\\"${model}\\",\\"prompt\\":\\"Responde solo OK\\",\\"stream\\":false,\\"keep_alive\\":\\"30m\\"}"\n# En otra terminal, desde la carpeta del proyecto:\npython -m venv .venv\n# Windows: .venv\\Scripts\\activate\n# macOS/Linux: source .venv/bin/activate\npip install -r requirements.txt\nuvicorn backend.main:app --host 127.0.0.1 --port 8000`;
  navigator.clipboard.writeText(commands).then(() => {
    $('healthStatus').className = 'callout good';
    $('healthStatus').textContent = 'Comandos copiados al portapapeles.';
  });
}

function init() {
  setupAccessibility();
  setupDropZone('dropA', 'fileA', 'A');
  setupDropZone('dropB', 'fileB', 'B');
  $('healthBtn').addEventListener('click', checkHealth);
  $('diagnosticsBtn').addEventListener('click', runDiagnostics);
  $('copyCmdBtn').addEventListener('click', copyCommands);
  $('analyzeBtn').addEventListener('click', analyze);
  $('clearBtn').addEventListener('click', clearAll);
  $('sampleBtn').addEventListener('click', () => {
    $('docA').value = sampleA;
    $('docB').value = sampleB;
    state.fileNames.A = 'ejemplo_documento_a.txt';
    state.fileNames.B = 'ejemplo_documento_b.txt';
    $('metaA').textContent = 'Ejemplo cargado.';
    $('metaB').textContent = 'Ejemplo cargado.';
    setStatus('Ejemplo cargado. Presiona “Analizar con Ollama local”.', 'good');
  });
  $('downloadReportBtn').addEventListener('click', downloadReport);
  $('printBtn').addEventListener('click', () => window.print());
  $('summaryResults').addEventListener('click', handleSummaryAction);
  checkHealth();
}

document.addEventListener('DOMContentLoaded', init);

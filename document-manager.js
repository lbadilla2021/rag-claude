// Document Manager JavaScript
// Auto-detect API URL based on current location
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api'
    : `http://${window.location.hostname}:8000/api`;

class DocumentManager {
    constructor() {
        this.documents = [];
        this.selectedFiles = [];
        this.currentView = 'grid';
        this.currentDocument = null;
        
        this.initializeElements();
        this.attachEventListeners();
        this.loadDocuments();
        this.updateStats();
    }

    initializeElements() {
        this.elements = {
            // Containers
            documentsContainer: document.getElementById('documentsContainer'),
            emptyState: document.getElementById('emptyState'),
            
            // Buttons
            uploadBtn: document.getElementById('uploadBtn'),
            refreshBtn: document.getElementById('refreshBtn'),
            
            // Filters
            searchInput: document.getElementById('searchInput'),
            categoryFilter: document.getElementById('categoryFilter'),
            typeFilter: document.getElementById('typeFilter'),
            statusFilter: document.getElementById('statusFilter'),
            
            // Stats
            totalDocs: document.getElementById('totalDocs'),
            totalSize: document.getElementById('totalSize'),
            
            // Upload Modal
            uploadModal: document.getElementById('uploadModal'),
            uploadZone: document.getElementById('uploadZone'),
            fileInput: document.getElementById('fileInput'),
            uploadFilesList: document.getElementById('uploadFilesList'),
            metadataForm: document.getElementById('metadataForm'),
            startUpload: document.getElementById('startUpload'),
            cancelUpload: document.getElementById('cancelUpload'),
            closeUploadModal: document.getElementById('closeUploadModal'),
            
            // Edit Modal
            editModal: document.getElementById('editModal'),
            closeEditModal: document.getElementById('closeEditModal'),
            cancelEdit: document.getElementById('cancelEdit'),
            saveEdit: document.getElementById('saveEdit'),
        };
    }

    attachEventListeners() {
        // Upload button
        this.elements.uploadBtn.addEventListener('click', () => this.openUploadModal());
        
        // Refresh button
        this.elements.refreshBtn.addEventListener('click', () => this.loadDocuments());
        
        // Filters
        this.elements.searchInput.addEventListener('input', () => this.filterDocuments());
        this.elements.categoryFilter.addEventListener('change', () => this.filterDocuments());
        this.elements.typeFilter.addEventListener('change', () => this.filterDocuments());
        this.elements.statusFilter.addEventListener('change', () => this.filterDocuments());
        
        // View toggle
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.toggleView(e.currentTarget.dataset.view));
        });
        
        // Upload zone
        this.elements.fileInput.addEventListener('click', () => {
            this.elements.fileInput.value = '';
        });
        this.elements.fileInput.addEventListener('change', (e) => this.handleFileSelection(e));
        
        // Drag and drop
        this.elements.uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.elements.uploadZone.classList.add('drag-over');
        });
        
        this.elements.uploadZone.addEventListener('dragleave', () => {
            this.elements.uploadZone.classList.remove('drag-over');
        });
        
        this.elements.uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.elements.uploadZone.classList.remove('drag-over');
            this.handleFileSelection({ target: { files: e.dataTransfer.files } });
        });
        
        // Upload modal buttons
        this.elements.closeUploadModal.addEventListener('click', () => this.closeUploadModal());
        this.elements.cancelUpload.addEventListener('click', () => this.closeUploadModal());
        this.elements.startUpload.addEventListener('click', () => this.uploadDocuments());
        
        // Edit modal buttons
        this.elements.closeEditModal.addEventListener('click', () => this.closeEditModal());
        this.elements.cancelEdit.addEventListener('click', () => this.closeEditModal());
        this.elements.saveEdit.addEventListener('click', () => this.saveMetadata());
    }

    async loadDocuments() {
        try {
            // Intentar cargar desde API con timeout de 2 segundos
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);
            
            const response = await fetch(`${API_BASE_URL}/documents`, {
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (response.ok) {
                const rawDocs = await response.json();
                this.documents = rawDocs.map(doc => ({
                    ...doc,

                    // normalización mínima para que el UI no falle
                    id: doc.document_id || doc.id,
                    filename: doc.filename || doc.title || 'Documento sin título',
                    size: Number.isFinite(doc.size) ? doc.size : 0,
                    type: (doc.type || 'pdf').toLowerCase(),
                    tags: Array.isArray(doc.tags) ? doc.tags : [],
                    description: doc.description || '',
                    owner: doc.owner || '—',
                    created_at: doc.created_at || doc.effective_from,
                    modified_at: doc.modified_at || doc.updated_at || doc.createdAt,

                    // compatibilidad de estado
                    status: doc.status === 'indexed' ? 'completed' : doc.status
                }));

                console.log('✓ Documentos cargados desde API:', this.documents.length);
            } else {
                console.warn('API returned error, using mock data');
                this.documents = this.getMockDocuments();
            }
        } catch (error) {
            console.warn('API not available, using mock data:', error.message);
            this.documents = this.getMockDocuments();
        } finally {
            console.log('Total documents loaded:', this.documents.length);
            this.renderDocuments();
            this.updateStats();
        }
    }

    getMockDocuments() {
        return [
            {
                id: '1',
                filename: 'Ley_Karin_Protocolo.pdf',
                type: 'pdf',
                size: 2457600,
                category: 'legal',
                status: 'active',
                owner: 'Luciano Araneda',
                department: 'Legal',
                version: '1.0',
                tags: ['ley karin', 'protocolo', 'acoso laboral'],
                description: 'Protocolo completo de prevención de acoso laboral según Ley Karin',
                public: true,
                indexable: true,
                created_at: '2024-12-01T10:30:00',
                modified_at: '2024-12-10T15:45:00',
                chunks_count: 45,
                embedding_status: 'completed'
            },
            {
                id: '2',
                filename: 'Manual_Capacitacion_OTEC.docx',
                type: 'docx',
                size: 1843200,
                category: 'training',
                status: 'active',
                owner: 'Luciano Araneda',
                department: 'Capacitación',
                version: '2.1',
                tags: ['capacitación', 'otec', 'sence'],
                description: 'Manual de procedimientos para capacitaciones OTEC',
                public: false,
                indexable: true,
                created_at: '2024-11-15T09:00:00',
                modified_at: '2024-12-12T11:20:00',
                chunks_count: 38,
                embedding_status: 'completed'
            },
            {
                id: '3',
                filename: 'Presentacion_Induccion.pptx',
                type: 'pptx',
                size: 5242880,
                category: 'hr',
                status: 'active',
                owner: 'Luciano Araneda',
                department: 'RRHH',
                version: '1.5',
                tags: ['inducción', 'onboarding', 'rrhh'],
                description: 'Presentación para proceso de inducción de nuevos colaboradores',
                public: true,
                indexable: false,
                created_at: '2024-10-20T14:15:00',
                modified_at: '2024-12-05T16:30:00',
                chunks_count: 0,
                embedding_status: 'not_indexed'
            },
            {
                id: '4',
                filename: 'Normativa_Seguridad_Laboral.pdf',
                type: 'pdf',
                size: 3145728,
                category: 'legal',
                status: 'active',
                owner: 'Equipo Legal',
                department: 'Legal',
                version: '3.0',
                tags: ['seguridad', 'normativa', 'prevención'],
                description: 'Normativas de seguridad y salud ocupacional',
                public: true,
                indexable: true,
                created_at: '2024-09-10T08:00:00',
                modified_at: '2024-11-28T10:15:00',
                chunks_count: 52,
                embedding_status: 'completed'
            },
            {
                id: '5',
                filename: 'Guia_Tecnica_RAG.txt',
                type: 'txt',
                size: 524288,
                category: 'technical',
                status: 'processing',
                owner: 'Luciano Araneda',
                department: 'Tecnología',
                version: '1.0',
                tags: ['rag', 'ia', 'embeddings'],
                description: 'Guía técnica para implementación de sistemas RAG',
                public: false,
                indexable: true,
                created_at: '2024-12-14T07:30:00',
                modified_at: '2024-12-14T07:30:00',
                chunks_count: 12,
                embedding_status: 'processing'
            }
        ];
    }

    renderDocuments() {
        const filteredDocs = this.filterDocuments();
        
        if (filteredDocs.length === 0) {
            this.elements.documentsContainer.style.display = 'none';
            this.elements.emptyState.style.display = 'flex';
            return;
        }
        
        this.elements.documentsContainer.style.display = this.currentView === 'grid' ? 'grid' : 'flex';
        this.elements.emptyState.style.display = 'none';
        
        this.elements.documentsContainer.innerHTML = filteredDocs.map(doc => 
            this.createDocumentCard(doc)
        ).join('');
        
        // Attach action listeners
        this.attachDocumentActions();
    }

    createDocumentCard(doc) {
        const iconClass = `doc-icon-${doc.type}`;
        const statusClass = `status-${doc.status}`;
        const formattedSize = this.formatFileSize(doc.size);
        const formattedDate = this.formatDate(doc.modified_at);
        
        const documentId = doc.document_id || doc.id;

        return `
            <div class="document-card" data-id="${documentId}">
                <div class="document-icon ${iconClass}">
                    ${this.getFileIcon(doc.type)}
                </div>
                
                ${this.currentView === 'list' ? '<div class="document-info">' : ''}
                
                <div class="document-title" title="${doc.filename}">${doc.filename}</div>
                
                <div class="document-meta">
                    <div class="meta-item">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                            <circle cx="12" cy="7" r="4"></circle>
                        </svg>
                        ${doc.owner}
                    </div>
                    <div class="meta-item">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        ${formattedDate}
                    </div>
                    <div class="meta-item">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
                        </svg>
                        ${formattedSize}
                    </div>
                </div>
                
                <div class="document-tags">
                    <span class="tag tag-category">${doc.category}</span>
                    ${doc.tags.slice(0, 2).map(tag => `<span class="tag">${tag}</span>`).join('')}
                    ${doc.tags.length > 2 ? `<span class="tag">+${doc.tags.length - 2}</span>` : ''}
                </div>
                
                <span class="document-status ${statusClass}">
                    ${this.getStatusIcon(doc.status)}
                    ${this.getStatusLabel(doc.status)}
                </span>
                
                ${this.currentView === 'list' ? '</div>' : ''}
                
                <div class="document-actions">
                    <button class="doc-action-btn edit-btn" data-id="${documentId}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                        </svg>
                        Editar
                    </button>
                    <button class="doc-action-btn download-btn" data-id="${documentId}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                            <polyline points="7 10 12 15 17 10"></polyline>
                            <line x1="12" y1="15" x2="12" y2="3"></line>
                        </svg>
                        Descargar
                    </button>
                    <button class="doc-action-btn danger delete-btn" data-id="${documentId}">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        Eliminar
                    </button>
                </div>
            </div>
        `;
    }

    attachDocumentActions() {
        // Edit buttons
        document.querySelectorAll('.edit-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const docId = btn.dataset.id;
                this.editDocument(docId);
            });
        });
        
        // Download buttons
        document.querySelectorAll('.download-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const docId = btn.dataset.id;
                this.downloadDocument(docId);
            });
        });
        
        // Delete buttons
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const docId = btn.dataset.id;
                this.deleteDocument(docId);
            });
        });
    }

    filterDocuments() {
        const searchTerm = this.elements.searchInput.value.toLowerCase();
        const category = this.elements.categoryFilter.value;
        const type = this.elements.typeFilter.value;
        const status = this.elements.statusFilter.value;
        
        return this.documents.filter(doc => {
            const matchesSearch = !searchTerm || 
                (doc.filename && doc.filename.toLowerCase().includes(searchTerm)) ||
                (doc.description && doc.description.toLowerCase().includes(searchTerm)) ||
                (Array.isArray(doc.tags) && doc.tags.some(tag => tag.toLowerCase().includes(searchTerm)));
            
            const matchesCategory = !category || doc.category === category;
            const matchesType = !type || doc.type === type;
            const matchesStatus = !status || doc.status === status;
            
            return matchesSearch && matchesCategory && matchesType && matchesStatus;
        });
    }

    toggleView(view) {
        this.currentView = view;
        
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        document.querySelector(`[data-view="${view}"]`).classList.add('active');
        
        this.elements.documentsContainer.className = `documents-container ${view}-view`;
        this.renderDocuments();
    }

    // Upload Modal
    openUploadModal() {
        this.selectedFiles = [];
        this.elements.uploadFilesList.innerHTML = '';
        this.elements.metadataForm.style.display = 'none';
        this.elements.startUpload.disabled = true;
        this.elements.fileInput.value = '';
        this.elements.uploadModal.classList.add('active');
    }

    closeUploadModal() {
        this.elements.uploadModal.classList.remove('active');
        this.selectedFiles = [];
        this.elements.fileInput.value = '';
    }

    handleFileSelection(e) {
        const files = Array.from(e.target.files);
        
        files.forEach(file => {
            if (this.isValidFile(file)) {
                this.selectedFiles.push(file);
            }
        });
        
        this.renderUploadFilesList();
        
        if (this.selectedFiles.length > 0) {
            this.elements.metadataForm.style.display = 'block';
            this.elements.startUpload.disabled = false;
        }
    }

    isValidFile(file) {
        const validTypes = [
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'text/plain'
        ];
        
        const maxSize = 50 * 1024 * 1024; // 50 MB
        
        if (!validTypes.includes(file.type)) {
            alert(`Tipo de archivo no válido: ${file.name}`);
            return false;
        }
        
        if (file.size > maxSize) {
            alert(`Archivo demasiado grande: ${file.name}`);
            return false;
        }
        
        return true;
    }

    renderUploadFilesList() {
        this.elements.uploadFilesList.innerHTML = this.selectedFiles.map((file, index) => `
            <div class="upload-file-item">
                <div class="upload-file-icon ${this.getIconClass(file)}">
                    ${this.getFileIconByMime(file.type)}
                </div>
                <div class="upload-file-info">
                    <div class="upload-file-name">${file.name}</div>
                    <div class="upload-file-size">${this.formatFileSize(file.size)}</div>
                </div>
                <button class="upload-file-remove" data-index="${index}">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
        `).join('');
        
        // Attach remove listeners
        document.querySelectorAll('.upload-file-remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const index = parseInt(btn.dataset.index);
                this.selectedFiles.splice(index, 1);
                this.renderUploadFilesList();
                
                if (this.selectedFiles.length === 0) {
                    this.elements.metadataForm.style.display = 'none';
                    this.elements.startUpload.disabled = true;
                }
            });
        });
    }

    async uploadDocuments() {
        const metadata = {
            category: document.getElementById('docCategory').value,
            owner: document.getElementById('docOwner').value,
            version: document.getElementById('docVersion').value || '1.0',
            department: document.getElementById('docDepartment').value,
            tags: document.getElementById('docTags').value.split(',').map(t => t.trim()).filter(t => t),
            description: document.getElementById('docDescription').value,
            public: document.getElementById('docPublic').checked,
            indexable: document.getElementById('docIndexable').checked
        };
        
        if (!metadata.category || !metadata.owner) {
            alert('Por favor completa los campos obligatorios');
            return;
        }
        
        this.elements.startUpload.disabled = true;
        this.elements.startUpload.textContent = 'Subiendo...';
        
        try {
            for (const file of this.selectedFiles) {
                const formData = new FormData();
                formData.append('file', file);
                Object.keys(metadata).forEach(key => {
                    formData.append(key, metadata[key]);
                });
                
                const response = await fetch(`${API_BASE_URL}/documents/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    throw new Error(`Error subiendo ${file.name}`);
                }
            }
            
            alert('Documentos subidos exitosamente');
            this.closeUploadModal();
            this.loadDocuments();
            
        } catch (error) {
            console.error('Error uploading documents:', error);
            alert('Error al subir documentos. Por favor intenta nuevamente.');
        } finally {
            this.elements.startUpload.disabled = false;
            this.elements.startUpload.textContent = 'Subir Documentos';
        }
    }

    // Edit Document
    editDocument(docId) {
        const doc = this.documents.find(d => (d.document_id || d.id) === docId);
        if (!doc) return;
        
        this.currentDocument = doc;
        
        // Fill form
        document.getElementById('editFileName').value = doc.filename;
        document.getElementById('editFileType').value = doc.type.toUpperCase();
        document.getElementById('editCategory').value = doc.category;
        document.getElementById('editStatus').value = doc.status;
        document.getElementById('editOwner').value = doc.owner;
        document.getElementById('editDepartment').value = doc.department || '';
        document.getElementById('editVersion').value = doc.version || '';
        document.getElementById('editSize').value = this.formatFileSize(doc.size);
        document.getElementById('editTags').value = doc.tags.join(', ');
        document.getElementById('editDescription').value = doc.description || '';
        document.getElementById('editCreated').value = this.formatDate(doc.created_at);
        document.getElementById('editModified').value = this.formatDate(doc.modified_at);
        document.getElementById('editPublic').checked = doc.public;
        document.getElementById('editIndexable').checked = doc.indexable;
        
        // Preview
        const iconClass = `doc-icon-${doc.type}`;
        document.getElementById('editDocPreview').innerHTML = `
            <div class="preview-icon ${iconClass}">
                ${this.getFileIcon(doc.type)}
            </div>
            <div class="preview-info">
                <h3>${doc.filename}</h3>
                <p>${doc.chunks_count} chunks | ${this.getStatusLabel(doc.embedding_status)}</p>
            </div>
        `;
        
        this.elements.editModal.classList.add('active');
    }

    closeEditModal() {
        this.elements.editModal.classList.remove('active');
        this.currentDocument = null;
    }

    async saveMetadata() {
        if (!this.currentDocument) return;
        
        const updatedMetadata = {
            category: document.getElementById('editCategory').value,
            status: document.getElementById('editStatus').value,
            owner: document.getElementById('editOwner').value,
            department: document.getElementById('editDepartment').value,
            version: document.getElementById('editVersion').value,
            tags: document.getElementById('editTags').value.split(',').map(t => t.trim()).filter(t => t),
            description: document.getElementById('editDescription').value,
            public: document.getElementById('editPublic').checked,
            indexable: document.getElementById('editIndexable').checked
        };
        
        try {
            const documentId = this.currentDocument.document_id || this.currentDocument.id;
            const response = await fetch(
                `${API_BASE_URL}/documents/${encodeURIComponent(documentId)}`,
                {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedMetadata)
                }
            );
            
            if (response.ok) {
                alert('Metadatos actualizados exitosamente');
                this.closeEditModal();
                this.loadDocuments();
            } else {
                throw new Error('Error actualizando metadatos');
            }
        } catch (error) {
            console.error('Error saving metadata:', error);
            alert('Error al guardar metadatos. Los cambios se aplicarán localmente.');
            
            // Update local copy
            Object.assign(this.currentDocument, updatedMetadata);
            this.currentDocument.modified_at = new Date().toISOString();
            this.closeEditModal();
            this.renderDocuments();
        }
    }

    async downloadDocument(docId) {
        const doc = this.documents.find(d => (d.document_id || d.id) === docId);
        if (!doc) return;
        
        try {
            const response = await fetch(
                `${API_BASE_URL}/documents/${encodeURIComponent(docId)}/download`
            );
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = doc.filename;
                a.click();
                window.URL.revokeObjectURL(url);
            }
        } catch (error) {
            console.error('Error downloading document:', error);
            alert('Error al descargar documento');
        }
    }

    async deleteDocument(docId) {
        const doc = this.documents.find(d => (d.document_id || d.id) === docId);
        if (!doc) return;
        
        if (!confirm(`¿Estás seguro de eliminar "${doc.filename}"?\n\nEsta acción no se puede deshacer y eliminará el documento de la base vectorial.`)) {
            return;
        }
        
        try {
            const response = await fetch(
                `${API_BASE_URL}/documents/${encodeURIComponent(docId)}`,
                {
                method: 'DELETE'
                }
            );
            
            if (response.ok) {
                alert('Documento eliminado exitosamente');
                this.loadDocuments();
            } else {
                const message = await response.text();
                throw new Error(message || 'Error eliminando documento');
            }
        } catch (error) {
            console.error('Error deleting document:', error);
            // Simulate deletion locally
            this.documents = this.documents.filter(d => d.id !== docId);
            this.renderDocuments();
            this.updateStats();
        }
    }

    updateStats() {
        const totalDocs = this.documents.length;
        const totalBytes = this.documents.reduce((sum, doc) => sum + doc.size, 0);
        const totalMB = (totalBytes / (1024 * 1024)).toFixed(1);
        
        this.elements.totalDocs.textContent = totalDocs;
        this.elements.totalSize.textContent = `${totalMB} MB`;
    }

    // Helper functions
    getFileIcon(type) {
        const icons = {
            pdf: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>',
            docx: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="12" y1="9" x2="8" y2="9"></line></svg>',
            pptx: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><rect x="8" y="12" width="8" height="6"></rect></svg>',
            txt: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>'
        };
        return icons[type] || icons.txt;
    }

    getFileIconByMime(mimeType) {
        if (mimeType.includes('pdf')) return this.getFileIcon('pdf');
        if (mimeType.includes('word')) return this.getFileIcon('docx');
        if (mimeType.includes('presentation')) return this.getFileIcon('pptx');
        return this.getFileIcon('txt');
    }

    getIconClass(file) {
        if (file.type.includes('pdf')) return 'doc-icon-pdf';
        if (file.type.includes('word')) return 'doc-icon-docx';
        if (file.type.includes('presentation')) return 'doc-icon-pptx';
        return 'doc-icon-txt';
    }

    getStatusIcon(status) {
        const icons = {
            active: '●',
            processing: '⟳',
            completed: '✔',
            error: '✕',
            archived: '📦'
        };
    return icons[status] || '●';
}


    getStatusLabel(status) {
        const labels = {
            active: 'Activo',
            processing: 'Procesando',
            error: 'Error',
            archived: 'Archivado',
            completed: 'Indexado',
            not_indexed: 'No indexado'
        };
        return labels[status] || status;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (days === 0) return 'Hoy';
        if (days === 1) return 'Ayer';
        if (days < 7) return `Hace ${days} días`;
        
        return date.toLocaleDateString('es-CL', { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.documentManager = new DocumentManager();
    console.log('Document Manager initialized');
});

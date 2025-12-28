// Configuration
const CONFIG = {
    API_BASE_URL: 'http://65.108.150.100:8000/api',
    AGENTS: {
        general: { name: 'General Assistant', model: 'gpt-4', systemPrompt: 'Eres un asistente general útil.' },
        hr: { name: 'HR Specialist', model: 'gpt-4', systemPrompt: 'Eres un experto en recursos humanos y legislación laboral chilena.' },
        legal: { name: 'Legal Compliance', model: 'gpt-4', systemPrompt: 'Eres un experto en cumplimiento legal y normativas.' },
        technical: { name: 'Technical Support', model: 'gpt-4', systemPrompt: 'Eres un experto técnico en soporte y desarrollo.' },
        training: { name: 'Training Expert', model: 'gpt-4', systemPrompt: 'Eres un experto en capacitación y desarrollo profesional.' }
    }
};

const USE_MOCK_RAG = false; // desdeactiva funcion mockquery


// State Management
class ChatApp {
    constructor() {
        this.currentChatId = null;
        this.currentAgent = 'general';
        this.chats = this.loadChats();
        this.currentMessages = [];
        
        this.initializeElements();
        this.attachEventListeners();
        this.updateChatHistory();
    }

    initializeElements() {
        this.elements = {
            sidebar: document.getElementById('sidebar'),
            newChatBtn: document.getElementById('newChatBtn'),
            chatHistory: document.getElementById('chatHistory'),
            agentSelector: document.getElementById('agentSelector'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            attachBtn: document.getElementById('attachBtn'),
            messagesContainer: document.getElementById('messagesContainer'),
            welcomeScreen: document.getElementById('welcomeScreen'),
            ragStatus: document.getElementById('ragStatus'),
            docCount: document.getElementById('docCount')
        };
    }

    attachEventListeners() {
        // New chat button
        this.elements.newChatBtn.addEventListener('click', () => this.createNewChat());

        // Agent selector
        this.elements.agentSelector.addEventListener('change', (e) => {
            this.currentAgent = e.target.value;
            this.updateRagStatus();
        });

        // Message input
        this.elements.messageInput.addEventListener('input', (e) => {
            this.autoResizeTextarea(e.target);
        });

        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Send button
        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());

        // Attach button
        this.elements.attachBtn.addEventListener('click', () => this.handleAttachment());

        // Example prompts
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const prompt = e.target.getAttribute('data-prompt');
                this.elements.messageInput.value = prompt;
                this.sendMessage();
            });
        });
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
    }

    createNewChat() {
        this.currentChatId = this.generateChatId();
        this.currentMessages = [];
        
        this.chats.unshift({
            id: this.currentChatId,
            title: 'Nueva conversación',
            timestamp: Date.now(),
            agent: this.currentAgent
        });
        
        this.saveChats();
        this.updateChatHistory();
        this.showWelcomeScreen();
        this.elements.messageInput.focus();
    }

    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message) return;

        // Create chat if doesn't exist
        if (!this.currentChatId) {
            this.createNewChat();
        }

        // Clear input
        this.elements.messageInput.value = '';
        this.autoResizeTextarea(this.elements.messageInput);

        // Hide welcome screen and show messages
        this.elements.welcomeScreen.style.display = 'none';
        this.elements.messagesContainer.classList.add('active');

        // Add user message
        const userMessage = {
            role: 'user',
            content: message,
            timestamp: Date.now()
        };
        this.currentMessages.push(userMessage);
        this.renderMessage(userMessage);

        // Update chat title if it's the first message
        if (this.currentMessages.length === 1) {
            this.updateChatTitle(message);
        }

        // Show loading indicator
        this.showLoadingIndicator();

        try {
            // Call RAG API
            const response = await this.queryRAG(message);
            
            // Remove loading indicator
            this.removeLoadingIndicator();

            // Add assistant message
            const assistantMessage = {
                role: 'assistant',
                content: response.answer,
                sources: response.sources,
                timestamp: Date.now(),
                agent: 'rag' // ← fuerza que NO sea un agente humano/especialista
            };

            this.currentMessages.push(assistantMessage);
            this.renderMessage(assistantMessage);

            // Save chat
            this.saveCurrentChat();
            
        } catch (error) {
            console.error('Error querying RAG:', error);
            this.removeLoadingIndicator();
            
            const errorMessage = {
                role: 'assistant',
                content: 'Lo siento, ha ocurrido un error al procesar tu consulta. Por favor, intenta nuevamente.',
                timestamp: Date.now(),
                isError: true
            };
            this.currentMessages.push(errorMessage);
            this.renderMessage(errorMessage);
        }

        // Scroll to bottom
        this.scrollToBottom();
    }

    async queryRAG(query) {

        if (USE_MOCK_RAG) {
            console.warn('⚠️ Usando mockRAGQuery (solo desarrollo)');
            return await this.mockRAGQuery(query);
        }

        const response = await fetch(`${CONFIG.API_BASE_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: query,
                top_k: 5
            })
        });

        if (!response.ok) {
            throw new Error('Error consultando backend RAG');
        }

        return await response.json();
    }


    /* 
    async mockRAGQuery(query) {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Mock responses based on agent
        const agentResponses = {
            general: {
                answer: `He analizado tu consulta "${query}" en la base de conocimiento. Basándome en los documentos indexados, puedo proporcionarte la siguiente información:\n\nLa documentación muestra varios puntos relevantes sobre este tema. Los sistemas RAG (Retrieval-Augmented Generation) permiten combinar la búsqueda semántica con la generación de respuestas, lo que mejora significativamente la precisión y relevancia de las respuestas.\n\n¿Hay algún aspecto específico sobre el que quieras más detalles?`,
                sources: [
                    { title: 'Introducción a sistemas RAG', chunk: 'Documento general', score: 0.92 },
                    { title: 'Best practices RAG', chunk: 'Capítulo 3', score: 0.87 }
                ]
            },
            hr: {
                answer: `Según la documentación de Recursos Humanos y la legislación laboral chilena:\n\nLa Ley Karin (Ley 21.643) establece requisitos específicos para la prevención, investigación y sanción del acoso laboral, sexual y violencia en el trabajo. Las empresas deben implementar protocolos de prevención y contar con canales de denuncia confidenciales.\n\nLos puntos clave incluyen:\n- Capacitación obligatoria para todo el personal\n- Implementación de protocolos de actuación\n- Canales de denuncia seguros\n- Medidas preventivas y correctivas\n\n¿Necesitas información más específica sobre alguno de estos aspectos?`,
                sources: [
                    { title: 'Ley Karin - Normativa completa', chunk: 'Artículo 2, Sección 3', score: 0.95 },
                    { title: 'Protocolo de prevención de acoso', chunk: 'Procedimientos', score: 0.89 },
                    { title: 'Capacitación Ley Karin', chunk: 'Módulo 1', score: 0.84 }
                ]
            },
            legal: {
                answer: `En base a la documentación legal disponible:\n\nEl marco normativo chileno establece requisitos claros de cumplimiento. Las organizaciones deben mantener registros actualizados y procedimientos documentados que demuestren el cumplimiento de las normativas aplicables.\n\nLos aspectos principales incluyen:\n- Documentación de procesos\n- Auditorías periódicas\n- Capacitación del personal\n- Actualización normativa continua\n\n¿Requieres información sobre alguna normativa específica?`,
                sources: [
                    { title: 'Marco legal empresarial Chile', chunk: 'Capítulo 5', score: 0.91 },
                    { title: 'Compliance y auditoría', chunk: 'Sección 2', score: 0.86 }
                ]
            },
            technical: {
                answer: `Revisando la documentación técnica disponible:\n\nLos sistemas RAG modernos utilizan modelos de embeddings avanzados para convertir documentos en representaciones vectoriales que pueden buscarse semánticamente. Esto permite encontrar información relevante incluso cuando no hay coincidencia exacta de palabras clave.\n\nLa arquitectura típica incluye:\n- Base de datos vectorial (Pinecone, Weaviate, ChromaDB)\n- Modelo de embeddings (OpenAI, Cohere, local)\n- LLM para generación de respuestas\n- Sistema de ranking y reranking\n\n¿Necesitas detalles sobre algún componente específico?`,
                sources: [
                    { title: 'Arquitectura RAG', chunk: 'Diseño de sistema', score: 0.94 },
                    { title: 'Bases de datos vectoriales', chunk: 'Comparativa', score: 0.88 }
                ]
            },
            training: {
                answer: `Según los materiales de capacitación disponibles:\n\nLos programas de formación efectivos deben incluir objetivos claros, contenido estructurado y evaluaciones que permitan medir el aprendizaje. La modalidad e-learning con plataformas como Moodle facilita el seguimiento y certificación.\n\nElementos clave de un buen programa:\n- Objetivos de aprendizaje medibles\n- Contenido multimedia e interactivo\n- Evaluaciones formativas y sumativas\n- Certificación y seguimiento\n- Integración con SENCE cuando aplique\n\n¿Te gustaría explorar algún aspecto específico de diseño instruccional?`,
                sources: [
                    { title: 'Diseño instruccional avanzado', chunk: 'Capítulo 4', score: 0.93 },
                    { title: 'Evaluación de aprendizaje', chunk: 'Métodos', score: 0.87 },
                    { title: 'Plataformas LMS', chunk: 'Moodle', score: 0.82 }
                ]
            }
        };

        return agentResponses[this.currentAgent] || agentResponses.general;
    }
    */

    renderMessage(message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${message.role}`;
        
        const avatar = message.role === 'user' ? 'TÚ' : 'AI';
        const roleName =
            message.role === 'user'
                ? 'Tú'
                : message.agent === 'rag'
                    ? 'Apex AI (RAG)'
                    : CONFIG.AGENTS[message.agent]?.name || 'Asistente';
        let messageHTML = `
            <div class="message-header">
                <div class="message-avatar">${avatar}</div>
                <div class="message-role">${roleName}</div>
            </div>
            <div class="message-content">${this.formatMessageContent(message.content)}</div>
        `;

        if (message.sources && message.sources.length > 0) {
        messageHTML += `
            <div class="rag-sources">
            <div class="rag-sources-title">📚 Fuentes consultadas</div>
            ${message.sources.map(s => `
                <div class="source-item">
                <span><strong>${s.filename}</strong></span>
                <span>Chunk ${s.chunk_index}</span>
                <span>Score ${(s.score * 100).toFixed(1)}%</span>
                </div>
            `).join('')}
            </div>
        `;
        }

        messageDiv.innerHTML = messageHTML;
        this.elements.messagesContainer.appendChild(messageDiv);
    }

    formatMessageContent(content) {
        // Simple markdown-like formatting
        return content
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>');
    }

    showLoadingIndicator() {
        const loadingDiv = document.createElement('div');
        loadingDiv.className = 'message assistant loading';
        loadingDiv.innerHTML = `
            <div class="message-header">
                <div class="message-avatar">AI</div>
                <div class="message-role">${CONFIG.AGENTS[this.currentAgent].name}</div>
            </div>
            <div class="message-content">
                <div class="loading-indicator">
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                    <div class="loading-dot"></div>
                </div>
            </div>
        `;
        this.elements.messagesContainer.appendChild(loadingDiv);
    }

    removeLoadingIndicator() {
        const loading = this.elements.messagesContainer.querySelector('.message.loading');
        if (loading) {
            loading.remove();
        }
    }

    scrollToBottom() {
        const container = document.getElementById('chatContainer');
        container.scrollTop = container.scrollHeight;
    }

    showWelcomeScreen() {
        this.elements.welcomeScreen.style.display = 'flex';
        this.elements.messagesContainer.classList.remove('active');
        this.elements.messagesContainer.innerHTML = '';
    }

    updateChatTitle(firstMessage) {
        const title = firstMessage.length > 50 
            ? firstMessage.substring(0, 50) + '...' 
            : firstMessage;
        
        const chat = this.chats.find(c => c.id === this.currentChatId);
        if (chat) {
            chat.title = title;
            this.saveChats();
            this.updateChatHistory();
        }
    }

    updateChatHistory() {
        this.elements.chatHistory.innerHTML = '';
        
        this.chats.forEach(chat => {
            const item = document.createElement('div');
            item.className = 'chat-history-item';
            if (chat.id === this.currentChatId) {
                item.classList.add('active');
            }
            
            item.innerHTML = `
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                </svg>
                <div class="chat-title">${chat.title}</div>
            `;
            
            item.addEventListener('click', () => this.loadChat(chat.id));
            this.elements.chatHistory.appendChild(item);
        });
    }

    loadChat(chatId) {
        // In a real app, load messages from storage/API
        this.currentChatId = chatId;
        this.updateChatHistory();
        // For now, just show welcome screen
        this.showWelcomeScreen();
    }

    saveCurrentChat() {
        const chat = this.chats.find(c => c.id === this.currentChatId);
        if (chat) {
            chat.lastMessage = this.currentMessages[this.currentMessages.length - 1];
            chat.timestamp = Date.now();
            this.saveChats();
        }
    }

    saveChats() {
        localStorage.setItem('apex_ai_chats', JSON.stringify(this.chats));
    }

    loadChats() {
        const stored = localStorage.getItem('apex_ai_chats');
        return stored ? JSON.parse(stored) : [];
    }

    generateChatId() {
        return 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    handleAttachment() {
        alert('Función de adjuntar documentos en desarrollo.\n\nEn la versión completa, aquí podrás:\n- Subir PDFs, DOCX, TXT\n- Los documentos se procesarán y agregarán a la base vectorial\n- El sistema podrá consultar esos documentos en futuras conversaciones');
    }

    updateRagStatus() {
        const agent = CONFIG.AGENTS[this.currentAgent];
        this.elements.docCount.querySelector('span').textContent = 
            `Agente: ${agent.name} - 1,247 documentos indexados`;
    }
}

// Initialize app when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
    console.log('Apex AI Assistant initialized');
    console.log('Ready to connect to RAG backend at:', CONFIG.API_BASE_URL);
});

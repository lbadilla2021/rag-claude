import { CONFIG } from '../config/constants.js';

export function renderMessage({ message, elements }) {
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
        <div class="message-content">${formatMessageContent(message.content)}</div>
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
    elements.messagesContainer.appendChild(messageDiv);
}

export function formatMessageContent(content) {
    return content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');
}

export function showLoadingIndicator({ elements, currentAgent }) {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message assistant loading';
    loadingDiv.innerHTML = `
        <div class="message-header">
            <div class="message-avatar">AI</div>
            <div class="message-role">${CONFIG.AGENTS[currentAgent].name}</div>
        </div>
        <div class="message-content">
            <div class="loading-indicator">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        </div>
    `;
    elements.messagesContainer.appendChild(loadingDiv);
}

export function removeLoadingIndicator(elements) {
    const loading = elements.messagesContainer.querySelector('.message.loading');
    if (loading) {
        loading.remove();
    }
}

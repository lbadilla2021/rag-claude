import { CONFIG } from '../config/constants.js';
import { queryRAG } from '../services/ragService.js';
import { loadChats, saveChats } from '../storage/chatStorage.js';
import { autoResizeTextarea, scrollToBottom } from '../utils/dom.js';
import { renderMessage, showLoadingIndicator, removeLoadingIndicator } from '../ui/messages.js';

export class ChatApp {
    constructor() {
        this.currentChatId = null;
        this.currentAgent = 'general';
        this.chats = loadChats();
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
        this.elements.newChatBtn.addEventListener('click', () => this.createNewChat());

        this.elements.agentSelector.addEventListener('change', (e) => {
            this.currentAgent = e.target.value;
            this.updateRagStatus();
        });

        this.elements.messageInput.addEventListener('input', (e) => {
            autoResizeTextarea(e.target);
        });

        this.elements.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        this.elements.attachBtn.addEventListener('click', () => this.handleAttachment());

        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const prompt = e.target.getAttribute('data-prompt');
                this.elements.messageInput.value = prompt;
                this.sendMessage();
            });
        });
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

        saveChats(this.chats);
        this.updateChatHistory();
        this.showWelcomeScreen();
        this.elements.messageInput.focus();
    }

    async sendMessage() {
        const message = this.elements.messageInput.value.trim();
        if (!message) return;

        if (!this.currentChatId) {
            this.createNewChat();
        }

        this.elements.messageInput.value = '';
        autoResizeTextarea(this.elements.messageInput);

        this.elements.welcomeScreen.style.display = 'none';
        this.elements.messagesContainer.classList.add('active');

        const userMessage = {
            role: 'user',
            content: message,
            timestamp: Date.now()
        };
        this.currentMessages.push(userMessage);
        renderMessage({ message: userMessage, elements: this.elements });

        if (this.currentMessages.length === 1) {
            this.updateChatTitle(message);
        }

        showLoadingIndicator({ elements: this.elements, currentAgent: this.currentAgent });

        try {
            const response = await queryRAG({ query: message, agentKey: this.currentAgent });

            removeLoadingIndicator(this.elements);

            const assistantMessage = {
                role: 'assistant',
                content: response.answer,
                sources: response.sources,
                timestamp: Date.now(),
                agent: 'rag'
            };

            this.currentMessages.push(assistantMessage);
            renderMessage({ message: assistantMessage, elements: this.elements });

            this.saveCurrentChat();
        } catch (error) {
            console.error('Error querying RAG:', error);
            removeLoadingIndicator(this.elements);

            const errorMessage = {
                role: 'assistant',
                content: 'Lo siento, ha ocurrido un error al procesar tu consulta. Por favor, intenta nuevamente.',
                timestamp: Date.now(),
                isError: true
            };
            this.currentMessages.push(errorMessage);
            renderMessage({ message: errorMessage, elements: this.elements });
        }

        this.scrollToBottom();
    }

    scrollToBottom() {
        const container = document.getElementById('chatContainer');
        scrollToBottom(container);
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
            saveChats(this.chats);
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
        this.currentChatId = chatId;
        this.updateChatHistory();
        this.showWelcomeScreen();
    }

    saveCurrentChat() {
        const chat = this.chats.find(c => c.id === this.currentChatId);
        if (chat) {
            chat.lastMessage = this.currentMessages[this.currentMessages.length - 1];
            chat.timestamp = Date.now();
            saveChats(this.chats);
        }
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

import { ChatApp } from './app/chatApp.js';
import { CONFIG } from './config/constants.js';

document.addEventListener('DOMContentLoaded', () => {
    window.chatApp = new ChatApp();
    console.log('Apex AI Assistant initialized');
    console.log('Ready to connect to RAG backend at:', CONFIG.API_BASE_URL);
});

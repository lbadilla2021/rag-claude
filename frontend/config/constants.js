export const CONFIG = {
    API_BASE_URL: 'http://65.108.150.100:8000/api',
    AGENTS: {
        general: {
            name: 'General Assistant',
            model: 'gpt-4',
            systemPrompt: 'Eres un asistente general útil.'
        },
        hr: {
            name: 'HR Specialist',
            model: 'gpt-4',
            systemPrompt: 'Eres un experto en recursos humanos y legislación laboral chilena.'
        },
        legal: {
            name: 'Legal Compliance',
            model: 'gpt-4',
            systemPrompt: 'Eres un experto en cumplimiento legal y normativas.'
        },
        technical: {
            name: 'Technical Support',
            model: 'gpt-4',
            systemPrompt: 'Eres un experto técnico en soporte y desarrollo.'
        },
        training: {
            name: 'Training Expert',
            model: 'gpt-4',
            systemPrompt: 'Eres un experto en capacitación y desarrollo profesional.'
        }
    }
};

export const USE_MOCK_RAG = false; // desactiva funcion mockquery

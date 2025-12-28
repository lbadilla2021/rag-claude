import { CONFIG, USE_MOCK_RAG } from '../config/constants.js';

export async function queryRAG({ query, agentKey }) {
    if (USE_MOCK_RAG) {
        console.warn('⚠️ Usando mockRAGQuery (solo desarrollo)');
        return mockRAGQuery(query, agentKey);
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

async function mockRAGQuery(query, agentKey) {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 1500));

    const agentResponses = {
        general: {
            answer: `He analizado tu consulta "${query}" en la base de conocimiento. Basándome en los documentos indexados, puedo proporcionarte la siguiente información:\n\nLa documentación muestra varios puntos relevantes sobre este tema. Los sistemas RAG (Retrieval-Augmented Generation) permiten combinar la búsqueda semántica con la generación de respuestas, lo que mejora significativamente la precisión y relevancia de las respuestas.\n\n¿Hay algún aspecto específico sobre el que quieras más detalles?`,
            sources: [
                { filename: 'Introducción a sistemas RAG', chunk_index: 1, score: 0.92 },
                { filename: 'Best practices RAG', chunk_index: 3, score: 0.87 }
            ]
        },
        hr: {
            answer: `Según la documentación de Recursos Humanos y la legislación laboral chilena:\n\nLa Ley Karin (Ley 21.643) establece requisitos específicos para la prevención, investigación y sanción del acoso laboral, sexual y violencia en el trabajo. Las empresas deben implementar protocolos de prevención y contar con canales de denuncia confidenciales.\n\nLos puntos clave incluyen:\n- Capacitación obligatoria para todo el personal\n- Implementación de protocolos de actuación\n- Canales de denuncia seguros\n- Medidas preventivas y correctivas\n\n¿Necesitas información más específica sobre alguno de estos aspectos?`,
            sources: [
                { filename: 'Ley Karin - Normativa completa', chunk_index: 2, score: 0.95 },
                { filename: 'Protocolo de prevención de acoso', chunk_index: 1, score: 0.89 },
                { filename: 'Capacitación Ley Karin', chunk_index: 4, score: 0.84 }
            ]
        },
        legal: {
            answer: `En base a la documentación legal disponible:\n\nEl marco normativo chileno establece requisitos claros de cumplimiento. Las organizaciones deben mantener registros actualizados y procedimientos documentados que demuestren el cumplimiento de las normativas aplicables.\n\nLos aspectos principales incluyen:\n- Documentación de procesos\n- Auditorías periódicas\n- Capacitación del personal\n- Actualización normativa continua\n\n¿Requieres información sobre alguna normativa específica?`,
            sources: [
                { filename: 'Marco legal empresarial Chile', chunk_index: 5, score: 0.91 },
                { filename: 'Compliance y auditoría', chunk_index: 2, score: 0.86 }
            ]
        },
        technical: {
            answer: `Revisando la documentación técnica disponible:\n\nLos sistemas RAG modernos utilizan modelos de embeddings avanzados para convertir documentos en representaciones vectoriales que pueden buscarse semánticamente. Esto permite encontrar información relevante incluso cuando no hay coincidencia exacta de palabras clave.\n\nLa arquitectura típica incluye:\n- Base de datos vectorial (Pinecone, Weaviate, ChromaDB)\n- Modelo de embeddings (OpenAI, Cohere, local)\n- LLM para generación de respuestas\n- Sistema de ranking y reranking\n\n¿Necesitas detalles sobre algún componente específico?`,
            sources: [
                { filename: 'Arquitectura RAG', chunk_index: 1, score: 0.94 },
                { filename: 'Bases de datos vectoriales', chunk_index: 2, score: 0.88 }
            ]
        },
        training: {
            answer: `Según los materiales de capacitación disponibles:\n\nLos programas de formación efectivos deben incluir objetivos claros, contenido estructurado y evaluaciones que permitan medir el aprendizaje. La modalidad e-learning con plataformas como Moodle facilita el seguimiento y certificación.\n\nElementos clave de un buen programa:\n- Objetivos de aprendizaje medibles\n- Contenido multimedia e interactivo\n- Evaluaciones formativas y sumativas\n- Certificación y seguimiento\n- Integración con SENCE cuando aplique\n\n¿Te gustaría explorar algún aspecto específico de diseño instruccional?`,
            sources: [
                { filename: 'Diseño instruccional avanzado', chunk_index: 4, score: 0.93 },
                { filename: 'Evaluación de aprendizaje', chunk_index: 3, score: 0.87 },
                { filename: 'Plataformas LMS', chunk_index: 1, score: 0.82 }
            ]
        }
    };

    return agentResponses[agentKey] || agentResponses.general;
}

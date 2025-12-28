export function autoResizeTextarea(textarea, maxHeight = 200) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, maxHeight) + 'px';
}

export function scrollToBottom(container) {
    container.scrollTop = container.scrollHeight;
}

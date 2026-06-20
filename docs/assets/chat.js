/**
 * Tennis-Doctor — Chat Widget
 * ===========================
 * Vanilla JS chat widget that talks to /api/chat with Server-Sent Events.
 * Designed to work both:
 *   - Embedded inline on the homepage (welcome + suggestions)
 *   - As a full-page chat interface (/chat/)
 */

(function () {
    'use strict';

    // -----------------------------------------------------------------------
    // Configuration
    // -----------------------------------------------------------------------
    const CONFIG = {
        apiEndpoint: '/api/chat',
        suggestions: [
            'How do I improve my forehand topspin?',
            'What is the kinetic chain in tennis?',
            'How can I prevent knee pain during play?',
            'Explain the split step technique',
            "What's the 70% Rule in tennis tactics?",
            'How does Carlos Alcaraz generate power?',
        ],
        maxHistory: 20,
    };

    // -----------------------------------------------------------------------
    // State
    // -----------------------------------------------------------------------
    const state = {
        history: [],
        isStreaming: false,
        currentBotMessage: null,
        currentSources: [],
    };

    // -----------------------------------------------------------------------
    // DOM helpers
    // -----------------------------------------------------------------------
    function $(sel) { return document.querySelector(sel); }
    function $all(sel) { return Array.from(document.querySelectorAll(sel)); }

    function escapeHtml(s) {
        const div = document.createElement('div');
        div.textContent = s;
        return div.innerHTML;
    }

    // -----------------------------------------------------------------------
    // Markdown rendering (lightweight, no external deps)
    // -----------------------------------------------------------------------
    function renderMarkdown(text) {
        // Escape HTML first
        let html = escapeHtml(text);
        // Code blocks
        html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (m, lang, code) =>
            `<pre><code>${code}</code></pre>`);
        // Inline code
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Bold
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        // Italic
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        // Headings (h3, h4 only inside chat to keep compact)
        html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
        html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
        // Unordered lists
        html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>\n?)+/g, m => `<ul>${m}</ul>`);
        // Numbered lists
        html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
        // Paragraphs (double newline)
        html = html.split(/\n\n+/).map(p => {
            if (p.startsWith('<h') || p.startsWith('<ul') || p.startsWith('<ol') || p.startsWith('<pre') || p.startsWith('<li')) {
                return p;
            }
            return `<p>${p.replace(/\n/g, '<br>')}</p>`;
        }).join('\n');
        return html;
    }

    // -----------------------------------------------------------------------
    // Chat message rendering
    // -----------------------------------------------------------------------
    function addUserMessage(text) {
        const msg = document.createElement('div');
        msg.className = 'message user';
        msg.innerHTML = `
            <div class="message-avatar">👤</div>
            <div class="message-bubble">${escapeHtml(text)}</div>
        `;
        $('.chat-messages').appendChild(msg);
        scrollToBottom();
    }

    function addBotMessageSkeleton() {
        const msg = document.createElement('div');
        msg.className = 'message bot';
        msg.innerHTML = `
            <div class="message-avatar">🎾</div>
            <div class="message-bubble">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        $('.chat-messages').appendChild(msg);
        scrollToBottom();
        state.currentBotMessage = msg;
        return msg;
    }

    function appendTokenToBot(token) {
        if (!state.currentBotMessage) return;
        const bubble = state.currentBotMessage.querySelector('.message-bubble');
        // First token: replace typing indicator with empty content
        if (bubble.querySelector('.typing-indicator')) {
            bubble.innerHTML = '';
            const content = document.createElement('div');
            content.className = 'content';
            bubble.appendChild(content);
        }
        const content = bubble.querySelector('.content');
        content.textContent = (content.textContent || '') + token;
        scrollToBottom();
    }

    function appendSourcesToBot(sources) {
        if (!state.currentBotMessage || !sources || sources.length === 0) return;
        state.currentSources = sources;
        const bubble = state.currentBotMessage.querySelector('.message-bubble');
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'sources';
        const toggle = document.createElement('button');
        toggle.className = 'sources-toggle';
        toggle.textContent = `📚 ${sources.length} source${sources.length > 1 ? 's' : ''}`;
        const list = document.createElement('ul');
        list.className = 'sources-list';
        sources.forEach(s => {
            const li = document.createElement('li');
            li.innerHTML = `[${s.id}] <strong>${escapeHtml(s.title || 'Untitled')}</strong>
                <span style="color:var(--td-text-muted);font-size:0.9em">${escapeHtml(s.section || '')}</span>`;
            list.appendChild(li);
        });
        toggle.onclick = () => list.classList.toggle('open');
        sourcesDiv.appendChild(toggle);
        sourcesDiv.appendChild(list);
        bubble.appendChild(sourcesDiv);
    }

    function finalizeBotMessage(fullText) {
        if (!state.currentBotMessage) return;
        const bubble = state.currentBotMessage.querySelector('.message-bubble');
        const content = bubble.querySelector('.content');
        if (content) {
            content.innerHTML = renderMarkdown(content.textContent);
        }
        // Save to history (just the text, no HTML)
        state.history.push({ role: 'assistant', content: fullText });
        if (state.history.length > CONFIG.maxHistory) {
            state.history = state.history.slice(-CONFIG.maxHistory);
        }
        state.currentBotMessage = null;
        scrollToBottom();
    }

    function scrollToBottom() {
        const container = $('.chat-messages');
        if (container) {
            setTimeout(() => container.scrollTop = container.scrollHeight, 50);
        }
    }

    // -----------------------------------------------------------------------
    // Send question to API (streaming via SSE)
    // -----------------------------------------------------------------------
    async function sendQuestion(question) {
        if (!question.trim() || state.isStreaming) return;
        state.isStreaming = true;
        setInputEnabled(false);

        addUserMessage(question);
        addBotMessageSkeleton();

        // Save to history
        state.history.push({ role: 'user', content: question });

        try {
            const response = await fetch(CONFIG.apiEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question,
                    history: state.history.slice(0, -1),  // exclude the just-added
                    stream: true,
                }),
            });

            if (!response.ok) {
                const err = await response.json().catch(() => ({ error: 'Network error' }));
                throw new Error(err.error || `HTTP ${response.status}`);
            }

            // Read SSE stream
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let accumulatedText = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buffer += decoder.decode(value, { stream: true });

                // Process events separated by \n\n
                const parts = buffer.split('\n\n');
                buffer = parts.pop();  // keep incomplete part

                for (const part of parts) {
                    const lines = part.split('\n');
                    let event = 'message';
                    let data = '';
                    for (const line of lines) {
                        if (line.startsWith('event: ')) event = line.slice(7).trim();
                        else if (line.startsWith('data: ')) data += line.slice(6);
                    }
                    if (!data) continue;
                    if (event === 'sources') {
                        try {
                            const sources = JSON.parse(data);
                            appendSourcesToBot(sources);
                        } catch (e) { /* ignore parse errors */ }
                    } else if (event === 'token') {
                        try {
                            const token = JSON.parse(data);
                            accumulatedText += token;
                            appendTokenToBot(token);
                        } catch (e) { /* ignore */ }
                    } else if (event === 'error') {
                        try {
                            const err = JSON.parse(data);
                            throw new Error(err.error || 'Server error');
                        } catch (e) { /* ignore */ }
                    }
                }
            }

            finalizeBotMessage(accumulatedText);
        } catch (err) {
            if (state.currentBotMessage) {
                const bubble = state.currentBotMessage.querySelector('.message-bubble');
                bubble.innerHTML = `<div class="content"><p>❌ ${escapeHtml(err.message)}</p><p style="color:var(--td-text-muted);font-size:0.9em">Please try again, or check your connection.</p></div>`;
            }
            // Remove the failed question from history
            state.history.pop();
        } finally {
            state.isStreaming = false;
            setInputEnabled(true);
            $('.chat-input').focus();
        }
    }

    function setInputEnabled(enabled) {
        const input = $('.chat-input');
        const send = $('.chat-send');
        if (input) input.disabled = !enabled;
        if (send) send.disabled = !enabled;
        if (enabled && input) input.focus();
    }

    // -----------------------------------------------------------------------
    // Input handling
    // -----------------------------------------------------------------------
    function setupInputHandlers() {
        const input = $('.chat-input');
        const send = $('.chat-send');
        if (!input) return;

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitInput();
            }
        });

        send.addEventListener('click', submitInput);
        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = Math.min(input.scrollHeight, 150) + 'px';
        });
    }

    function submitInput() {
        const input = $('.chat-input');
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        input.style.height = 'auto';
        sendQuestion(text);
    }

    // -----------------------------------------------------------------------
    // Suggestions
    // -----------------------------------------------------------------------
    function setupSuggestions() {
        const container = $('.chat-suggestions');
        if (!container) return;
        CONFIG.suggestions.forEach(s => {
            const btn = document.createElement('button');
            btn.className = 'chat-suggestion';
            btn.textContent = s;
            btn.onclick = () => sendQuestion(s);
            container.appendChild(btn);
        });
    }

    // -----------------------------------------------------------------------
    // Language toggle (cookie-based)
// -----------------------------------------------------------------------
    function setupLangToggle() {
        const toggle = $('#lang-toggle');
        if (!toggle) return;
        const currentLang = document.documentElement.lang || 'en';
        const otherLang = currentLang === 'en' ? 'vi' : 'en';
        const otherUrl = currentLang === 'en'
            ? 'https://henryphamduc.github.io/tennis-wiki/'
            : window.location.origin;
        toggle.textContent = currentLang === 'en' ? '🇻🇳 Tiếng Việt' : '🇬🇧 English';
        toggle.title = `Switch to ${otherLang === 'vi' ? 'Vietnamese (Tennis-WIKI)' : 'English (Tennis-Doctor)'}`;
        toggle.onclick = () => {
            // Set cookie so the target site remembers preference
            document.cookie = `tennis-lang-pref=${otherLang};domain=.github.io;path=/;max-age=31536000`;
            window.location.href = otherUrl;
        };
    }

    // -----------------------------------------------------------------------
    // Init
    // -----------------------------------------------------------------------
    function init() {
        setupInputHandlers();
        setupSuggestions();
        setupLangToggle();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
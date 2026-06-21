/* Tennis Doctor - References page logic */
(function() {
    'use strict';

    const books = window.TENNIS_BOOKS || [];
    const tbody = document.getElementById('refs-tbody');
    const search = document.getElementById('refs-search');
    const filterBtns = document.querySelectorAll('.refs-filter');
    const visibleCount = document.getElementById('refs-visible-count');
    const totalCount = document.getElementById('refs-total-count');
    const bookCountEl = document.getElementById('book-count');
    const modal = document.getElementById('refs-modal');
    const modalBody = document.getElementById('refs-modal-body');
    const ths = document.querySelectorAll('.refs-table th[data-sort]');

    let activeFilter = 'all';
    let sortKey = 'title';
    let sortDir = 'asc';
    let searchQuery = '';

    if (bookCountEl) bookCountEl.textContent = books.length;
    if (totalCount) totalCount.textContent = books.length;

    // Sort books alphabetically by title initially
    const sorted = [...books].sort((a, b) => a.title.localeCompare(b.title));

    function getFiltered() {
        const q = searchQuery.trim().toLowerCase();
        return sorted.filter(b => {
            if (activeFilter !== 'all' && b.category !== activeFilter) return false;
            if (!q) return true;
            return (
                (b.title || '').toLowerCase().includes(q) ||
                (b.author || '').toLowerCase().includes(q) ||
                (b.category || '').toLowerCase().includes(q) ||
                (b.publisher || '').toLowerCase().includes(q) ||
                (b.intro || '').toLowerCase().includes(q)
            );
        });
    }

    function sortBooks(arr) {
        const k = sortKey;
        const d = sortDir === 'asc' ? 1 : -1;
        return [...arr].sort((a, b) => {
            const av = (a[k] || '').toString().toLowerCase();
            const bv = (b[k] || '').toString().toLowerCase();
            if (k === 'year') {
                return (parseInt(a.year) || 0 - parseInt(b.year) || 0) * d;
            }
            return av.localeCompare(bv) * d;
        });
    }

    function render() {
        const filtered = sortBooks(getFiltered());
        visibleCount.textContent = filtered.length;

        tbody.innerHTML = filtered.map((b, i) => `
            <tr data-id="${escapeHtml(b.id)}">
                <td class="col-num">${i + 1}</td>
                <td class="col-title"><strong>${escapeHtml(b.title)}</strong></td>
                <td class="col-author">${escapeHtml(b.author)}</td>
                <td class="col-year">${escapeHtml(b.year)}</td>
                <td class="col-cat"><span class="refs-cat refs-cat-${escapeHtml(b.category)}">${escapeHtml(b.category)}</span></td>
                <td class="col-actions"><button class="refs-detail-btn" data-id="${escapeHtml(b.id)}">About →</button></td>
            </tr>
        `).join('');

        // Re-bind detail buttons
        tbody.querySelectorAll('.refs-detail-btn').forEach(btn => {
            btn.addEventListener('click', e => {
                e.preventDefault();
                showDetail(btn.getAttribute('data-id'));
            });
        });
    }

    function showDetail(id) {
        const b = books.find(x => x.id === id);
        if (!b) return;
        const paragraphs = (b.intro || '').split('\n\n').filter(Boolean);
        modalBody.innerHTML = `
            <h2 id="refs-modal-title">${escapeHtml(b.title)}</h2>
            <div class="refs-modal-meta">
                <span class="refs-meta-item"><strong>Author:</strong> ${escapeHtml(b.author)}</span>
                <span class="refs-meta-item"><strong>Year:</strong> ${escapeHtml(b.year)}</span>
                <span class="refs-meta-item"><strong>Publisher:</strong> ${escapeHtml(b.publisher || '—')}</span>
                <span class="refs-meta-item"><strong>Topic:</strong> <span class="refs-cat refs-cat-${escapeHtml(b.category)}">${escapeHtml(b.category)}</span></span>
            </div>
            <div class="refs-modal-intro">
                ${paragraphs.map(p => `<p>${escapeHtml(p)}</p>`).join('')}
            </div>
            <div class="refs-modal-cta">
                <a href="/chat/?q=${encodeURIComponent('Tell me about ' + b.title + ' by ' + b.author)}" class="td-btn td-btn-primary">Ask Tennis Doctor about this book →</a>
            </div>
        `;
        modal.hidden = false;
        document.body.style.overflow = 'hidden';
        // Focus close button for accessibility
        modal.querySelector('.refs-modal-close').focus();
    }

    function hideDetail() {
        modal.hidden = true;
        document.body.style.overflow = '';
    }

    // Wire up filters
    filterBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            filterBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            activeFilter = btn.getAttribute('data-filter');
            render();
        });
    });

    // Wire up search
    let searchTimer;
    if (search) {
        search.addEventListener('input', () => {
            clearTimeout(searchTimer);
            searchTimer = setTimeout(() => {
                searchQuery = search.value;
                render();
            }, 150);
        });
    }

    // Wire up sort
    ths.forEach(th => {
        th.addEventListener('click', () => {
            const k = th.getAttribute('data-sort');
            if (sortKey === k) {
                sortDir = sortDir === 'asc' ? 'desc' : 'asc';
            } else {
                sortKey = k;
                sortDir = 'asc';
            }
            ths.forEach(t => t.classList.remove('sort-asc', 'sort-desc'));
            th.classList.add(sortDir === 'asc' ? 'sort-asc' : 'sort-desc');
            render();
        });
    });

    // Wire up modal close
    modal.querySelectorAll('[data-close]').forEach(el => {
        el.addEventListener('click', hideDetail);
    });
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && !modal.hidden) hideDetail();
    });

    function escapeHtml(s) {
        if (s == null) return '';
        return String(s)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    // Initial render
    render();
})();
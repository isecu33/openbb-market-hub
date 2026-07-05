// API Base URL
const API_BASE = 'http://localhost:8000';

// Estado de la aplicacion
let appState = {
    portfolioSymbols: [],
    thesisCandidates: [],
    newsCount: 0
};

// Inicializar la app
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    loadDashboardStats();

    // Pre-cargar portfolio de ejemplo
    document.getElementById('portfolio-input').value = 'AAPL, MSFT, NVDA';
});

// Navegacion entre secciones
function initNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const section = btn.dataset.section;
            showSection(section);

            // Actualizar boton activo
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        });
    });
}

function showSection(sectionId) {
    const sections = document.querySelectorAll('.section');
    sections.forEach(section => {
        section.classList.remove('active');
    });

    document.getElementById(sectionId).classList.add('active');
}

// Dashboard Stats
async function loadDashboardStats() {
    try {
        const response = await fetch(`${API_BASE}/api/status`);
        const data = await response.json();

        if (data.status === 'ok') {
            document.getElementById('portfolio-count').textContent = appState.portfolioSymbols.length || 3;
            document.getElementById('thesis-count').textContent = appState.thesisCandidates.length || 13;
            document.getElementById('news-count').textContent = appState.newsCount || 15;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// PORTFOLIO
async function loadPortfolio() {
    const input = document.getElementById('portfolio-input').value;
    const symbols = input.split(',').map(s => s.trim().toUpperCase()).filter(s => s.length > 0);

    if (symbols.length === 0) {
        alert('Por favor ingresa al menos un simbolo');
        return;
    }

    const loadingEl = document.getElementById('portfolio-loading');
    const resultsEl = document.getElementById('portfolio-results');

    loadingEl.classList.remove('hidden');
    resultsEl.innerHTML = '';

    try {
        const params = symbols.map(s => `symbols=${s}`).join('&');
        const response = await fetch(`${API_BASE}/portfolio?${params}`);
        const data = await response.json();

        appState.portfolioSymbols = symbols;
        appState.newsCount = 0;

        if (data.positions && data.positions.length > 0) {
            resultsEl.innerHTML = data.positions.map(pos => renderPosition(pos)).join('');
            loadDashboardStats();
        } else {
            resultsEl.innerHTML = '<div class="card"><p>No se encontraron datos</p></div>';
        }
    } catch (error) {
        resultsEl.innerHTML = `<div class="card alert alert-warning"><strong>Error:</strong> ${error.message}</div>`;
    } finally {
        loadingEl.classList.add('hidden');
    }
}

function renderPosition(position) {
    const symbol = position.symbol || 'N/A';
    const price = position.price || 'N/A';
    const news = position.news || [];

    appState.newsCount += news.length;

    return `
        <div class="position-card">
            <div class="position-header">
                <div class="position-symbol">${symbol}</div>
                <div class="position-price">$${typeof price === 'number' ? price.toFixed(2) : price}</div>
            </div>

            <div class="news-list">
                <h4 style="color: var(--text-secondary); margin-bottom: 0.75rem; font-size: 1rem;">
                    📰 Noticias Recientes (${news.length})
                </h4>
                ${news.length > 0 ? news.map(n => renderNews(n)).join('') : '<p style="color: var(--text-secondary);">No hay noticias disponibles</p>'}
            </div>
        </div>
    `;
}

function renderNews(newsItem) {
    const title = newsItem.title || newsItem.headline || 'Sin titulo';
    const source = newsItem.source || newsItem.publisher || 'Fuente desconocida';
    const date = newsItem.date || newsItem.published_utc || null;

    return `
        <div class="news-item">
            <div class="news-title">${title}</div>
            <div class="news-source">
                ${source}${date ? ' • ' + formatDate(date) : ''}
            </div>
        </div>
    `;
}

// TESIS TEMATICAS
async function loadThesis() {
    const sector = document.getElementById('thesis-sector').value;
    const growth = document.getElementById('thesis-growth').value;
    const pe = document.getElementById('thesis-pe').value;

    const loadingEl = document.getElementById('thesis-loading');
    const resultsEl = document.getElementById('thesis-results');

    loadingEl.classList.remove('hidden');
    resultsEl.innerHTML = '';

    try {
        let url = `${API_BASE}/thesis?`;
        if (sector) url += `sector=${encodeURIComponent(sector)}&`;
        if (growth) url += `min_revenue_growth=${growth}&`;
        if (pe) url += `max_pe=${pe}&`;

        const response = await fetch(url);
        const data = await response.json();

        appState.thesisCandidates = data.candidates || [];

        if (data.candidates && data.candidates.length > 0) {
            resultsEl.innerHTML = `
                <div class="card">
                    <div class="card-header">
                        <h3>Candidatas Encontradas (${data.candidates.length})</h3>
                    </div>
                    ${data.candidates.map(c => renderCandidate(c)).join('')}
                </div>
            `;
            loadDashboardStats();
        } else {
            resultsEl.innerHTML = '<div class="card"><p>No se encontraron candidatas con esos criterios. Intenta relajar los filtros.</p></div>';
        }
    } catch (error) {
        resultsEl.innerHTML = `<div class="card alert alert-warning"><strong>Error:</strong> ${error.message}</div>`;
    } finally {
        loadingEl.classList.add('hidden');
    }
}

function renderCandidate(candidate) {
    return `
        <div class="candidate-card" style="margin-top: 1rem;">
            <div class="position-header">
                <div class="position-symbol">${candidate.symbol}</div>
                <div style="color: var(--text-secondary);">${candidate.name || 'N/A'}</div>
            </div>
            <div class="candidate-info">
                <div class="info-item">
                    <div class="info-label">Sector</div>
                    <div class="info-value">${candidate.sector || 'N/A'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">P/E Ratio</div>
                    <div class="info-value">${candidate.pe_ratio ? candidate.pe_ratio.toFixed(2) : 'N/A'}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Crecimiento Ingresos</div>
                    <div class="info-value" style="color: var(--secondary);">
                        ${candidate.revenue_growth ? (candidate.revenue_growth * 100).toFixed(1) + '%' : 'N/A'}
                    </div>
                </div>
            </div>
        </div>
    `;
}

// TRACKER POLITICOS
async function loadPoliticians() {
    const politician = document.getElementById('politician-name').value;
    const days = document.getElementById('politician-days').value;
    const minTrades = document.getElementById('politician-min-trades').value;

    const loadingEl = document.getElementById('politicians-loading');
    const resultsEl = document.getElementById('politicians-results');

    loadingEl.classList.remove('hidden');
    resultsEl.innerHTML = '';

    try {
        let url = `${API_BASE}/politician-trades?build_watchlist=true&days_back=${days}&min_trades=${minTrades}`;
        if (politician) url += `&politician=${encodeURIComponent(politician)}`;

        const response = await fetch(url);
        const data = await response.json();

        if (response.status === 500) {
            throw new Error(data.detail || 'Error del servidor');
        }

        if (data.watchlist && data.watchlist.length > 0) {
            resultsEl.innerHTML = renderWatchlist(data.watchlist, data.source);
        } else {
            resultsEl.innerHTML = `
                <div class="card alert alert-warning">
                    <p><strong>ℹ️ Sin datos disponibles</strong></p>
                    <p>El endpoint de Government Trades requiere un plan premium de FMP. El plan gratuito no incluye estos datos.</p>
                    <p>Alternativamente, no se encontraron operaciones que cumplan los criterios especificados.</p>
                </div>
            `;
        }
    } catch (error) {
        resultsEl.innerHTML = `
            <div class="card alert alert-warning">
                <p><strong>Error:</strong> ${error.message}</p>
                <p>El endpoint de Government Trades generalmente requiere un plan premium de FMP. Verifica tu suscripcion o los parametros de busqueda.</p>
            </div>
        `;
    } finally {
        loadingEl.classList.add('hidden');
    }
}

function renderWatchlist(watchlist, source) {
    return `
        <div class="card">
            <div class="card-header">
                <h3>Watchlist Espejo - Top Operaciones</h3>
                <span style="color: var(--text-secondary); font-size: 0.9rem;">Fuente: ${source}</span>
            </div>
            <table class="watchlist-table">
                <thead>
                    <tr>
                        <th>Simbolo</th>
                        <th>Numero de Operaciones</th>
                    </tr>
                </thead>
                <tbody>
                    ${watchlist.map(([symbol, count]) => `
                        <tr>
                            <td><strong>${symbol}</strong></td>
                            <td>${count} operaciones</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
}

// UTILIDADES
function formatDate(dateStr) {
    try {
        const date = new Date(dateStr);
        return date.toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (e) {
        return dateStr;
    }
}

function formatCurrency(value) {
    if (typeof value !== 'number') return value;
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'USD'
    }).format(value);
}

// Exportar funciones globales
window.showSection = showSection;
window.loadPortfolio = loadPortfolio;
window.loadThesis = loadThesis;
window.loadPoliticians = loadPoliticians;

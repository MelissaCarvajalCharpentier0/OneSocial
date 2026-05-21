const fileInput = document.getElementById('image-input');
const fileName = document.getElementById('file-name');
const overlay = document.getElementById('overlay');
let currentImage = null;
let publishResults = [];

const accountState = {
    accountsByProvider: {},
    selected: new Set(),
    activeTab: 'Todas',
    hasLoaded: false,
    collapsedProviders: new Set()
};

function escapeHTML(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        fileName.textContent = file.name;

        const reader = new FileReader();
        reader.onload = function (e) {
            currentImage = e.target.result;
            updatePreview(); 
        };

        reader.readAsDataURL(file);

    } else {
        fileName.textContent = "No file selected";
        currentImage = null;
        updatePreview();
    }

    syncSidebarHeight();
});

// ==================== LINK ACCOUNTS SIDEBAR ====================
const linkSidebar = document.getElementById('link-sidebar');
const showLinkBtn = document.getElementById('show-link-sidebar-btn');
const closeLinkBtn = document.getElementById('close-link-sidebar');

function toggleLinkSidebar(show) {
    if (show) {
        linkSidebar.classList.remove('hidden-sidebar');
        linkSidebar.classList.add('visible-sidebar');
        overlay.classList.add('active');
    } else {
        linkSidebar.classList.add('hidden-sidebar');
        linkSidebar.classList.remove('visible-sidebar');
        overlay.classList.remove('active');
    }
}

overlay.addEventListener('click', () => {
    toggleLinkSidebar(false);
});

showLinkBtn.addEventListener('click', () => toggleLinkSidebar(true));
closeLinkBtn.addEventListener('click', () => toggleLinkSidebar(false));

// Expand/collapse forms
const mastodonToggle = document.getElementById('toggle-mastodon-form');
const wordpressToggle = document.getElementById('toggle-wordpress-form');
const blueskyToggle = document.getElementById('toggle-bluesky-form');
// const redditToggle = document.getElementById('toggle-reddit-form');
const wordpressRestToggle = document.getElementById('toggle-wordpress-rest-form');
const linkedinToggle = document.getElementById('toggle-linkedin-form');
const mastodonForm = document.getElementById('mastodon-form');
const wordpressForm = document.getElementById('wordpress-form');
const blueskyForm = document.getElementById('bluesky-form');
// const redditForm = document.getElementById('reddit-form');
const wordpressRestForm = document.getElementById('wordpress-rest-form');
const linkedinForm = document.getElementById('linkedin-form');

mastodonToggle.addEventListener('click', () => {
    mastodonForm.classList.toggle('hidden-form');
    const icon = mastodonToggle.querySelector('.expand-icon');
    icon.textContent = mastodonForm.classList.contains('hidden-form') ? '▼' : '▲';
});

wordpressToggle.addEventListener('click', () => {
    wordpressForm.classList.toggle('hidden-form');
    const icon = wordpressToggle.querySelector('.expand-icon');
    icon.textContent = wordpressForm.classList.contains('hidden-form') ? '▼' : '▲';
});

blueskyToggle.addEventListener('click', () => {
    blueskyForm.classList.toggle('hidden-form');
    const icon = blueskyToggle.querySelector('.expand-icon');
    icon.textContent = blueskyForm.classList.contains('hidden-form') ? '▼' : '▲';
});
wordpressRestToggle.addEventListener('click', () => {
    wordpressRestForm.classList.toggle('hidden-form');
    const icon = wordpressRestToggle.querySelector('.expand-icon');
    icon.textContent = wordpressRestForm.classList.contains('hidden-form') ? '▼' : '▲';
});

linkedinToggle.addEventListener('click', () => {
    linkedinForm.classList.toggle('hidden-form');
    const icon = linkedinToggle.querySelector('.expand-icon');
    icon.textContent = linkedinForm.classList.contains('hidden-form') ? '▼' : '▲';
});

/* redditToggle.addEventListener('click', () => {
    redditForm.classList.toggle('hidden-form');
    const icon = redditToggle.querySelector('.expand-icon');
    icon.textContent = redditForm.classList.contains('hidden-form') ? '▼' : '▲';
}); */

// Mastodon: Get Auth URL & Connect
document.getElementById('get-mastodon-url-btn').addEventListener('click', async () => {
    const username = document.getElementById('mastodon-username').value.trim();
    
    if (!username) {
        showLinkStatus('mastodon-status', 'Please enter username first', 'error');
        return;
    }
    try {
        showLinkStatus('mastodon-status', 'Connecting to Mastodon...', 'info');
        
        // Calls connect_mastodon from main.py
        const result = await eel.connect_mastodon(username)();
        
        if (result && result.success) {
            showLinkStatus('mastodon-status', result.message, 'success');
            await loadAccounts(); // Account might be fully linked!
        } else {
            // This handles the fallback if they need to paste an auth code
            showLinkStatus('mastodon-status', result.message || 'Complete login, then paste the code below', 'info');
        }
    } catch (err) {
        showLinkStatus('mastodon-status', 'Error: ' + err, 'error');
    }
});

// Mastodon: Link account with Auth Code
document.getElementById('link-mastodon-btn').addEventListener('click', async () => {
    const username = document.getElementById('mastodon-username').value.trim();
    const code = document.getElementById('mastodon-code').value.trim();
    
    if (!username || !code) {
        showLinkStatus('mastodon-status', 'Username and auth code required', 'error');
        return;
    }
    
    try {
        showLinkStatus('mastodon-status', 'Linking account...', 'info');
        // Calls auth_mastodon from main.py
        const result = await eel.auth_mastodon(code, username)();
        
        if (result && result.success) {
            showLinkStatus('mastodon-status', result.message || 'Account linked!', 'success');
            document.getElementById('mastodon-username').value = '';
            document.getElementById('mastodon-code').value = '';
            await loadAccounts(); // Refresh left sidebar
            setTimeout(() => toggleLinkSidebar(false), 1500);
        } else {
            showLinkStatus('mastodon-status', result?.message || 'Link failed', 'error');
        }
    } catch (err) {
        showLinkStatus('mastodon-status', 'Error: ' + err, 'error');
    }
});

// WordPress: Link account
document.getElementById('link-wordpress-btn').addEventListener('click', async () => {
    const username = document.getElementById('wp-username').value.trim();
    const clientId = document.getElementById('wp-client-id').value.trim();
    const clientSecret = document.getElementById('wp-client-secret').value.trim();
    
    if (!username || !clientId || !clientSecret) {
        showLinkStatus('wordpress-status', 'All fields required', 'error');
        return;
    }
    
    try {
        showLinkStatus('wordpress-status', 'Starting WordPress OAuth...', 'info');
        const result = await eel.setup_wordpress_account(username, clientId, clientSecret)();
        
        if (result && result.success) {
            showLinkStatus('wordpress-status', result.message || 'Account linked!', 'success');
            document.getElementById('wp-username').value = '';
            document.getElementById('wp-client-id').value = '';
            document.getElementById('wp-client-secret').value = '';
            await loadAccounts();
            setTimeout(() => toggleLinkSidebar(false), 1500);
        } else {
            showLinkStatus('wordpress-status', result?.message || 'Link failed', 'error');
        }
    } catch (err) {
        showLinkStatus('wordpress-status', 'Error: ' + err, 'error');
    }
});

// Bluesky: Link account
document.getElementById('link-bluesky-btn').addEventListener('click', async () => {
    const username = document.getElementById('bk-username').value.trim();
    const password = document.getElementById('bk-password').value.trim();
    
    if (!username || !password) {
        showLinkStatus('bluesky-status', 'All fields required', 'error');
        return;
    }
    
    try {
        showLinkStatus('bluesky-status', 'Starting Bluesky Login...', 'info');
        const result = await eel.setup_bluesky_account(username, password)();
        
        if (result && result.success) {
            showLinkStatus('bluesky-status', result.message || 'Account linked!', 'success');
            document.getElementById('bk-username').value = '';
            document.getElementById('bk-password').value = '';
            await loadAccounts();
            setTimeout(() => toggleLinkSidebar(false), 1500);
        } else {
            showLinkStatus('bluesky-status', result?.message || 'Link failed', 'error');
        }
    } catch (err) {
        showLinkStatus('bluesky-status', 'Error: ' + err, 'error');
    }
});
// Self‑hosted WordPress link handler
document.getElementById('link-wordpress-rest-btn').addEventListener('click', async () => {
    const siteUrl = document.getElementById('wp-rest-url').value.trim();
    const username = document.getElementById('wp-rest-username').value.trim();
    const appPassword = document.getElementById('wp-rest-password').value.trim();
    
    if (!siteUrl || !username || !appPassword) {
        showLinkStatus('wordpress-rest-status', 'All fields required', 'error');
        return;
    }
    
    try {
        showLinkStatus('wordpress-rest-status', 'Verifying credentials...', 'info');
        // Calls connect_wordpress_rest from main.py
        const result = await eel.connect_wordpress_rest(siteUrl, username, appPassword)();
        
        if (result && result.success) {
            showLinkStatus('wordpress-rest-status', result.message, 'success');
            document.getElementById('wp-rest-url').value = '';
            document.getElementById('wp-rest-username').value = '';
            document.getElementById('wp-rest-password').value = '';
            await loadAccounts();
            setTimeout(() => toggleLinkSidebar(false), 1500);
        } else {
            showLinkStatus('wordpress-rest-status', result?.message || 'Link failed', 'error');
        }
    } catch (err) {
        showLinkStatus('wordpress-rest-status', 'Error: ' + err, 'error');
    }
});


// LinkedIn: Abrir OAuth URL y conectar
document.getElementById('get-linkedin-url-btn').addEventListener('click', async () => {

    const clientId = document.getElementById('ln-client-id').value.trim();

    if (!clientId) {
        showLinkStatus('linkedin-status', 'Client ID required', 'error');
        return;
    }

    try {
        const response = await eel.connect_linkedin(clientId)();

        if (response.success) {
            showLinkStatus('linkedin-status', response.message, 'success');
        } else {
            showLinkStatus('linkedin-status', response.message, 'error');
        }

    } catch (err) {
        showLinkStatus('linkedin-status', 'Error: ' + err, 'error');
    }
});


// LinkedIn: Link account with Auth Code
document.getElementById('link-linkedin-btn').addEventListener('click', async () => {
    const username =document.getElementById('ln-username').value.trim();
    const clientId = document.getElementById('ln-client-id').value.trim();
    const clientSecret = document.getElementById('ln-client-secret').value.trim();
    const code = document.getElementById('ln-code').value.trim();

    if (!username || !clientId || !clientSecret || !code) {
        showLinkStatus('linkedin-status', 'All fields are required', 'error');
        return;
    }

    try {
        showLinkStatus('linkedin-status', 'Linking LinkedIn account...', 'info');
        const result = await eel.auth_linkedin(username, clientId, clientSecret, code)();

        if (result && result.success) {
            showLinkStatus('linkedin-status', result.message || 'LinkedIn account linked!', 'success');
            document.getElementById('ln-username').value = '';
            document.getElementById('ln-client-id').value = '';
            document.getElementById('ln-client-secret').value = '';
            document.getElementById('ln-code').value = '';
            await loadAccounts();
            setTimeout(() => toggleLinkSidebar(false), 1500);
        } else {
            showLinkStatus('linkedin-status', result?.message || 'LinkedIn link failed', 'error');
        }
    } catch (err) {
        showLinkStatus('linkedin-status', 'Error: ' + err, 'error');
    }
});


// Reddit: Link account
/* document.getElementById('link-reddit-btn').addEventListener('click', async () => {
    const username = document.getElementById('reddit-username').value.trim();
    const clientId = document.getElementById('reddit-client-id').value.trim();
    const clientSecret = document.getElementById('reddit-client-secret').value.trim();
    const subreddit = document.getElementById('reddit-subreddit').value.trim();

    if (!username || !clientId || !clientSecret || !subreddit) {
        showLinkStatus('reddit-status', 'All fields required', 'error');
        return;
    }

    try {
        showLinkStatus('reddit-status', 'Starting Reddit OAuth...', 'info');
        const result = await eel.setup_reddit_account(username, clientId, clientSecret, subreddit)();

        if (result && result.success) {
            showLinkStatus('reddit-status', result.message || 'Account linked!', 'success');
            document.getElementById('reddit-username').value = '';
            document.getElementById('reddit-client-id').value = '';
            document.getElementById('reddit-client-secret').value = '';
            document.getElementById('reddit-subreddit').value = '';
            await loadAccounts();
            setTimeout(() => toggleLinkSidebar(false), 1500);
        } else {
            showLinkStatus('reddit-status', result?.message || 'Link failed', 'error');
        }
    } catch (err) {
        showLinkStatus('reddit-status', 'Error: ' + err, 'error');
    }
}); */

function showLinkStatus(elementId, message, type) {
    const el = document.getElementById(elementId);
    el.textContent = message;
    el.className = `link-status ${type}`;
    setTimeout(() => {
        if (el.textContent === message) {
            el.textContent = '';
            el.className = 'link-status';
        }
    }, 4000);
}

// ==================== EXISTING ACCOUNT FUNCTIONS ====================
eel.expose(showStatus);
function showStatus(message, type) {
    const statusBar = document.getElementById('publish-status-bar');
    const statusText = document.getElementById('publish-status-text');

    if (!statusBar || !statusText) return;
    statusText.textContent = message;
    statusBar.classList.remove('hidden');
    statusBar.classList.remove('success', 'error', 'info');
    statusBar.classList.add(type);

    setTimeout(() => {
        statusBar.classList.add('hidden');
    }, 3000);
}

function accountKey(provider, username) {
    return `${provider}::${username}`;
}

function accountFromKey(key) {
    const splitIndex = key.indexOf('::');
    return [key.slice(0, splitIndex), key.slice(splitIndex + 2)];
}

function getAllAccountObjects() {
    const all = [];
    Object.keys(accountState.accountsByProvider).forEach((provider) => {
        accountState.accountsByProvider[provider].forEach((acc) => {
            all.push({ provider, username: acc.username, accountLabel: acc.accountLabel });
        });
    });
    return all;
}

function getAccountsForActiveTab() {
    if (accountState.activeTab === 'Todas') {
        return getAllAccountObjects();
    }
}

// --- NEW: Nickname/label helpers ---
function getAccountLabel(provider, username) {
    const accounts = accountState.accountsByProvider[provider];
    if (accounts) {
        const acc = accounts.find(a => a.username === username);
        return acc ? acc.accountLabel : null;
    }
    return null;
}

function updateAccountLabel(provider, username, newLabel) {
    const accounts = accountState.accountsByProvider[provider];
    if (accounts) {
        const acc = accounts.find(a => a.username === username);
        if (acc) acc.accountLabel = newLabel || null;
    }
}

function renderTabs() {
    const providers = Object.keys(accountState.accountsByProvider).sort((a, b) => a.localeCompare(b));
    const tabs = ['Todas', ...providers];

    if (!tabs.includes(accountState.activeTab)) {
        accountState.activeTab = 'Todas';
    }
}

function renderAccountList() {
    const listContainer = document.getElementById('account-list');
    const accounts = getAccountsForActiveTab();

    if (accounts.length === 0) {
        listContainer.innerHTML = '<div class="empty-accounts">No linked accounts found.</div>';
        renderSummary();
        return;
    }
    const grouped = {};

    accounts.forEach(acc => {
        const providerKey = acc.provider || 'unknown';
        if (!grouped[providerKey]) {
            grouped[providerKey] = [];
        }
        grouped[providerKey].push(acc);
    });

    let html = '';

    Object.keys(grouped).forEach(provider => {

        const isCollapsed = accountState.collapsedProviders.has(provider);

        const styles = {
            Mastodon: { icon: 'icons/Mastodon_logo.png', border: '#6364FF' },
            WordPress: { icon: 'icons/WordPress_logo.png', border: '#21759B' },
            WordPressREST: { icon: 'icons/WordPress_logo.png', border: '#21759B' },
            Bluesky: { icon: 'icons/Bluesky_logo.png', border: '#1184FE' },
            LinkedIn: { icon: 'icons/LinkedIn_logo.png', border: '#0077B5' },
            // Reddit: { icon: 'icons/default.png', border: '#ff4500' }
        };
        const data = styles[provider] || { icon: 'icons/default.png'};
        const displayName = provider.charAt(0).toUpperCase() + provider.slice(1);

        html += `
            <div class="provider-group">
                <div class="provider-header" data-provider="${provider}">
                    
                    <div class="provider-left">
                        <div class="provider-icon">
                            <img src="${data.icon}">
                        </div>
                        <span class="provider-name">${displayName}</span>
                    </div>

                    <span class="toggle-icon">${isCollapsed ? '▶' : '▼'}</span>

                </div>
                
                <div class="account-items ${isCollapsed ? 'collapsed' : ''}">
        `;

        grouped[provider].forEach(({ username, accountLabel }) => {
            const display = accountLabel || username;
            const key = accountKey(provider, username);
            const checked = accountState.selected.has(key) ? 'checked' : '';

            html += `
                <label class="account-item">
                    <input type="checkbox"
                        data-provider="${provider}"
                        data-username="${username}"
                        ${checked}>

                    <span class="account-name" title="${display}">${display}</span>

                    <div class="account-actions">
                        <button class="edit-label-btn"
                            data-provider="${provider}"
                            data-username="${username}"
                            title="Edit label">✎</button>

                        <button class="delete-account-btn"
                            data-provider="${provider}"
                            data-username="${username}"
                            title="Delete account">x</button>
                    </div>
                </label>
            `;
        });

        html += `
                </div>
            </div>
        `;
    });

    listContainer.innerHTML = html;

    document.querySelectorAll('.provider-header').forEach(header => {
        header.addEventListener('click', () => {
            const provider = header.dataset.provider;

            if (accountState.collapsedProviders.has(provider)) {
                accountState.collapsedProviders.delete(provider);
            } else {
                accountState.collapsedProviders.add(provider);
            }

            renderAccountList();
        });
    });

    document.querySelectorAll('.account-item input').forEach(input => {
        input.addEventListener('click', e => e.stopPropagation());
    });

    renderSummary();
}

function openModal({ title, bodyHTML, confirmText = "OK", danger = false }) {
    return new Promise((resolve) => {

        const modalOverlay = document.getElementById('modal-overlay');
        const modal = document.getElementById('modal');

        const titleEl = document.getElementById('modal-title');
        const bodyEl = document.getElementById('modal-body');
        const confirmBtn = document.getElementById('modal-confirm');
        const cancelBtn = document.getElementById('modal-cancel');

        titleEl.textContent = title;
        bodyEl.innerHTML = bodyHTML;
        confirmBtn.textContent = confirmText;

        confirmBtn.classList.toggle('danger', danger);

        modalOverlay.classList.remove('hidden'); 
        modalOverlay.classList.add('active');

        modal.classList.add('active'); 

        const close = () => {
            modalOverlay.classList.remove('active');
            modalOverlay.classList.add('hidden');

            modal.classList.remove('active'); 
        };

        cancelBtn.onclick = () => {
            close();
            resolve(null); 
        };

        confirmBtn.onclick = () => {
            close();
            resolve(true); 
        };

        modalOverlay.onclick = () => {
            close();
            resolve(null);
        };
    });
}

function renderSummary() {
    const summary = document.getElementById('account-summary');
    const total = getAllAccountObjects().length;
    const selectedCount = accountState.selected.size;
    summary.textContent = `${selectedCount} of ${total} account(s) selected`;
}

function renderAccounts() {
    renderTabs();
    renderAccountList();
    syncSidebarHeight();
}

function syncSidebarHeight() {
    const leftSidebar = document.querySelector('.account-sidebar');
    const rightSidebar = document.getElementById('link-sidebar');
    const mainContainer = document.querySelector('.container');

    if (window.innerWidth <= 1180) {
        if (leftSidebar) leftSidebar.style.height = '';
        if (rightSidebar) rightSidebar.style.height = '';
        return;
    }

    const mainHeight = mainContainer ? mainContainer.offsetHeight : 0;
    if (leftSidebar) leftSidebar.style.height = `${mainHeight}px`;
    if (rightSidebar && rightSidebar.classList.contains('visible-sidebar')) {
        rightSidebar.style.height = `${mainHeight}px`;
    } else if (rightSidebar) {
        rightSidebar.style.height = '';
    }
}

async function loadAccounts() {
    try {
        const response = await eel.get_available_accounts()();

        if (!response || !response.success) {
            showStatus('Could not load linked accounts', 'error');
            document.getElementById('account-list').innerHTML = '<div class="empty-accounts">Could not load accounts.</div>';
            document.getElementById('account-summary').textContent = '0 of 0 account(s) selected';
            return;
        }

        const grouped = {};
        (response.accounts || []).forEach((account) => {
            const provider = account.provider ?? account[0];
            const username = account.username ?? account[1];
            const accountLabel = account.display_name ?? account[2] ?? null; 
            if (!provider || !username) return;
            if (!grouped[provider]) grouped[provider] = [];
            grouped[provider].push({ username, accountLabel });
        });

        // Sort by username or label
        Object.keys(grouped).forEach((provider) => {
            grouped[provider].sort((a, b) => a.username.localeCompare(b.username));
        });

        accountState.accountsByProvider = grouped;

        if (!accountState.hasLoaded) {
            getAllAccountObjects().forEach(({ provider, username }) => {
                accountState.selected.add(accountKey(provider, username));
            });
            accountState.hasLoaded = true;
        }

        renderAccounts();
        updatePreview();

    } catch (error) {
        console.error(error);
        showStatus('Error loading linked accounts', 'error');
    }
}

function getSelectedAccountsPayload() {
    return [...accountState.selected].map((key) => accountFromKey(key));
}

eel.expose(clearForm);
function clearForm() {
    document.getElementById('post-header').value = '';
    document.getElementById('post-body').value = '';
    fileName.textContent = "No file selected";
    currentImage = null;
    updatePreview();
    updateCounters();
    syncSidebarHeight();
}

function updateCounters() {
    const header = document.getElementById('post-header').value;
    const body = document.getElementById('post-body').value;
    document.getElementById('header-count').textContent = header.length;
    document.getElementById('body-count').textContent = body.length;
}

function renderMastodon(label, username, header, body, image) {
    const content = [header, body].filter(Boolean).join('\n');
    const avatarLetter = label ? label.charAt(0).toUpperCase() : 'M';

    return `
        <div class="mastodon-post">
            <div class="mastodon-top">
                <div class="avatar mastodon-avatar">${avatarLetter}</div>

                <div class="mastodon-user">
                    <div class="name">${label}</div>
                    <div class="handle">${username}</div>
                </div>

                <div class="mastodon-time">
                    <svg viewBox="0 0 24 24" class="mastodon-small-icon">
                        <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm6.9 9h-3.1a15.7 15.7 0 0 0-1.1-5A8.05 8.05 0 0 1 18.9 11ZM12 4.1c.8 1.1 1.5 3 1.8 4.9h-3.6c.3-1.9 1-3.8 1.8-4.9ZM4.3 13h3.1c.1 1.8.5 3.5 1.1 5A8.05 8.05 0 0 1 4.3 13Zm3.1-2H4.3A8.05 8.05 0 0 1 8.5 6a15.7 15.7 0 0 0-1.1 5ZM12 19.9c-.8-1.1-1.5-3-1.8-4.9h3.6c-.3 1.9-1 3.8-1.8 4.9Zm2.2-6.9H9.8A16.5 16.5 0 0 1 9.7 12c0-.3 0-.7.1-1h4.4c0 .3.1.7.1 1s0 .7-.1 1Zm1.3 5c.6-1.5 1-3.2 1.1-5h3.1a8.05 8.05 0 0 1-4.2 5Zm1.1-7c-.1-1.8-.5-3.5-1.1-5a8.05 8.05 0 0 1 4.2 5h-3.1Z"/>
                    </svg>
                    1 d
                </div>
            </div>

            <div class="mastodon-content">
                <p>${content || 'Your post content...'}</p>
                ${image ? `<img src="${image}" class="mastodon-image"/>` : ''}
            </div>

            <div class="mastodon-actions">
                <button class="mastodon-action-btn mastodon-reply-btn" aria-label="Reply">
                    <svg viewBox="0 0 24 24">
                        <path d="M9 7 4 12l5 5" />
                        <path d="M4 12h9.5A5.5 5.5 0 0 1 19 17.5V19" />
                    </svg>
                    <span>0</span>
                </button>

                <button class="mastodon-action-btn" aria-label="Boost">
                    <svg viewBox="0 0 24 24">
                        <path d="M7 7h9.2l-2.1-2.1a1 1 0 0 1 1.4-1.4l3.8 3.8a1 1 0 0 1 0 1.4l-3.8 3.8a1 1 0 1 1-1.4-1.4L16.2 9H7a3 3 0 0 0-3 3v1H2v-1a5 5 0 0 1 5-5Zm10 10H7.8l2.1 2.1a1 1 0 0 1-1.4 1.4l-3.8-3.8a1 1 0 0 1 0-1.4l3.8-3.8a1 1 0 1 1 1.4 1.4L7.8 15H17a3 3 0 0 0 3-3v-1h2v1a5 5 0 0 1-5 5Z"/>
                    </svg>
                </button>

                <button class="mastodon-action-btn" aria-label="Favorite">
                    <svg viewBox="0 0 24 24">
                        <path d="m12 2.8 2.9 5.9 6.5.9-4.7 4.6 1.1 6.5L12 17.6 6.2 20.7l1.1-6.5-4.7-4.6 6.5-.9L12 2.8Zm0 4.5-1.6 3.2-3.6.5 2.6 2.5-.6 3.6 3.2-1.7 3.2 1.7-.6-3.6 2.6-2.5-3.6-.5L12 7.3Z"/>
                    </svg>
                </button>

                <button class="mastodon-action-btn" aria-label="Bookmark">
                    <svg viewBox="0 0 24 24">
                        <path d="M6 3h12a1 1 0 0 1 1 1v19l-7-4-7 4V4a1 1 0 0 1 1-1Zm2 2v14.55l4-2.29 4 2.29V5H8Z"/>
                    </svg>
                </button>

                <button class="mastodon-action-btn" aria-label="More">
                    <svg viewBox="0 0 24 24">
                        <circle cx="5" cy="12" r="2"></circle>
                        <circle cx="12" cy="12" r="2"></circle>
                        <circle cx="19" cy="12" r="2"></circle>
                    </svg>
                </button>
            </div>
        </div>
    `;
}

function renderWordPress(label, username, header, body, image) {
    return `
        <div class="wp-post">
            ${image ? `<img src="${image}" class="wp-featured-image"/>` : ''}
            <div class="wp-content">
                <h2>${header || 'Post Title'}</h2>
                <div class="wp-meta">Published just now by ${label}</div>
                <p>${body || 'Your content will appear here...'}</p>
            </div>
        </div>
    `;
}

/* function renderReddit(label, username, header, body) {
    return `
        <div class="reddit-post">
            <div class="reddit-header">
                <div class="reddit-avatar"></div>
                <div>
                    <div class="reddit-user">${label}</div>
                    <div class="reddit-handle">${username}</div>
                </div>
            </div>
            <div class="reddit-title">${header || 'Post title'}</div>
            <div class="reddit-body">${body || 'Your post content...'}</div>
            <div class="reddit-actions">
                <span>▲</span><span>▼</span><span>💬</span><span>🔗</span>
            </div>
        </div>
    `;
}*/

function renderLinkedIn(label, username, header, body, image) {
    const content = [header, body]
        .filter(Boolean)
        .join('<br>');

    return `
        <div class="linkedin-post">
            <div class="linkedin-top">
                <div class="linkedin-avatar">
                    ${label ? label.charAt(0).toUpperCase() : 'L'}
                </div>

                <div class="linkedin-user-info">
                    <div class="linkedin-name-row">
                        <span class="linkedin-name">${label || 'LinkedIn User'}</span>
                        <span class="linkedin-you">• You</span>
                    </div>

                    <div class="linkedin-headline">
                        ${username || '@linkedin-user'}
                    </div>

                    <div class="linkedin-meta">
                        now • public
                    </div>
                </div>

                <button class="linkedin-menu" aria-label="More">
                    <svg viewBox="0 0 24 24">
                        <circle cx="5" cy="12" r="2"></circle>
                        <circle cx="12" cy="12" r="2"></circle>
                        <circle cx="19" cy="12" r="2"></circle>
                    </svg>
                </button>
            </div>

            <div class="linkedin-content">
                <p>${content || 'Start writing your LinkedIn post...'}</p>
                ${image ? `<img src="${image}" class="linkedin-image"/>` : ''}
            </div>

            <div class="linkedin-actions">
                <button class="linkedin-action-btn" aria-label="Like">
                    <svg viewBox="0 0 24 24">
                        <path d="M7 10v11H3V10h4Zm2 11V10.5l4.4-7.2c.4-.7 1.4-.9 2-.3.5.5.7 1.2.5 1.9L15 9h4.5c1.5 0 2.6 1.4 2.2 2.8l-1.6 6.5A3 3 0 0 1 17.2 21H9Z"/>
                    </svg>
                    <span>Like</span>
                </button>

                <button class="linkedin-action-btn" aria-label="Comment">
                    <svg viewBox="0 0 24 24">
                        <path d="M12 4C7 4 3 7.6 3 12c0 2.2 1 4.1 2.7 5.6L5 21l3.7-1.8c1.1.3 2.2.5 3.3.5 5 0 9-3.6 9-8S17 4 12 4Zm0 2c3.9 0 7 2.7 7 6s-3.1 6-7 6c-1.1 0-2.1-.2-3-.6l-.4-.2-1.9.9.4-1.8-.6-.5C5.5 14.8 5 13.4 5 12c0-3.3 3.1-6 7-6Z"/>
                    </svg>
                    <span>Comment</span>
                </button>

                <button class="linkedin-action-btn" aria-label="Repost">
                    <svg viewBox="0 0 24 24">
                        <path d="M7 7h9.2l-2.1-2.1a1 1 0 0 1 1.4-1.4l3.8 3.8a1 1 0 0 1 0 1.4l-3.8 3.8a1 1 0 1 1-1.4-1.4L16.2 9H7a3 3 0 0 0-3 3v1H2v-1a5 5 0 0 1 5-5Zm10 10H7.8l2.1 2.1a1 1 0 0 1-1.4 1.4l-3.8-3.8a1 1 0 0 1 0-1.4l3.8-3.8a1 1 0 1 1 1.4 1.4L7.8 15H17a3 3 0 0 0 3-3v-1h2v1a5 5 0 0 1-5 5Z"/>
                    </svg>
                    <span>Repost</span>
                </button>

                <button class="linkedin-action-btn" aria-label="Send">
                    <svg viewBox="0 0 24 24">
                        <path d="M3.4 20.4 21 3l-4.5 18-5.2-7.2L3.4 20.4Zm5.1-5.9 3.3-2.8 2.9 4 2.3-9.1-8.5 7.9Z"/>
                    </svg>
                    <span>Send</span>
                </button>
            </div>
        </div>
    `;
}

function renderBluesky(label, username, header, body, image) {
    const content = [header, body].filter(Boolean).join('\n');
    const avatarLetter = label ? label.charAt(0).toUpperCase() : 'B';

    return `
        <div class="bluesky-post">
            <div class="bluesky-avatar">
                ${avatarLetter}
            </div>

            <div class="bluesky-main">
                <div class="bluesky-header">
                    <div class="bluesky-user">
                        <span class="bluesky-name">${label || 'Bluesky User'}</span>
                        <span class="bluesky-handle">${username || '@user.bsky.social'} · now</span>
                    </div>

                    <button class="bluesky-icon-btn" aria-label="More">
                        <svg viewBox="0 0 24 24">
                            <circle cx="5" cy="12" r="2"></circle>
                            <circle cx="12" cy="12" r="2"></circle>
                            <circle cx="19" cy="12" r="2"></circle>
                        </svg>
                    </button>
                </div>

                <div class="bluesky-content">
                    <p>${content || '¿Qué hay de nuevo?'}</p>

                    ${
                        image
                            ? `
                                <div class="bluesky-image-wrapper">
                                    <img src="${image}" class="bluesky-image" />
                                </div>
                            `
                            : ''
                    }
                </div>

                <div class="bluesky-actions">
                    <button class="bluesky-action-btn" aria-label="Reply">
                        <svg viewBox="0 0 24 24">
                            <path d="M12 4C7.03 4 3 7.58 3 12c0 2.03.86 3.88 2.27 5.29-.17.83-.54 1.85-1.21 2.71a.75.75 0 0 0 .75 1.18c1.44-.31 2.73-.96 3.72-1.65A10.4 10.4 0 0 0 12 20c4.97 0 9-3.58 9-8s-4.03-8-9-8Z"></path>
                        </svg>
                    </button>

                    <button class="bluesky-action-btn" aria-label="Repost">
                        <svg viewBox="0 0 24 24">
                            <path d="M7 7h9.2l-2.1-2.1a1 1 0 0 1 1.4-1.4l3.8 3.8a1 1 0 0 1 0 1.4l-3.8 3.8a1 1 0 1 1-1.4-1.4L16.2 9H7a3 3 0 0 0-3 3v1a1 1 0 1 1-2 0v-1a5 5 0 0 1 5-5Zm10 10H7.8l2.1 2.1a1 1 0 0 1-1.4 1.4l-3.8-3.8a1 1 0 0 1 0-1.4l3.8-3.8a1 1 0 1 1 1.4 1.4L7.8 15H17a3 3 0 0 0 3-3v-1a1 1 0 1 1 2 0v1a5 5 0 0 1-5 5Z"></path>
                        </svg>
                    </button>

                    <button class="bluesky-action-btn" aria-label="Like">
                        <svg viewBox="0 0 24 24">
                            <path d="M12 21s-7.5-4.35-9.6-9.02C.92 8.68 2.43 5 5.93 5c2.03 0 3.36 1.13 4.07 2.05C10.64 5.98 12 5 14.07 5c3.5 0 5.51 3.68 3.99 6.98C15.85 16.65 12 21 12 21Z"></path>
                        </svg>
                    </button>

                    <button class="bluesky-action-btn" aria-label="Bookmark">
                        <svg viewBox="0 0 24 24">
                            <path d="M7 4a2 2 0 0 0-2 2v16l7-4 7 4V6a2 2 0 0 0-2-2H7Zm0 2h10v12.55l-5-2.86-5 2.86V6Z"></path>
                        </svg>
                    </button>

                    <button class="bluesky-action-btn" aria-label="Share">
                        <svg viewBox="0 0 24 24">
                            <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7a3.3 3.3 0 0 0 0-1.39l7.05-4.11A3 3 0 1 0 15 5c0 .23.03.45.08.66L8.03 9.77a3 3 0 1 0 0 4.46l7.12 4.16c-.05.2-.08.41-.08.62a3 3 0 1 0 3-2.92Z"></path>
                        </svg>
                    </button>

                    <button class="bluesky-action-btn" aria-label="More actions">
                        <svg viewBox="0 0 24 24">
                            <circle cx="5" cy="12" r="2"></circle>
                            <circle cx="12" cy="12" r="2"></circle>
                            <circle cx="19" cy="12" r="2"></circle>
                        </svg>
                    </button>
                </div>
            </div>
        </div>
    `;
}


function updatePreview() {
    const header = escapeHTML(document.getElementById('post-header').value);
    const body = escapeHTML(document.getElementById('post-body').value);
    const container = document.getElementById('preview-container');
    container.innerHTML = '';

    const selectedAccounts = getSelectedAccountsPayload();

    selectedAccounts.forEach((account) => {
        const provider = account.provider ?? account[0];
        const username = escapeHTML(account.username ?? account[1] ?? '');
        const label = escapeHTML(getAccountLabel(provider, username)) || username;  

        let contentHTML = '';
        const image = currentImage;

        if (provider === 'Mastodon') {
            contentHTML = renderMastodon(label, username, header, body, image);
        } else if (provider === 'WordPress') {
            contentHTML = renderWordPress(label, username, header, body, image);
        /*} else if (provider === 'Reddit') {
            contentHTML = renderReddit(label, username, header, body);*/
        } else if (provider === 'WordPressREST') {
            contentHTML = renderWordPress(label, username, header, body, image);
        } else if (provider == 'Bluesky'){
            contentHTML = renderBluesky(label, username, header, body, image);
        } else if (provider === 'LinkedIn') {
            contentHTML = renderLinkedIn(label, username, header, body, image);
        } else {
            contentHTML = `
                <div class="generic-preview">
                    <div class="generic-preview-header">
                        ${header || 'Untitled Post'}
                    </div>

                    <div class="generic-preview-body">
                        <span>${body || 'Start writing your content...'}</span>
                    </div>

                    ${image? `
                            <div class="generic-preview-image-wrapper">
                                <img
                                    src="${image}"
                                    class="generic-preview-image"
                                />
                            </div>
                        `: ''
                    }
                </div>
            `;
        }

        const card = document.createElement('div');
        card.className = 'preview-card-social';
        card.innerHTML = `
            <div class="preview-platform">${provider} • ${label}</div>
            ${contentHTML}
        `;
        container.appendChild(card);
    });
}


function showPublishResults(results) {
    publishResults = results || [];
    const statusBar = document.getElementById('publish-status-bar');
    const statusText = document.getElementById('publish-status-text');

    const hasErrors = publishResults.some(r => !r.success);

    statusBar.classList.remove('hidden');

    statusText.textContent = hasErrors
        ? 'Some posts failed'
        : 'Published successfully';

    statusText.className =
        `status-text ${hasErrors ? 'error' : 'success'}`;

    const list = document.getElementById('publish-details-list');

    list.innerHTML = '';

    const styles = {
        Mastodon: 'icons/Mastodon_logo.png',
        WordPress: 'icons/WordPress_logo.png',
        WordPressREST: 'icons/WordPress_logo.png',
        Bluesky: 'icons/Bluesky_logo.png',
        LinkedIn: 'icons/LinkedIn_logo.png'
    };

    const sorted = [
        ...publishResults.filter(r => !r.success),
        ...publishResults.filter(r => r.success)
    ];

    sorted.forEach(result => {
        const icon = styles[result.provider]
            || 'icons/default.png';

        list.innerHTML += `
            <div class="publish-detail-item ${result.success ? 'success' : 'error'}">
                <div class="publish-detail-icon">
                    <img src="${icon}">
                </div>

                <div class="publish-detail-content">
                    <div class="publish-detail-title">
                        ${result.provider}
                    </div>
                    <div class="publish-detail-message">
                        ${escapeHTML(String(result.message || '').trim())}
                    </div>
                </div>
            </div>
        `;
    });
}


async function createPost() {
    const header = document.getElementById('post-header').value.trim();
    const body = document.getElementById('post-body').value.trim();
    const selectedAccounts = getSelectedAccountsPayload();
    
    if (!header && !body) {
        showStatus('Please add a header or body to your post', 'error');
        return;
    }

    if (selectedAccounts.length === 0) {
        showStatus('Select at least one account before publishing', 'error');
        return;
    }

    /*const hasReddit = selectedAccounts.some((account) => {
        const provider = account.provider ?? account[0];
        return provider === 'Reddit';
    });

    if (hasReddit && !header) {
        showStatus('Reddit requires a header title', 'error');
        return;
    }*/
    
    if (header.length + body.length > 299) {
        showStatus('Header and body exceeds 299 character limit', 'error');
        return;
    }

    const fileInput = document.getElementById('image-input');
    let imageData = null;
    let imageName = null;

    if (fileInput.files.length > 0) {
        const file = fileInput.files[0];
        imageName = file.name;
        const reader = new FileReader();
        reader.readAsDataURL(file);
        await new Promise((resolve) => {
            reader.onload = () => {
                imageData = reader.result;
                resolve();
            };
        });
    }

    publishResults = [];

    const statusText = document.getElementById('publish-status-text');
    const detailsList = document.getElementById('publish-details-list');
    statusText.textContent = 'Ready';
    statusText.className = 'status-text';
    detailsList.innerHTML = '';
    
    showStatus('Creating post...', 'info');
    const result = await eel.create_post(header, body, imageData, imageName, selectedAccounts)();

    if (result && result.results && result.results.length > 0) {
        showPublishResults(result.results);
        const hasErrors = result.results.some(r => !r.success);
        showStatus(
            hasErrors
                ? 'Some posts failed'
                : 'Post published successfully',
            hasErrors ? 'error' : 'success'
        );

        if (!hasErrors) {
            clearForm();
        }

    } else {
        publishResults = [{
            provider: 'System',
            success: false,
            message: result?.message || 'Unknown publish error'
        }];

        showPublishResults(publishResults);

        showStatus(
            'Failed to publish post',
            'error'
        );
    }
}

function initializeEventListeners() {
    document.getElementById('post-header').addEventListener('input', () => {
        updateCounters();
        updatePreview();
    });
    
    document.getElementById('post-body').addEventListener('input', () => {
        updateCounters();
        updatePreview();
    });

    document.getElementById('account-list').addEventListener('change', (event) => {
        const target = event.target;
        if (target.id === 'toggle-visible-accounts') {
            const accounts = getAccountsForActiveTab();
            accounts.forEach(({ provider, username }) => {
                const key = accountKey(provider, username);
                if (target.checked) {
                    accountState.selected.add(key);
                } else {
                    accountState.selected.delete(key);
                }
            });
            renderAccountList();
            updatePreview();
            return;
        }
        if (target.matches('input[type="checkbox"][data-provider][data-username]')) {
            const provider = target.getAttribute('data-provider');
            const username = target.getAttribute('data-username');
            const key = accountKey(provider, username);
            if (target.checked) {
                accountState.selected.add(key);
            } else {
                accountState.selected.delete(key);
            }
            renderAccountList();
            updatePreview();
        }
    });

    document.getElementById('account-list').addEventListener('click', async (e) => {
        const deleteBtn = e.target.closest('.delete-account-btn');
        const labelBtn = e.target.closest('.edit-label-btn');

        if (deleteBtn) {
            e.stopPropagation();
            e.preventDefault();

            const provider = deleteBtn.dataset.provider;
            const username = deleteBtn.dataset.username;

            const confirmed = await openModal({
                title: "Delete account",
                bodyHTML: `<p>Are you sure you want to remove <b>${username}</b>?</p>`,
                confirmText: "Delete",
                danger: true
            });

            if (!confirmed) return;

            try {
                const result = await eel.delete_account(provider, username)();

                if (result && result.success) {
                    const key = accountKey(provider, username);
                    accountState.selected.delete(key);

                    await loadAccounts();
                    showStatus('Account deleted successfully', 'success');
                } else {
                    showStatus(result?.message || 'Error deleting account', 'error');
                }

            } catch (err) {
                showStatus('Error: ' + err, 'error');
            }
        }

        if (labelBtn) {
            e.stopPropagation();

            const provider = labelBtn.dataset.provider;
            const username = labelBtn.dataset.username;

            const currentLabel = getAccountLabel(provider, username);

            const confirmed = await openModal({
                title: "Edit account label",
                bodyHTML: `<input id="edit-input" value="${currentLabel || username}">`,
                confirmText: "Save"
            });

            if (!confirmed) return;

            const input = document.getElementById('edit-input');
            const newLabel = input.value.trim();

            if (!newLabel) return;

            try {
                const result = await eel.update_display_name(provider, username, newLabel)();

                if (result && result.success) {
                    updateAccountLabel(provider, username, newLabel || null);
                    renderAccountList();
                    updatePreview();
                    showStatus('Label updated', 'success');
                } else {
                    showStatus(result?.message || 'Failed to update label', 'error');
                }

            } catch (err) {
                showStatus('Error: ' + err, 'error');
            }
        }
    });

    const publishOverlay = document.getElementById('publish-details-overlay');
    const publishModal = document.getElementById('publish-details-modal');

    document.getElementById('open-status-details')
        .addEventListener('click', () => {
            publishOverlay.classList.add('active');
            publishOverlay.classList.remove('hidden');
            publishModal.classList.add('active');
    });

    function closePublishModal() {
        publishOverlay.classList.remove('active');
        publishOverlay.classList.add('hidden');
        publishModal.classList.remove('active');
    }

    document.getElementById('close-publish-details').addEventListener('click', closePublishModal);
    publishOverlay.addEventListener('click', closePublishModal);

    window.addEventListener('resize', syncSidebarHeight);
}
function initializeApplication() {
    initializeEventListeners();
    updateCounters();
    updatePreview();
    loadAccounts();
    syncSidebarHeight();
}

initializeApplication();

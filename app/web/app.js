const fileInput = document.getElementById('image-input');
const fileName = document.getElementById('file-name');
const overlay = document.getElementById('overlay');
let currentImage = null;

const accountState = {
    accountsByProvider: {},
    selected: new Set(),
    activeTab: 'Todas',
    hasLoaded: false,
    collapsedProviders: new Set()
};


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
const redditToggle = document.getElementById('toggle-reddit-form');
const mastodonForm = document.getElementById('mastodon-form');
const wordpressForm = document.getElementById('wordpress-form');
const blueskyForm = document.getElementById('bluesky-form');
const redditForm = document.getElementById('reddit-form');

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

redditToggle.addEventListener('click', () => {
    redditForm.classList.toggle('hidden-form');
    const icon = redditToggle.querySelector('.expand-icon');
    icon.textContent = redditForm.classList.contains('hidden-form') ? '▼' : '▲';
});

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

// Reddit: Link account
document.getElementById('link-reddit-btn').addEventListener('click', async () => {
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
});

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
    const statusDiv = document.getElementById('status');
    statusDiv.textContent = message;
    statusDiv.className = `status ${type}`;
    statusDiv.classList.remove('hidden');
    
    setTimeout(() => {
        statusDiv.classList.add('hidden');
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
    console.log(accounts);

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
            Bluesky: { icon: 'icons/Bluesky_logo.png', border: '#1184FE' },
            Reddit: { icon: 'icons/default.png', border: '#ff4500' }
        };
        const data = styles[provider] || { icon: 'icons/default.png', border: '#FF80FF' };
        const displayName = provider.charAt(0).toUpperCase() + provider.slice(1);

        html += `
            <div class="provider-group">
                <div class="provider-header" data-provider="${provider}">
                    
                    <div class="provider-left">
                        <div class="provider-icon" style="border: 2px solid ${data.border}">
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

                    <button class="edit-label-btn"
                        data-provider="${provider}"
                        data-username="${username}"
                        title="Edit label">✎</button>

                    <button class="delete-account-btn"
                        data-provider="${provider}"
                        data-username="${username}"
                        title="Delete account">x</button>
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
        console.log(grouped);
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
    return `
        <div class="mastodon-post">
            <div class="mastodon-top">
                <div class="avatar"></div>
                <div class="mastodon-user">
                    <div class="name">${label}</div>
                    <div class="handle">${username}</div>
                </div>
                <div class="mastodon-time">now</div>
            </div>
            <div class="mastodon-content">
                <p>${content || 'Your post content...'}</p>
                ${image ? `<img src="${image}" class="mastodon-image"/>` : ''}
            </div>
            <div class="mastodon-actions">
                <span>💬</span><span>🔁</span><span>⭐</span><span>🔖</span>
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

function renderReddit(label, username, header, body) {
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
}

// Por cada red, se debe hacer una funcion con la estructura anterior 
// funtion render/NombreRed/(account, header, body, image)
// Y en estas se pone la estructura del HTML específico de la red y se 
// tiene que también añadir el css correspondiente

function updatePreview() {
    const header = document.getElementById('post-header').value;
    const body = document.getElementById('post-body').value;
    const container = document.getElementById('preview-container');
    container.innerHTML = '';

    const selectedAccounts = getSelectedAccountsPayload();

    selectedAccounts.forEach((account) => {
        const provider = account.provider ?? account[0];
        const username = account.username ?? account[1];
        const label = getAccountLabel(provider, username) || username;  

        let contentHTML = '';
        const image = currentImage;

        if (provider === 'Mastodon') {
            contentHTML = renderMastodon(label, username, header, body, image);
        } else if (provider === 'WordPress') {
            contentHTML = renderWordPress(label, username, header, body, image);
        } else if (provider === 'Reddit') {
            contentHTML = renderReddit(label, username, header, body);
        } else {
            contentHTML = `
                <div class="preview-card-social">
                    <div>${header || 'Title'}</div>
                    <div>${body || 'Content...'}</div>
                    ${image ? `<img src="${image}" />` : ''}
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

    const hasReddit = selectedAccounts.some((account) => {
        const provider = account.provider ?? account[0];
        return provider === 'Reddit';
    });

    if (hasReddit && !header) {
        showStatus('Reddit requires a header title', 'error');
        return;
    }
    
    if (header.length > 100) {
        showStatus('Header exceeds 100 characters', 'error');
        return;
    }
    
    if (body.length > 500) {
        showStatus('Body exceeds 500 characters', 'error');
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
    
    showStatus('Creating post...', 'info');
    const result = await eel.create_post(header, body, imageData, imageName, selectedAccounts)();

    if (result && result.success) {
        showStatus(result.message || 'Post published successfully', 'success');
        clearForm();
        return;
    }
    showStatus((result && result.message) || 'Error publishing post', 'error');
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

document.addEventListener("DOMContentLoaded", () => {
    // --- DOM ELEMENTS ---
    const chatOutput = document.getElementById("chat-output");
    const chartTabs = document.getElementById("chart-tabs");
    const kundliImg = document.getElementById("kundli-img");
    const kundliSkeleton = document.getElementById("kundli-skeleton");
    const dashaBody = document.getElementById("dasha-body");
    const systemStatus = document.getElementById("system-status");
    const sendBtn = document.getElementById("send-btn");
    const questionInput = document.getElementById("question");
    const domainPicker = document.getElementById("domain-picker");
    const domainPickerSummary = document.getElementById("domain-picker-summary");
    const domainPickerHelp = document.getElementById("domain-picker-help");
    const domainCheckboxes = Array.from(document.querySelectorAll('input[name="question-domain"]'));

    function selectedQuestionDomains() {
        return domainCheckboxes.filter(input => input.checked).map(input => input.value);
    }

    function refreshDomainPicker() {
        const selected = selectedQuestionDomains();
        domainPickerSummary.textContent = selected.length
            ? `Question tags (${selected.length} selected)`
            : "Choose question tags (required)";
        domainPickerHelp.classList.remove("error");
        domainPickerHelp.textContent = selected.length
            ? `Selected: ${selected.map(tag => tag.replaceAll("_", " ")).join(", ")}`
            : "Pick one or more tags so the chart and knowledge lookup focus on the right topics.";
    }

    domainCheckboxes.forEach(input => input.addEventListener("change", () => {
        if (input.value === "general" && input.checked) {
            domainCheckboxes.filter(item => item !== input).forEach(item => { item.checked = false; });
        } else if (input.checked) {
            const general = domainCheckboxes.find(item => item.value === "general");
            if (general) general.checked = false;
        }
        refreshDomainPicker();
    }));
    window.chooseQuestionDomains = domains => {
        domainCheckboxes.forEach(input => { input.checked = domains.includes(input.value); });
        refreshDomainPicker();
    };

    // Sidebar & Navigation
    const sidebar = document.getElementById("sidebar");
    const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
    const closeSidebarBtn = document.getElementById("close-sidebar-btn");
    const visualPanel = document.getElementById("visual-panel");
    const analysisToggleBtn = document.getElementById("analysis-toggle-btn");
    const closeMenuBtn = document.getElementById("close-menu-btn");
    const sidebarOverlay = document.getElementById("sidebar-overlay");
    const sidebarUsername = document.getElementById("sidebar-username");
    const logoutBtn = document.getElementById("logout-btn");
    const profileListContainer = document.getElementById("profile-list-container");
    const addProfileBtn = document.getElementById("add-profile-btn");

    // Modals
    const authModal = document.getElementById("auth-modal");
    const profileModal = document.getElementById("profile-modal");
    const closeModalBtn = document.getElementById("close-modal-btn");
    const saveProfileBtn = document.getElementById("save-profile-btn");
    const emptyChatState = document.getElementById("empty-chat-state");
    const emptyCreateBtn = document.getElementById("empty-create-btn");

    // Form Fields (Modal)
    const seekerNameInp = document.getElementById("seeker-name");
    const genderInp = document.getElementById("gender");
    const locInp = document.getElementById("location-input");
    const latInp = document.getElementById("lat");
    const lonInp = document.getElementById("lon");
    const tzInp = document.getElementById("tz");
    const dy = document.getElementById("dob-year"), dm = document.getElementById("dob-month"), dd = document.getElementById("dob-day");
    const dh = document.getElementById("dob-hour"), dmin = document.getElementById("dob-minute"), ampmInp = document.getElementById("dob-ampm");

    // Context Menu
    const contextMenu = document.getElementById("profile-context-menu");
    const ctxLoadBtn = document.getElementById("ctx-load-profile");
    const ctxDeleteBtn = document.getElementById("ctx-delete-profile");

    // --- STATE ---
    let jwtToken = localStorage.getItem("astra_auth_token");
    let currentProfile = null;
    let profilesCache = [];
    let activeContextMenuProfile = null;
    let currentSessionId = null;
    let sessionsCache = [];

    // --- INITIALIZATION ---
    populateDropdowns();
    checkAuth();

    // --- AUTHENTICATION ---
    async function secureFetch(url, options = {}) {
        const headers = { "Content-Type": "application/json", ...options.headers };
        if (jwtToken) headers["Authorization"] = `Bearer ${jwtToken}`;
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) { handleLogout(); throw new Error("Session expired"); }
        return response;
    }

    async function checkAuth() {
        if (!jwtToken) { showAuthModal("login"); return; }
        try {
            const res = await secureFetch("/api/me");
            const data = await res.json();
            if (data.username) {
                sidebarUsername.innerText = data.username;
                authModal.style.display = "none";

                // Fetch Settings
                const settingsRes = await secureFetch("/api/settings");
                const settings = await settingsRes.json();
                if (settings.preferred_language) {
                    document.getElementById("preferred-language").value = settings.preferred_language;
                }

                refreshProfileList();
            } else { handleLogout(); }
        } catch (e) { handleLogout(); }
    }

    function handleLogout() {
        console.log("Logging out...");
        localStorage.clear(); // Clear all to be safe
        jwtToken = null;
        window.location.href = "/"; // Force redirect to root
    }

    function showAuthModal(type) {
        authModal.style.display = "flex";
        const signupForm = document.getElementById("signup-form");
        const loginForm = document.getElementById("login-form");
        if (type === "signup") {
            loginForm.style.display = "none";
            signupForm.style.display = "block";
            document.getElementById("auth-title").innerText = "Join KaalDrishti";
        } else {
            loginForm.style.display = "block";
            signupForm.style.display = "none";
            document.getElementById("auth-title").innerText = "Welcome Back";
        }
    }

    // --- PROFILE MANAGEMENT ---
    async function refreshProfileList() {
        try {
            const res = await secureFetch("/api/profiles");
            profilesCache = await res.json();
            renderProfileList(profilesCache);

            if (profilesCache.length === 0) {
                emptyChatState.style.display = "flex";
            } else {
                emptyChatState.style.display = "none";
                // If no profile active, load from localStorage or the first one
                if (!currentProfile) {
                    const lastProfile = localStorage.getItem("astra_last_profile");
                    const profileToLoad = lastProfile && profilesCache.find(p => p.seeker_name === lastProfile)
                        ? lastProfile
                        : profilesCache[0].seeker_name;
                    loadProfile(profileToLoad);
                }
            }
        } catch (e) {
            console.error("Failed to fetch profiles", e);
        }
    }

    function renderProfileList(profiles) {
        profileListContainer.innerHTML = "";
        profiles.forEach(p => {
            const item = document.createElement("div");
            item.className = "profile-item-wrapper";

            // Main profile row (clickable to toggle sessions)
            const row = document.createElement("div");
            row.className = "profile-item";
            if (currentProfile && currentProfile.seeker_name === p.seeker_name) {
                row.style.borderColor = "var(--gold-accent)";
                row.style.background = "rgba(255, 184, 108, 0.05)";
            }

            // Get sessions for this profile
            const profileSessions = sessionsCacheByProfile[p.seeker_name] || [];
            const isExpanded = expandedProfiles[p.seeker_name] || false;

            row.innerHTML = `
                <div class="profile-info">
                    <span class="profile-name">${p.seeker_name}</span>
                    <span class="profile-sub">${p.gender} | ${new Date(p.local_time.split(' ')[0]).toLocaleDateString()}</span>
                </div>
                <div class="profile-actions">
                    <button class="profile-expand-btn" data-name="${p.seeker_name}">${isExpanded ? '▾' : '▸'}</button>
                    <button class="profile-actions-btn" data-name="${p.seeker_name}">⋮</button>
                </div>
            `;

            // Toggle expand on profile click
            row.onclick = (e) => {
                if (e.target.classList.contains('profile-actions-btn')) return;
                if (e.target.classList.contains('profile-expand-btn')) return;
                // Toggle expansion
                expandedProfiles[p.seeker_name] = !expandedProfiles[p.seeker_name];
                renderProfileList(profilesCache);
            };

            // Expand button click
            const expandBtn = row.querySelector('.profile-expand-btn');
            expandBtn.onclick = (e) => {
                e.stopPropagation();
                expandedProfiles[p.seeker_name] = !expandedProfiles[p.seeker_name];
                renderProfileList(profilesCache);
            };

            // 3-Dot Menu
            const actionBtn = row.querySelector('.profile-actions-btn');
            const openMenu = (e) => {
                e.stopPropagation();
                e.preventDefault();
                showContextMenu(e, p.seeker_name);
            };
            actionBtn.addEventListener('click', openMenu);
            actionBtn.addEventListener('touchend', openMenu, { passive: false });

            item.appendChild(row);

            // Sessions container (expandable)
            const sessionsContainer = document.createElement("div");
            sessionsContainer.className = "profile-sessions-container";
            sessionsContainer.style.display = isExpanded ? 'block' : 'none';
            sessionsContainer.id = `sessions-for-${p.seeker_name}`;

            if (isExpanded) {
                // Load sessions if not already loaded
                if (!sessionsCacheByProfile[p.seeker_name]) {
                    // Fetch and render sessions
                    loadSessionsForProfile(p.seeker_name).then(() => {
                        // Re-render to show sessions
                        renderProfileList(profilesCache);
                    });
                } else {
                    // Render sessions
                    const sessionList = document.createElement("div");
                    sessionList.className = "profile-session-list";
                    const profileSessions = sessionsCacheByProfile[p.seeker_name] || [];

                    if (profileSessions.length === 0) {
                        const emptyMsg = document.createElement("div");
                        emptyMsg.className = "profile-sessions-empty";
                        emptyMsg.textContent = "No sessions yet. Start a new chat!";
                        sessionList.appendChild(emptyMsg);
                    } else {
                        profileSessions.forEach(s => {
                            const sessItem = document.createElement("div");
                            sessItem.className = "profile-session-item" + (currentSessionId === s.id ? " active" : "");
                            sessItem.innerHTML = `
                                <span class="profile-session-title">${s.session_title || "New Chat"}</span>
                                <span class="profile-session-time">${new Date(s.updated_at).toLocaleDateString()}</span>
                                <button class="profile-session-delete-btn" data-id="${s.id}">✕</button>
                            `;
                            sessItem.onclick = (e) => {
                                if (e.target.classList.contains('profile-session-delete-btn')) return;
                                // Load this session
                                currentSessionId = s.id;
                                localStorage.setItem("astra_last_session", s.id.toString());
                                loadSessionHistory(s.id);
                                // Update UI
                                renderProfileList(profilesCache);
                            };
                            const delBtn = sessItem.querySelector('.profile-session-delete-btn');
                            delBtn.onclick = (e) => {
                                e.stopPropagation();
                                deleteSessionForProfile(s.id, p.seeker_name);
                            };
                            sessionList.appendChild(sessItem);
                        });
                    }

                    // New chat button for this profile
                    const newChatBtn = document.createElement("button");
                    newChatBtn.className = "profile-new-chat-btn";
                    newChatBtn.textContent = "+ New Chat";
                    newChatBtn.onclick = (e) => {
                        e.stopPropagation();
                        createNewSessionForProfile(p.seeker_name);
                    };
                    sessionList.appendChild(newChatBtn);

                    sessionsContainer.appendChild(sessionList);
                }
            }

            item.appendChild(sessionsContainer);
            profileListContainer.appendChild(item);
        });
    }

    // Store sessions per profile
    let sessionsCacheByProfile = {};
    let expandedProfiles = {};

    async function loadSessionsForProfile(profileName) {
        try {
            const res = await secureFetch(`/api/sessions?profile_name=${encodeURIComponent(profileName)}`);
            const sessions = await res.json();
            sessionsCacheByProfile[profileName] = sessions;
            return sessions;
        } catch (e) {
            console.error("Failed to load sessions for profile", e);
            sessionsCacheByProfile[profileName] = [];
            return [];
        }
    }

    async function createNewSessionForProfile(profileName) {
        try {
            const res = await secureFetch("/api/sessions", {
                method: "POST",
                body: JSON.stringify({ profile_name: profileName, session_title: "New Chat" })
            });
            const data = await res.json();
            if (!sessionsCacheByProfile[profileName]) {
                sessionsCacheByProfile[profileName] = [];
            }
            sessionsCacheByProfile[profileName].unshift(data);
            currentSessionId = data.id;
            localStorage.setItem("astra_last_session", data.id.toString());
            // Expand this profile
            expandedProfiles[profileName] = true;
            renderProfileList(profilesCache);
            showEmptyChatState(profileName);
            return data;
        } catch (e) {
            console.error("Failed to create session", e);
            return null;
        }
    }

    async function deleteSessionForProfile(sessionId, profileName) {
        if (!confirm("Delete this chat session?")) return;
        try {
            await secureFetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
            if (sessionsCacheByProfile[profileName]) {
                sessionsCacheByProfile[profileName] = sessionsCacheByProfile[profileName].filter(s => s.id !== sessionId);
            }
            if (currentSessionId === sessionId) {
                currentSessionId = null;
                localStorage.removeItem("astra_last_session");
            }
            renderProfileList(profilesCache);
        } catch (e) {
            alert("Failed to delete session: " + e.message);
        }
    }

    async function loadProfile(profileName) {
        const profile = profilesCache.find(p => p.seeker_name === profileName);
        if (!profile) return;

        currentProfile = profile;
        currentSessionId = null;
        localStorage.setItem("astra_last_profile", profileName);

        // Expand this profile in the sidebar
        expandedProfiles[profileName] = true;
        renderProfileList(profilesCache); // Update active state in UI

        // 1. Clear UI
        chatOutput.innerHTML = '<div class="message system-msg">Synchronizing with ' + profileName + '\'s celestial alignment...</div>';
        dashaBody.innerHTML = "";
        chartTabs.innerHTML = "";
        kundliImg.style.display = "none";
        kundliSkeleton.style.display = "block";
            document.getElementById("person-section").innerHTML = '<div class="no-selection-msg">Synthesizing charts...</div>';
            document.getElementById("analysis-cards").style.display = "none";

        // 2. Load Sessions for this profile
        const sessions = await loadSessionsForProfile(profileName);

        // Load the last session or create a new one
        if (sessions && sessions.length > 0) {
            // Try to restore last session from localStorage
            const lastSessionId = localStorage.getItem("astra_last_session");
            let sessionToLoad = null;
            if (lastSessionId) {
                sessionToLoad = sessions.find(s => s.id === parseInt(lastSessionId));
            }
            if (!sessionToLoad) {
                sessionToLoad = sessions[0];
            }
            currentSessionId = sessionToLoad.id;
            localStorage.setItem("astra_last_session", sessionToLoad.id.toString());
            loadSessionHistory(sessionToLoad.id);
        } else {
            // No sessions, create one
            await createNewSessionForProfile(profileName);
        }

        // Re-render to show sessions
        renderProfileList(profilesCache);

        // 3. Hydrate Charts/Panels
        try {
            const mRes = await secureFetch(`/api/chart_matrix?profile=${encodeURIComponent(profileName)}`);
            const mData = await mRes.json();
            if (mData.status === "success" && mData.deterministic_astronomy) {
                const astro = mData.deterministic_astronomy;
                renderTabs(astro.divisional_charts);
                renderDasha(astro.dasha_timeline);
                renderPersonalDetails(astro, currentProfile);
                renderFullAnalysis(mData);
            }
        } catch (e) { console.warn("Charts failed", e); }
    }

    async function deleteProfile(name) {
        if (!confirm(`Are you sure you want to permanently delete ${name}'s profile and all associated chat history?`)) return;
        try {
            const res = await secureFetch(`/api/profiles/${encodeURIComponent(name)}`, { method: "DELETE" });
            const data = await res.json();
            if (data.status === "success") {
                if (currentProfile && currentProfile.seeker_name === name) currentProfile = null;
                currentSessionId = null;
                // Clear per-profile cache
                delete sessionsCacheByProfile[name];
                delete expandedProfiles[name];
                refreshProfileList();
            }
        } catch (e) { alert("Deletion failed: " + e.message); }
    }

    // --- PROFILE MEMORY FUNCTIONS ---
    let memoryCache = [];

    async function loadMemory(profileName) {
        try {
            const res = await secureFetch(`/api/profile_memory?profile_name=${encodeURIComponent(profileName)}`);
            memoryCache = await res.json();
            renderMemoryList(memoryCache);
        } catch (e) {
            console.error("Failed to load memory", e);
            memoryCache = [];
            renderMemoryList([]);
        }
    }

    function renderMemoryList(memories) {
        const container = document.getElementById("memory-list-container");
        if (!container) return;

        if (!memories || memories.length === 0) {
            container.innerHTML = `<div class="memory-empty">No memories stored for this profile yet. Memories are automatically extracted from conversations.</div>`;
            return;
        }

        container.innerHTML = "";
        memories.forEach(m => {
            const item = document.createElement("div");
            item.className = "memory-item";
            item.innerHTML = `
                <div class="memory-content">
                    <span class="memory-key">${m.key}</span>
                    <span class="memory-value">${m.value}</span>
                    <span class="memory-source">${m.source || 'auto'}</span>
                </div>
                <button class="memory-delete-btn" data-id="${m.id}">✕</button>
            `;
            const deleteBtn = item.querySelector('.memory-delete-btn');
            deleteBtn.onclick = async (e) => {
                e.stopPropagation();
                if (!confirm("Delete this memory?")) return;
                try {
                    await secureFetch(`/api/profile_memory/${m.id}`, { method: "DELETE" });
                    await loadMemory(currentProfile?.seeker_name || "");
                } catch (err) {
                    alert("Failed to delete memory: " + err.message);
                }
            };
            container.appendChild(item);
        });
    }

    async function addMemory(profileName, key, value) {
        if (!key || !value) return alert("Please fill both Key and Value.");
        try {
            await secureFetch("/api/profile_memory", {
                method: "POST",
                body: JSON.stringify({ key: key.trim(), value: value.trim(), source: "user" })
            });
            document.getElementById("memory-key-input").value = "";
            document.getElementById("memory-value-input").value = "";
            await loadMemory(profileName);
        } catch (e) {
            alert("Failed to add memory: " + e.message);
        }
    }

    function openMemoryModal() {
        const modal = document.getElementById("memory-modal");
        if (modal) {
            modal.style.display = "flex";
            if (currentProfile) {
                loadMemory(currentProfile.seeker_name);
            }
        }
    }

    function closeMemoryModal() {
        const modal = document.getElementById("memory-modal");
        if (modal) modal.style.display = "none";
    }

    // --- SESSION MANAGEMENT ---
    async function loadSessions(profileName) {
        try {
            const res = await secureFetch(`/api/sessions?profile_name=${encodeURIComponent(profileName)}`);
            sessionsCache = await res.json();
            renderSessionList(sessionsCache);

            // If no sessions, create one automatically
            if (sessionsCache.length === 0) {
                await createNewSession(profileName);
            } else {
                // Try to restore last session from localStorage
                const lastSessionId = localStorage.getItem("astra_last_session");
                let sessionToLoad = null;
                if (lastSessionId) {
                    sessionToLoad = sessionsCache.find(s => s.id === parseInt(lastSessionId));
                }
                if (!sessionToLoad) {
                    sessionToLoad = sessionsCache[0];
                }
                currentSessionId = sessionToLoad.id;
                localStorage.setItem("astra_last_session", sessionToLoad.id.toString());
                loadSessionHistory(sessionToLoad.id);
            }
            renderSessionList(sessionsCache);
        } catch (e) {
            console.error("Failed to load sessions", e);
        }
    }

    async function createNewSession(profileName) {
        try {
            const res = await secureFetch("/api/sessions", {
                method: "POST",
                body: JSON.stringify({ profile_name: profileName, session_title: "New Chat" })
            });
            const data = await res.json();
            sessionsCache.unshift(data);
            currentSessionId = data.id;
            renderSessionList(sessionsCache);
            showEmptyChatState(profileName);
            return data;
        } catch (e) {
            console.error("Failed to create session", e);
            return null;
        }
    }

    async function loadSessionHistory(sessionId) {
        try {
            const res = await secureFetch(`/api/sessions/${sessionId}/history`);
            const history = await res.json();
            chatOutput.innerHTML = "";
            if (history && history.length > 0) {
                history.forEach(turn => {
                    addMessage(turn.content, turn.role === 'user' ? 'user-msg' : 'agent-msg');
                });
            } else {
                showEmptyChatState(currentProfile?.seeker_name || "");
            }
            currentSessionId = sessionId;
            localStorage.setItem("astra_last_session", sessionId.toString());
            renderSessionList(sessionsCache);
        } catch (e) {
            console.error("Failed to load session history", e);
            showEmptyChatState(currentProfile?.seeker_name || "");
        }
    }

    function showEmptyChatState(profileName) {
        chatOutput.innerHTML = `
            <div class="empty-chat-welcome">
                <div class="welcome-icon">✨</div>
                <h2>Welcome, ${profileName || "Seeker"}</h2>
                <p>Ask me anything about your astrological chart, planetary transits, or life guidance.</p>
                <div class="suggestion-chips">
                    <button class="chip" onclick="window.chooseQuestionDomains(['career']); document.getElementById('question').value='What does my chart say about my career?'; document.getElementById('send-btn').click();">Career Path</button>
                    <button class="chip" onclick="window.chooseQuestionDomains(['general']); document.getElementById('question').value='What are my current planetary transits?'; document.getElementById('send-btn').click();">Current Transits</button>
                    <button class="chip" onclick="window.chooseQuestionDomains(['general']); document.getElementById('question').value='What challenges and opportunities lie ahead for me?';">Life Guidance</button>
                </div>
            </div>
        `;
    }

    function renderSessionList(sessions) {
        const sessionListContainer = document.getElementById("session-list-container");
        if (!sessionListContainer) return;

        sessionListContainer.innerHTML = "";
        sessions.forEach(s => {
            const item = document.createElement("div");
            item.className = "session-item" + (currentSessionId === s.id ? " active" : "");
            item.innerHTML = `
                <span class="session-title">${s.session_title || "New Chat"}</span>
                <span class="session-time">${new Date(s.updated_at).toLocaleDateString()}</span>
                <button class="session-delete-btn" data-id="${s.id}">✕</button>
            `;
            item.onclick = (e) => {
                if (e.target.classList.contains('session-delete-btn')) return;
                loadSessionHistory(s.id);
            };
            const deleteBtn = item.querySelector('.session-delete-btn');
            deleteBtn.onclick = (e) => {
                e.stopPropagation();
                deleteSession(s.id);
            };
            sessionListContainer.appendChild(item);
        });

        // Show/hide empty state
        const emptyMsg = document.getElementById("sessions-empty-msg");
        if (emptyMsg) {
            emptyMsg.style.display = sessions.length === 0 ? "block" : "none";
        }
    }

    async function deleteSession(sessionId) {
        if (!confirm("Delete this chat session?")) return;
        try {
            await secureFetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
            sessionsCache = sessionsCache.filter(s => s.id !== sessionId);
            if (currentSessionId === sessionId) {
                currentSessionId = null;
                if (sessionsCache.length > 0) {
                    loadSessionHistory(sessionsCache[0].id);
                } else {
                    await createNewSession(currentProfile?.seeker_name || "");
                }
            }
            renderSessionList(sessionsCache);
        } catch (e) {
            alert("Failed to delete session: " + e.message);
        }
    }

    // --- NEW CHAT BUTTON ---
    const newChatBtn = document.getElementById("new-chat-btn");
    if (newChatBtn) {
        newChatBtn.onclick = async () => {
            if (currentProfile) {
                await createNewSession(currentProfile.seeker_name);
            }
        };
    }

    // --- UI INTERACTIONS ---
    function openSidebar() {
        sidebar.classList.add("open");
        sidebarOverlay.style.display = "block";
        if (window.innerWidth < 768) {
            visualPanel.classList.remove("menu-open");
        }
    }

    function closeSidebar() {
        sidebar.classList.remove("open");
        sidebarOverlay.style.display = "none";
    }

    // Analysis Panel Toggle
    if (analysisToggleBtn) {
        analysisToggleBtn.onclick = () => {
            visualPanel.classList.toggle("open");
        };
    }

    // Close visual panel when clicking outside (like hamburger menu)
    document.addEventListener("click", (e) => {
        if (visualPanel.classList.contains("open")) {
            const isClickInside = visualPanel.contains(e.target);
            const isClickOnToggle = analysisToggleBtn && analysisToggleBtn.contains(e.target);
            if (!isClickInside && !isClickOnToggle) {
                visualPanel.classList.remove("open");
            }
        }
    });

    sidebarToggleBtn.onclick = openSidebar;
    closeSidebarBtn.onclick = closeSidebar;
    sidebarOverlay.onclick = closeSidebar;

    if (logoutBtn) {
        const triggerLogout = (e) => {
            e.preventDefault();
            e.stopPropagation();
            handleLogout();
        };
        // Use both listeners for desktop and mobile responsiveness
        logoutBtn.addEventListener('click', triggerLogout);
        logoutBtn.addEventListener('touchend', triggerLogout, { passive: false });
    }

    addProfileBtn.onclick = openProfileModal;
    emptyCreateBtn.onclick = openProfileModal;
    closeModalBtn.onclick = () => profileModal.style.display = "none";

    function openProfileModal() {
        profileModal.style.display = "flex";
        seekerNameInp.value = "";
        locInp.value = "";
        latInp.value = "";
        lonInp.value = "";
        seekerNameInp.focus();
    }

    // Context Menu Logic
    function showContextMenu(e, profileName) {
        activeContextMenuProfile = profileName;
        contextMenu.style.display = "flex";
        contextMenu.style.flexDirection = "column";
        contextMenu.style.padding = "5px";

        // Use touch coordinates if available, otherwise mouse coordinates
        let clientX = e.clientX;
        let clientY = e.clientY;
        if (e.changedTouches && e.changedTouches.length > 0) {
            clientX = e.changedTouches[0].clientX;
            clientY = e.changedTouches[0].clientY;
        } else if (e.touches && e.touches.length > 0) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        }

        // Temporarily show to get dimensions
        contextMenu.style.visibility = 'hidden';
        contextMenu.style.display = 'flex';

        const menuW = contextMenu.offsetWidth || 180;
        const menuH = contextMenu.offsetHeight || 100;
        const vw = window.innerWidth;
        const vh = window.innerHeight;

        let left = clientX - menuW;
        let top = clientY;

        // Clamp to viewport
        if (left < 8) left = 8;
        if (left + menuW > vw - 8) left = vw - menuW - 8;
        if (top + menuH > vh - 8) top = vh - menuH - 8;
        if (top < 8) top = 8;

        contextMenu.style.left = left + 'px';
        contextMenu.style.top = top + 'px';
        contextMenu.style.visibility = 'visible';
    }

    ctxLoadBtn.onclick = () => {
        loadProfile(activeContextMenuProfile);
        contextMenu.style.display = "none";
    };

    // View Memory button in context menu
    const ctxViewMemoryBtn = document.getElementById("ctx-view-memory");
    if (ctxViewMemoryBtn) {
        ctxViewMemoryBtn.onclick = () => {
            contextMenu.style.display = "none";
            openMemoryModal();
        };
    }

    ctxDeleteBtn.onclick = () => {
        deleteProfile(activeContextMenuProfile);
        contextMenu.style.display = "none";
    };

    // Memory Modal controls
    const closeMemoryModalBtn = document.getElementById("close-memory-modal-btn");
    if (closeMemoryModalBtn) {
        closeMemoryModalBtn.onclick = closeMemoryModal;
    }
    // Click outside to close
    const memoryModal = document.getElementById("memory-modal");
    if (memoryModal) {
        memoryModal.onclick = (e) => {
            if (e.target === memoryModal) closeMemoryModal();
        };
    }
    // Add memory button
    const memoryAddBtn = document.getElementById("memory-add-btn");
    if (memoryAddBtn) {
        memoryAddBtn.onclick = async () => {
            const keyInput = document.getElementById("memory-key-input");
            const valueInput = document.getElementById("memory-value-input");
            if (currentProfile) {
                await addMemory(currentProfile.seeker_name, keyInput?.value || "", valueInput?.value || "");
            } else {
                alert("Please load a profile first.");
            }
        };
    }
    // Enter key support for memory add
    const memoryValueInput = document.getElementById("memory-value-input");
    if (memoryValueInput) {
        memoryValueInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const addBtn = document.getElementById("memory-add-btn");
                if (addBtn) addBtn.click();
            }
        });
    }

    // Language Preference Listener
    const languageInp = document.getElementById("preferred-language");
    languageInp.onchange = async () => {
        const newLang = languageInp.value;
        try {
            await secureFetch("/api/settings", {
                method: "POST",
                body: JSON.stringify({ preferred_language: newLang })
            });
            addMessage(`Response language updated to: ${newLang}`, "system-msg");
        } catch (e) {
            alert("Failed to save language preference.");
        }
    };

    window.onclick = (e) => {
        if (!e.target.classList.contains('profile-actions-btn')) contextMenu.style.display = "none";
        if (e.target === profileModal) profileModal.style.display = "none";
        if (e.target === authModal) { /* Force auth */ }
    };

    // --- FORM HANDLING ---
    saveProfileBtn.onclick = async () => {
        const name = seekerNameInp.value.trim();
        const gender = genderInp.value;
        const lat = latInp.value;
        const lon = lonInp.value;
        const locName = locInp.value;
        const tz = tzInp.value;

        if (!name || !lat || !lon || !dy.value || !dm.value || !dd.value || !dh.value || !dmin.value) {
            alert("Please complete all fields (Name, DOB, Time, and Location).");
            return;
        }

        let h24 = parseInt(dh.value, 10);
        if (ampmInp.value === "PM" && h24 < 12) h24 += 12;
        if (ampmInp.value === "AM" && h24 === 12) h24 = 0;

        const dob = `${dy.value}-${dm.value}-${dd.value} ${h24.toString().padStart(2, '0')}:${dmin.value}:00`;
        const birthData = {
            local_time: dob,
            timezone: tz,
            latitude: parseFloat(lat),
            longitude: parseFloat(lon),
            location_name: locName,
            gender: gender
        };

        saveProfileBtn.disabled = true;
        saveProfileBtn.innerText = "Calculating Orbit...";

        try {
            // First time generate to verify and save
            const res = await secureFetch("/generate_chart_data", {
                method: "POST",
                body: JSON.stringify(birthData)
            });
            const data = await res.json();
            if (data.status === "success") {
                // Now save it as a profile by tricking the backend via a chat request or similar
                // Actually, just sending agent_chat with a blank question will save birth details
                await secureFetch("/agent_chat", {
                    method: "POST",
                    body: JSON.stringify({ seeker_name: name, birth_data: birthData, question: "[INITIALIZATION]" })
                });

                profileModal.style.display = "none";
                await refreshProfileList();
                loadProfile(name);
            }
        } catch (e) {
            alert("Orbit calculation failed: " + e.message);
        } finally {
            saveProfileBtn.disabled = false;
            saveProfileBtn.innerText = "Calculate & Save Profile";
        }
    };

    // Location Autocomplete
    let locTimeout = null;
    locInp.addEventListener("input", function() {
        clearTimeout(locTimeout);
        const val = this.value;
        const list = document.getElementById("location-suggestions");
        if (!val || val.length < 3) { list.style.display = "none"; return; }
        locTimeout = setTimeout(() => {
            fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(val)}`)
                .then(r => r.json()).then(data => {
                    list.innerHTML = "";
                    if (data.length > 0) {
                        list.style.display = "block";
                        data.forEach(place => {
                            const div = document.createElement("div");
                            div.innerHTML = place.display_name;
                            div.onclick = () => {
                                const parts = place.display_name.split(",");
                                locInp.value = parts[0].trim() + ", " + (parts[parts.length - 1] || "").trim();
                                latInp.value = place.lat;
                                lonInp.value = place.lon;
                                list.style.display = "none";
                            };
                            list.appendChild(div);
                        });
                    }
                });
        }, 600);
    });

    // --- CHAT LOGIC ---
    let currentLoader = null;

    function showLoader() {
        if (currentLoader) currentLoader.remove();
        currentLoader = document.createElement("div");
        currentLoader.className = "message agent-msg loading-msg";
        currentLoader.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';
        chatOutput.appendChild(currentLoader);

        // Delay scrolling so mobile keyboards have time to animate open before we jump to bottom
        setTimeout(() => {
            chatOutput.scrollTop = chatOutput.scrollHeight;
        }, 300);
    }

    function removeLoader() {
        if (currentLoader) {
            currentLoader.remove();
            currentLoader = null;
        }
    }

    async function processQuery(question, errorNodeToRemove = null, selectedDomains = selectedQuestionDomains()) {
        if (!selectedDomains.length) {
            domainPickerHelp.textContent = "Choose at least one question tag before sending.";
            domainPickerHelp.classList.add("error");
            domainPicker.open = true;
            return;
        }
        if (errorNodeToRemove) {
            errorNodeToRemove.remove(); // Clean up the failed system message block
        }

        sendBtn.disabled = true;
        sendBtn.classList.add("loading");
        systemStatus.style.animationDuration = "0.3s";

        showLoader();

        try {
            const res = await secureFetch("/agent_chat", {
                method: "POST",
                body: JSON.stringify({
                    seeker_name: currentProfile.seeker_name,
                    birth_data: {
                        local_time: currentProfile.local_time,
                        timezone: currentProfile.timezone,
                        latitude: currentProfile.lat,
                        longitude: currentProfile.lon,
                        location_name: currentProfile.location,
                        gender: currentProfile.gender
                    },
                    question: question,
                    selected_domains: selectedDomains,
                    session_id: currentSessionId
                })
            });
            const data = await res.json();

            removeLoader();

            // Check if the response is valid and not a hidden backend error string
            const isErrorString = data.agent_response && (
                data.agent_response.includes("SYSTEM_ERROR") ||
                data.agent_response.toLowerCase().includes("try again later") ||
                data.agent_response.toLowerCase().includes("quota exceeded") ||
                data.agent_response.toLowerCase().includes("too many requests") ||
                data.agent_response.toLowerCase().includes("overloaded")
            );

            if (data.status === "success" && data.agent_response && !isErrorString) {
                if (data.diagnostics) renderDiagnostics(data.diagnostics);
                addMessage(data.agent_response, "agent-msg");

                // Auto-generate title for new sessions
                if (currentSessionId) {
                    const currentSession = sessionsCache.find(s => s.id === currentSessionId);
                    if (currentSession && currentSession.session_title === "New Chat") {
                        try {
                            const titleRes = await secureFetch(`/api/sessions/${currentSessionId}/generate_title`, {
                                method: "POST"
                            });
                            const titleData = await titleRes.json();
                            if (titleData.status === "success" && titleData.title) {
                                // Update the session in cache
                                const sessionToUpdate = sessionsCache.find(s => s.id === currentSessionId);
                                if (sessionToUpdate) {
                                    sessionToUpdate.session_title = titleData.title;
                                }
                                renderSessionList(sessionsCache);
                            }
                        } catch (titleErr) {
                            console.warn("Title generation failed:", titleErr);
                        }
                    }
                }
            } else {
                // If it's an API error, gracefully show the retry button below it
                let errMsg = data.detail || (isErrorString ? data.agent_response : "The system is currently busy analyzing other cosmic energies. Please try again.");

                // Truncate overly long technical errors for the UI
                if (errMsg.length > 200) errMsg = errMsg.substring(0, 200) + "...";

                showRetryMessage(question, `<strong>API Overload / Busy:</strong> ${errMsg}`, selectedDomains);
            }
        } catch (e) {
            removeLoader();
            showRetryMessage(question, "Cosmic alignment lost. Check your connection.", selectedDomains);
        } finally {
            sendBtn.disabled = false;
            sendBtn.classList.remove("loading");
            systemStatus.style.animationDuration = "2s";
        }
    }

    // Keyboard shortcut: Enter to send, Shift+Enter for new line
    questionInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendBtn.click();
        }
        // Shift+Enter naturally adds a new line in textarea - no need to prevent default
    });

    sendBtn.onclick = async () => {
        const question = questionInput.value.trim();
        if (!question || !currentProfile) return;
        const domains = selectedQuestionDomains();
        if (!domains.length) {
            domainPickerHelp.textContent = "Choose at least one question tag before sending.";
            domainPickerHelp.classList.add("error");
            domainPicker.open = true;
            return;
        }

        const selectedLabels = domains.map(tag => {
            const input = domainCheckboxes.find(item => item.value === tag);
            return input ? input.parentElement.textContent.trim() : tag;
        });
        addMessage(`${question}\nTopics: ${selectedLabels.join(", ")}`, "user-msg");
        questionInput.value = "";

        await processQuery(question, null, domains);
    };

    window.pendingDomainSelections = {};
    window.retryLastMessage = function(btnElement, questionText) {
        const errorNode = btnElement.closest('.message');
        const domains = window.pendingDomainSelections[questionText] || selectedQuestionDomains();
        processQuery(questionText, errorNode, domains);
    };

    function showRetryMessage(questionText, customMsg, selectedDomains = selectedQuestionDomains()) {
        // Build an elegant retry button inside the system message
        window.pendingDomainSelections[questionText] = selectedDomains;
        const escQuestion = questionText.replace(/'/g, "\\'").replace(/"/g, '\\"');
        const btnHtml = `<div style="margin-top: 15px;"><button class="retry-action-btn" onclick="window.retryLastMessage(this, '${escQuestion}')">⟳ Retry Request</button></div>`;
        addMessage(`${customMsg} ${btnHtml}`, "system-msg");
    }

    // --- HELPERS ---
    function addMessage(text, type) {
        const msg = document.createElement("div");
        msg.className = `message ${type}`;
        if (type === 'agent-msg' && window.marked) {
            // Remove the literal "Markdown" prefix if present at the start
            let cleanText = text;
            if (typeof cleanText === 'string' && cleanText.trim().toLowerCase().startsWith('markdown')) {
                // Remove the word "Markdown" and any following whitespace/newlines
                cleanText = cleanText.replace(/^[\s]*[Mm]arkdown[\s]*\n?/, '');
            }
            msg.innerHTML = marked.parse(cleanText);

            // Post-process to extract Conversational Bridge items into clickable buttons
            const lists = msg.querySelectorAll('ul, ol');
            if (lists.length > 0) {
                // Find all headers, checking for any that might be the bridge
                const headers = msg.querySelectorAll('h1, h2, h3, h4, h5, h6, strong');
                let bridgeHeader = null;
                headers.forEach(h => {
                    const txt = h.innerText.toLowerCase();
                    // Look for 7, bridge, or the translated terms
                    if (txt.includes('7.') || txt.includes('bridge') || txt.includes('सेतु') || txt.includes('সেতু') || txt.includes('conversational')) {
                        bridgeHeader = h;
                    }
                });

                let targetList = null;
                if (bridgeHeader) {
                    // Hide the header
                    bridgeHeader.style.display = 'none';
                    // The target list is likely the very next sibling
                    let curr = bridgeHeader.nextElementSibling;
                    while (curr) {
                        if (curr.tagName === 'UL' || curr.tagName === 'OL') {
                            targetList = curr;
                            break;
                        }
                        curr = curr.nextElementSibling;
                    }
                }

                // Fallback: If no explicit bridge header was found, cautiously grab the very last list
                if (!targetList) {
                    targetList = lists[lists.length - 1];
                    // Optional: remove any generic header directly above it
                    let prev = targetList.previousElementSibling;
                    if (prev && prev.tagName.match(/^H[1-6]$/)) {
                        prev.style.display = 'none';
                    }
                }

                if (targetList) {
                    processListIntoSuggestions(targetList);
                }
            }

            function processListIntoSuggestions(listEl) {
                const items = listEl.querySelectorAll('li');
                const btnContainer = document.createElement('div');
                btnContainer.className = 'suggestion-container';

                items.forEach(li => {
                    const btn = document.createElement('button');
                    btn.className = 'suggestion-action-btn';
                    // extract text without nested tags
                    btn.innerText = "👉 " + li.innerText.replace(/^\d+\.\s*/, '').replace(/^-\s*/, '');
                    btn.onclick = () => {
                        document.getElementById('question').value = btn.innerText.replace("👉 ", "");
                        document.getElementById('send-btn').click();
                    };
                    btnContainer.appendChild(btn);
                });

                // Hide the original physical list
                listEl.style.display = 'none';

                // FORCE the buttons to append to the very end of the message bubble,
                // so they never accidentally appear in the middle of the response!
                msg.appendChild(btnContainer);
            }

        } else if (type === 'system-msg') {
            msg.innerHTML = text; // Allow HTML like retry buttons
        } else {
            msg.innerText = text;
        }

        chatOutput.appendChild(msg);

        if (type === 'agent-msg') {
            // Guarantee scroll to the top of the new response by doing explicit math routing on the container
            setTimeout(() => {
                const scrollPos = msg.offsetTop - chatOutput.offsetTop - 10;
                chatOutput.scrollTo({ top: scrollPos, behavior: 'smooth' });
            }, 150);
        } else {
            // Normal scroll for user messages
            chatOutput.scrollTop = chatOutput.scrollHeight;
        }
    }

    function renderDiagnostics(d) {
        const hud = document.createElement("div");
        hud.className = "diagnostic-hud";
        hud.innerHTML = `
            <div class="diag-item">🚀 <strong>RAG Engine:</strong> ${d.rag_online ? 'SYNCED (' + d.neo4j_rules + ' rules)' : 'OFFLINE'}</div>
            <div class="diag-item">⌛ <strong>Timing:</strong> ${d.dasha_active}</div>
        `;
        chatOutput.appendChild(hud);

        if (!d.rag_online) systemStatus.classList.add("status-warning");
        else systemStatus.classList.remove("status-warning");
    }

    function renderFullAnalysis(data) {
        const cards = document.getElementById("analysis-cards");
        if (!cards) return;
        cards.style.display = "flex";

        const astro = data.deterministic_astronomy || data.chart || data;
        const esc = (v) => String(v ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
        const pairsHtml = (obj, limit = 12) => Object.entries(obj || {}).slice(0, limit).map(([k, v]) => `<span class="engine-chip"><b>${esc(k)}</b>: ${esc(typeof v === 'object' ? JSON.stringify(v) : v)}</span>`).join(' ');

        // 1. Shadbala Card
        const sb = data.shadbala_summary || astro.shadbala_summary || {};
        const planets = sb.planets || {};
        let sbHtml = '';
        for (const [p, v] of Object.entries(planets).sort((a,b) => (b[1].total_rupas||0) - (a[1].total_rupas||0))) {
            const r = v.total_rupas || 0;
            const w = Math.min(100, r * 12);
            const clr = r > 6 ? 'var(--green-glow)' : r > 4 ? 'var(--gold-accent)' : r > 2.5 ? '#ccc' : 'var(--red-glow)';
            sbHtml += `<div class="strength-row"><span class="strength-name">${p}</span><div class="strength-bar"><div class="strength-fill" style="width:${w}%;background:${clr}"></div></div><span class="strength-val">${r.toFixed(1)}R</span></div>`;
        }
        if (sb.strongest_planet) sbHtml += `<div style="margin-top:6px;font-size:11px;">🏆 Strongest: <b style="color:var(--green-glow)">${sb.strongest_planet}</b> | Weakest: <b style="color:var(--red-glow)">${sb.weakest_planet}</b></div>`;
        document.getElementById("shadbala-body").innerHTML = sbHtml || '<span style="color:#888">Shadbala data not available</span>';

        // 2. Ashtakavarga Card
        const av = data.ashtakavarga || astro.ashtakavarga || {};
        const sarva = av.sarvashtakavarga || {};
        let avHtml = '<div class="bindu-grid">';
        for (let h = 1; h <= 12; h++) {
            const b = sarva[h] || 0;
            const cls = b >= 30 ? 'bindu-high' : b >= 22 ? 'bindu-mid' : 'bindu-low';
            avHtml += `<div class="bindu-cell ${cls}">H${h}<br><strong>${b}</strong></div>`;
        }
        avHtml += '</div>';
        if (av.strongest_sign) avHtml += `<div style="margin-top:6px;font-size:11px;">Strongest sign: ${av.strongest_sign} (${sarva[av.strongest_sign]||0}) | Weakest sign: ${av.weakest_sign} (${sarva[av.weakest_sign]||0}) | Avg: ${av.average_bindus||'N/A'}</div>`;
        document.getElementById("ashtakavarga-body").innerHTML = avHtml || '<span style="color:#888">Ashtakavarga data not available</span>';

        // 3. Panchang + positions card
        const panchang = astro.panchang || {};
        const positions = astro.planetary_positions || {};
        let panchangHtml = `<div class="engine-kv-grid">
            <div><span>Tithi</span><b>${esc(panchang.tithi || 'N/A')}</b></div>
            <div><span>Paksha</span><b>${esc(panchang.paksha || 'N/A')}</b></div>
            <div><span>Nakshatra</span><b>${esc(panchang.nakshatra || 'N/A')}</b></div>
            <div><span>Vaar</span><b>${esc(panchang.vaar || 'N/A')}</b></div>
        </div>`;
        panchangHtml += '<div class="engine-mini-table">' + Object.entries(positions).map(([planet, pos]) => `<div><b>${esc(planet)}</b><span>${esc(pos.sign)} H${esc(pos.house_number)} N${esc(pos.nakshatra_index)}.${esc(pos.nakshatra_pada)}${pos.is_retrograde ? ' R' : ''}</span></div>`).join('') + '</div>';
        document.getElementById("panchang-body").innerHTML = panchangHtml;

        // 4. Current transits card
        const transits = astro.current_transits || {};
        document.getElementById("transits-body").innerHTML = pairsHtml(transits) || '<span style="color:#888">Transit data not available</span>';

        // 5. Dasha systems card
        const dashas = astro.dasha_timeline || {};
        const dashaHtml = Object.entries(dashas).map(([name, periods]) => {
            if (name === 'dasha_sandhi') {
                const critical = periods.critical_periods || [];
                return `<div class="engine-list-row"><b>${esc(name)}</b><span>${critical.length} critical periods</span></div>`;
            }
            const count = Array.isArray(periods) ? periods.length : Object.keys(periods || {}).length;
            const first = Array.isArray(periods) && periods[0] ? `First: ${periods[0].lord || periods[0].sign || 'period'} ${periods[0].start ? '(' + periods[0].start + ')' : ''}` : '';
            return `<div class="engine-list-row"><b>${esc(name)}</b><span>${count} periods ${esc(first)}</span></div>`;
        }).join('');
        document.getElementById("dasha-systems-body").innerHTML = dashaHtml || '<span style="color:#888">Dasha data not available</span>';

        // 6. Graha drishti card
        const gd = astro.graha_drishti || {};
        const received = gd.total_aspect_received || {};
        const topAspects = Object.entries(received).sort((a,b) => (b[1] || 0) - (a[1] || 0)).slice(0, 5);
        let gdHtml = `<div style="font-size:11px;margin-bottom:5px;">Most Aspected: <b>${esc(gd.most_aspected_planet || 'N/A')}</b> | Least: <b>${esc(gd.least_aspected_planet || 'N/A')}</b></div>`;
        gdHtml += topAspects.map(([p, v]) => `<span class="engine-chip"><b>${esc(p)}</b>: ${esc(v)} received</span>`).join(' ');
        document.getElementById("graha-body").innerHTML = gdHtml || '<span style="color:#888">Aspect data not available</span>';

        // 7. Combustion card
        const combustion = astro.combustion || {};
        const combustStatus = combustion.combustion_status || {};
        const combustPlanets = Object.entries(combustStatus).filter(([, active]) => active).map(([planet]) => planet);
        let combustionHtml = `<div>Combust planets: <b>${esc(combustPlanets.join(', ') || 'None')}</b></div>`;
        const wars = combustion.planetary_wars || [];
        combustionHtml += `<div style="font-size:11px;margin-top:4px;">Planetary wars: ${wars.length ? esc(JSON.stringify(wars)) : 'None'}</div>`;
        combustionHtml += '<div style="margin-top:5px;">' + pairsHtml(combustion.combustion_severity || {}, 9) + '</div>';
        document.getElementById("combustion-body").innerHTML = combustionHtml;

        // 8. Jaimini Card
        const js = data.jaimini_system || astro.jaimini_system || {};
        const kk = js.karakas || {};
        let jsHtml = `<div style="margin-bottom:6px;"><b>Atmakaraka (Soul):</b> ${kk.atmakaraka||'N/A'} | <b>Amatyakaraka (Career):</b> ${kk.amatyakaraka||'N/A'} | <b>Darakaraka (Spouse):</b> ${kk.darakaraka||'N/A'}</div>`;
        jsHtml += `<div style="font-size:11px;">Arudha Lagna: ${(js.arudha||{}).arudha_lagna||'N/A'} | Chara Karakas: ${Object.entries(kk.chara_karakas||{}).map(([k,v])=>`${k.split(' ')[0]}=${v}`).join(', ') || 'N/A'}</div>`;
        document.getElementById("jaimini-body").innerHTML = jsHtml;

        // 4. KP Card
        const kp = data.kp_system || astro.kp_system || {};
        const rp = kp.ruling_planets || {};
        let kpHtml = '<div style="margin-bottom:6px;">';
        for (const [k,v] of Object.entries(rp)) kpHtml += `<span class="ruling-planet">${k}: ${v}</span> `;
        kpHtml += '</div>';
        const sigs = kp.significators || {};
        kpHtml += '<div style="font-size:11px;">Significators: ' + Object.entries(sigs).map(([p,h])=>`${p}→H${h}`).join(', ') + '</div>';
        document.getElementById("kp-body").innerHTML = kpHtml || '<span style="color:#888">KP data not available</span>';

        // 5. Yogas Card
        const feats = data.semantic_features || data.features || astro.semantic_features || {};
        const comp = feats.composite || {};
        const yogas = comp.yogas || comp.yoga_details || [];
        let yogaHtml = `<div style="margin-bottom:4px;"><b>Total:</b> ${comp.total_yogas || yogas.length || 0} yogas detected</div>`;
        if (Array.isArray(yogas)) yogas.forEach(y => { yogaHtml += `<span class="yoga-badge">${typeof y === 'string' ? y : y.name}</span> `; });
        else if (typeof yogas === 'object') Object.values(yogas).forEach(y => { yogaHtml += `<span class="yoga-badge">${typeof y === 'string' ? y : y.name||y}</span> `; });
        document.getElementById("yogas-body").innerHTML = yogaHtml || '<span style="color:#888">No yogas detected</span>';

        // 6. Special Features Card
        const sf = data.special_features || astro.special_features || {};
        const ss = sf.sade_sati || {};
        const md = sf.mangal_dosha || {};
        const pd = sf.pitra_dosha || {};
        let sfHtml = '';
        sfHtml += `<span class="phase-tag ${ss.in_sade_sati ? 'phase-active' : 'phase-safe'}">Sade Sati: ${ss.in_sade_sati ? ss.phase : 'None'}</span> `;
        sfHtml += `<span class="dosha-badge ${md.has_mangal_dosha ? 'dosha-active' : 'dosha-inactive'}">Mangal: ${md.severity||'None'}</span> `;
        sfHtml += `<span class="dosha-badge ${pd.has_pitra_dosha ? 'dosha-active' : 'dosha-inactive'}">Pitra: ${pd.severity||'None'}</span>`;
        const vt = astro.vargottama || {};
        const vtPlanets = Object.entries(vt).filter(([k,v])=>v).map(([k])=>k);
        if (vtPlanets.length) sfHtml += `<div style="margin-top:4px;font-size:11px;">Vargottama: ${vtPlanets.join(', ')}</div>`;
        document.getElementById("special-body").innerHTML = sfHtml || '<span style="color:#888">No special features data</span>';

        // 7. Historical calibration status (not a direct chart-to-event prediction)
        const empirical = data.prediction_calibration || astro.prediction_calibration || data.empirical_predictions || astro.empirical_predictions || { status: 'calibration_unavailable' };
        if (empirical.status) {
            let mlHtml = '';
            if (empirical.status === 'available' && Array.isArray(empirical.claims) && empirical.claims.length) {
                mlHtml = empirical.claims.map(claim => {
                    const domain = String(claim.domain || 'Prediction').replace(/[&<>"']/g, '');
                    if (claim.status !== 'available' || !Number.isFinite(Number(claim.observed_match_rate))) {
                        return `<div>${domain}: historical reference not yet available (${Number(claim.matched_cases || 0)} matched cases).</div>`;
                    }
                    const rate = (Number(claim.observed_match_rate) * 100).toFixed(1);
                    return `<div>${domain}: ${rate}% observed matches across ${Number(claim.matched_cases || 0)} similar resolved cases.</div>`;
                }).join('');
                mlHtml += '<div style="margin-top:6px;font-size:11px;color:#888;">Historical cohort reference, not a personal probability or guarantee.</div>';
            } else {
                mlHtml = '<span style="color:#888">No historical candidate-window calibration is available yet. Direct chart-to-event ML is research-only.</span>';
            }
            document.getElementById("ml-body").innerHTML = mlHtml;
        } else {
            document.getElementById("ml-body").innerHTML = '<span style="color:#888">No calibrated historical reliability reference is available for this prediction.</span>';
        }

        // 8. Predictive Card
        const pred = data.predictive_tech || astro.predictive_tech || {};
        const muh = pred.muhurta_quality || {};
        const rems = pred.remedies || {};
        let predHtml = '';
        if (muh.quality) predHtml += `<div style="margin-bottom:4px;">Muhurta: <b>${muh.quality}</b> (${muh.score||'N/A'})</div>`;
        const vp = pred.varshaphala || {};
        if (vp.muntha) predHtml += `<div style="font-size:11px;">Varshaphala Muntha: ${vp.muntha} | Tajika Yogas: ${(vp.tajika_yogas||[]).join(', ')||'None'}</div>`;
        if (Object.keys(rems).length) {
            predHtml += '<div style="margin-top:4px;font-size:11px;"><b>Remedies:</b></div>';
            for (const [p, r] of Object.entries(rems)) predHtml += `<div class="remedy-item">${p}: ${r.gem||''} · ${r.mantra||''}</div>`;
        }
        document.getElementById("predictive-body").innerHTML = predHtml || '<span style="color:#888">Predictive data not available</span>';

        // 9. Navatara Chakra Card
        const nv = data.navatara_chakra || astro.navatara_chakra || {};
        const janmaNak = nv.janma_nakshatra || 'N/A';
        const janmaPada = nv.janma_nakshatra_pada || '';
        let nvHtml = `<div class="navatara-janma">☽ Janma Nakshatra: ${janmaNak}${janmaPada ? ' · Pada ' + janmaPada : ''}</div>`;

        function _buildTaraRows(planets) {
            if (!planets || !planets.length) return '<span style="color:#888">No data</span>';
            let rows = '';
            for (const p of planets) {
                const qCls = p.quality === 'Benefic' ? 'tara-benefic' : p.quality === 'Malefic' ? 'tara-malefic' : 'tara-neutral';
                rows += `<div class="navatara-row">
                    <span class="navatara-planet">${p.alert} ${p.planet}</span>
                    <span class="navatara-nak">${p.nakshatra}</span>
                    <span class="navatara-tara-badge ${qCls}">${p.tara_name} (T${p.tara_number})</span>
                </div>`;
            }
            return rows;
        }

        // Natal section
        const natal = nv.natal || {};
        const natalSummary = natal.summary || {};
        nvHtml += '<div class="navatara-section-label">📍 Natal — Birth Planet Taras</div>';
        nvHtml += _buildTaraRows(natal.planets);
        if (natalSummary.critical_alert) {
            nvHtml += `<div class="navatara-alert">⚠️ Natal Alert: ${natalSummary.critical_alert}</div>`;
        }
        nvHtml += `<div class="navatara-strength">Natal Strength: <b>${natalSummary.overall_strength || 'N/A'}</b> · ✅ ${natalSummary.benefic_count || 0} benefic · ⚠️ ${natalSummary.malefic_count || 0} malefic</div>`;

        // Transit section
        const transit = nv.transit || {};
        const transitSummary = transit.summary || {};
        if (transit.planets && transit.planets.length) {
            nvHtml += '<hr class="navatara-divider">';
            nvHtml += '<div class="navatara-section-label">🌍 Transit — Current Sky Taras (vs Janma Nakshatra)</div>';
            nvHtml += _buildTaraRows(transit.planets);
            if (transitSummary.critical_alert) {
                nvHtml += `<div class="navatara-alert">⚠️ Transit Alert: ${transitSummary.critical_alert}</div>`;
            }
            const malPlanets = (transitSummary.malefic_planets || []).join(', ') || 'None';
            nvHtml += `<div class="navatara-strength">Transit Strength: <b>${transitSummary.overall_strength || 'N/A'}</b> · Malefic Transits: ${malPlanets}</div>`;
        }

        document.getElementById("navatara-body").innerHTML = nvHtml || '<span style="color:#888">Navatara data not available</span>';
    }

    function renderPersonalDetails(astro, profile) {
        const sec = document.getElementById("person-section");
        const p = astro.panchang;
        const meta = astro.metadata;

        sec.innerHTML = `
            <div class="details-container">
                <div class="details-group">
                    <h4>👤 Profile</h4>
                    <div class="details-grid">
                        <div class="detail-item"><div class="detail-label">Name</div><div class="detail-value">${profile.seeker_name}</div></div>
                        <div class="detail-item"><div class="detail-label">Gender</div><div class="detail-value">${profile.gender}</div></div>
                        <div class="detail-item"><div class="detail-label">Birth Date</div><div class="detail-value">${new Date(profile.local_time.split(' ')[0]).toDateString()}</div></div>
                        <div class="detail-item"><div class="detail-label">Place</div><div class="detail-value">${profile.location || "Earth"}</div></div>
                    </div>
                </div>
                <div class="details-group">
                    <h4>✨ Cosmic Signatures</h4>
                    <div class="details-grid">
                        <div class="detail-item" style="border-left: 3px solid var(--cyan-glow);"><div class="detail-label">Lagna</div><div class="detail-value">${meta.ascendant}</div></div>
                        <div class="detail-item" style="border-left: 3px solid var(--gold-accent);"><div class="detail-label">Moon Sign</div><div class="detail-value">${p.moon_rashi}</div></div>
                        <div class="detail-item"><div class="detail-label">Nakshatra</div><div class="detail-value">${p.nakshatra}</div></div>
                    </div>
                </div>
            </div>
        `;
    }

    function renderTabs(vargas) {
        chartTabs.innerHTML = "";
        const keys = Object.keys(vargas).sort((a,b) => {
            const numA = parseInt(a.match(/\d+/) || [0], 10);
            const numB = parseInt(b.match(/\d+/) || [0], 10);
            return numA - numB;
        });

        keys.forEach((vName, i) => {
            const btn = document.createElement("button");
            btn.className = "tab-btn" + (i === 0 ? " active" : "");
            const displayName = vName.split("_")[0].toUpperCase();
            btn.innerText = displayName;
            btn.onclick = () => {
                document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
                btn.classList.add("active");
                loadChartImage(displayName, vargas[vName]);
            };
            chartTabs.appendChild(btn);
            if (i === 0) loadChartImage(displayName, vargas[vName]);
        });
    }

    async function loadChartImage(chartName, matrix) {
        kundliSkeleton.style.display = "block";
        kundliImg.style.display = "none";
        try {
            const res = await secureFetch("/generate_chart_image", {
                method: "POST",
                body: JSON.stringify({ chart_name: chartName, varga_matrix: matrix })
            });
            const data = await res.json();
            if (data.status === "success") {
                kundliImg.src = "data:image/png;base64," + data.image_base64;
                kundliImg.style.display = "block";
                kundliSkeleton.style.display = "none";
            }
        } catch (e) { kundliSkeleton.innerText = "Optic failure"; }
    }

    function renderDasha(timelineData) {
        dashaBody.innerHTML = "";
        const timeline = timelineData.Vimshottari || timelineData;
        timeline.forEach((maha) => {
            const mahaRow = document.createElement("tr");
            mahaRow.className = "dasha-row maha";
            mahaRow.innerHTML = `<td>${maha.lord}</td><td>${maha.start || ''}</td><td>${maha.end || ''}</td>`;

            // Build antar rows and their children (hidden by default)
            const antarRows = [];
            const antarChildren = new Map(); // antar row element → its pratyantar rows

            if (maha.antardashas && maha.antardashas.length > 0) {
                maha.antardashas.forEach(antar => {
                    const antarRow = document.createElement("tr");
                    antarRow.className = "dasha-row antar";
                    antarRow.style.display = "none";
                    antarRow.innerHTML = `<td>${antar.lord}</td><td>${antar.start || ''}</td><td>${antar.end || ''}</td>`;

                    // Build pratyantar rows (hidden by default)
                    const pratRows = [];
                    if (antar.pratyantardashas && antar.pratyantardashas.length > 0) {
                        antar.pratyantardashas.forEach(prat => {
                            const pratRow = document.createElement("tr");
                            pratRow.className = "dasha-row pratyantar";
                            pratRow.style.display = "none";
                            pratRow.innerHTML = `<td>${prat.lord}</td><td>${prat.start || ''}</td><td>${prat.end || ''}</td>`;
                            pratRows.push(pratRow);
                        });
                    }

                    // Toggle pratyantar accordion on antar row tap
                    const togglePrat = (e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        const isExpanded = antarRow.classList.toggle('expanded');
                        pratRows.forEach(pr => { pr.style.display = isExpanded ? '' : 'none'; });
                    };
                    if (pratRows.length > 0) {
                        antarRow.addEventListener('click', togglePrat);
                        antarRow.addEventListener('touchend', togglePrat, { passive: false });
                    }

                    antarChildren.set(antarRow, pratRows);
                    antarRows.push(antarRow);
                });
            }

            // Toggle antar accordion on maha row tap
            const toggleAntar = (e) => {
                e.stopPropagation();
                const isExpanded = mahaRow.classList.toggle('expanded');
                antarRows.forEach(ar => {
                    ar.style.display = isExpanded ? '' : 'none';
                    // Collapse pratyantar when collapsing antar
                    if (!isExpanded) {
                        ar.classList.remove('expanded');
                        const pratRows = antarChildren.get(ar) || [];
                        pratRows.forEach(pr => { pr.style.display = 'none'; });
                    }
                });
            };
            mahaRow.addEventListener('click', toggleAntar);
            mahaRow.addEventListener('touchend', (e) => { e.preventDefault(); toggleAntar(e); }, { passive: false });

            dashaBody.appendChild(mahaRow);
            antarRows.forEach(ar => {
                dashaBody.appendChild(ar);
                const pratRows = antarChildren.get(ar) || [];
                pratRows.forEach(pr => dashaBody.appendChild(pr));
            });
        });
    }

    function populateDropdowns() {
        for(let i=2030; i>=1900; i--) dy.options.add(new Option(i, i));
        for(let i=1; i<=12; i++) dm.options.add(new Option(i.toString().padStart(2,'0'), i.toString().padStart(2,'0')));
        for(let i=1; i<=31; i++) dd.options.add(new Option(i.toString().padStart(2,'0'), i.toString().padStart(2,'0')));
        for(let i=1; i<=12; i++) dh.options.add(new Option(i.toString().padStart(2,'0'), i.toString().padStart(2,'0')));
        for(let i=0; i<=59; i++) dmin.options.add(new Option(i.toString().padStart(2,'0'), i.toString().padStart(2,'0')));
    }

    // Auth toggle
    document.getElementById("show-signup").onclick = (e) => { e.preventDefault(); showAuthModal("signup"); };
    document.getElementById("show-login").onclick = (e) => { e.preventDefault(); showAuthModal("login"); };

    // Helper to show auth errors
    function showAuthError(message) {
        const errorEl = document.getElementById("auth-error");
        if (errorEl) {
            errorEl.textContent = message;
            errorEl.classList.add("visible");
        }
    }

    function clearAuthError() {
        const errorEl = document.getElementById("auth-error");
        if (errorEl) {
            errorEl.classList.remove("visible");
            errorEl.textContent = "";
        }
    }

    // Password Toggle Functionality
    document.querySelectorAll(".password-toggle").forEach(btn => {
        btn.addEventListener("click", function(e) {
            e.preventDefault();
            const targetId = this.getAttribute("data-target");
            const input = document.getElementById(targetId);
            if (!input) return;

            const isPassword = input.type === "password";
            input.type = isPassword ? "text" : "password";
            this.classList.toggle("active");

            // Update icon
            const icon = this.querySelector(".toggle-icon");
            if (icon) {
                icon.textContent = isPassword ? "👁️‍🗨️" : "👁️";
            }
        });
    });

    document.getElementById("login-submit").onclick = async () => {
        clearAuthError();
        const u = document.getElementById("login-username").value.trim();
        const p = document.getElementById("login-password").value;
        if (!u || !p) {
            showAuthError("Please enter both username and password.");
            return;
        }
        const formData = new URLSearchParams();
        formData.append("username", u); formData.append("password", p);
        try {
            const res = await fetch("/api/token", { method: "POST", body: formData });
            const data = await res.json();
            if (res.ok && data.access_token) {
                localStorage.setItem("astra_auth_token", data.access_token);
                jwtToken = data.access_token;
                checkAuth();
            } else {
                const errMsg = data.detail || "Invalid username or password. Please try again.";
                showAuthError(errMsg);
            }
        } catch (e) {
            showAuthError("Network error. Please check your connection.");
        }
    };

    document.getElementById("signup-submit").onclick = async () => {
        clearAuthError();
        const u = document.getElementById("signup-username").value.trim();
        const p = document.getElementById("signup-password").value;
        const c = document.getElementById("signup-confirm").value;

        if (!u || !p || !c) {
            showAuthError("Please fill in all fields.");
            return;
        }
        if (u.length < 3) {
            showAuthError("Username must be at least 3 characters long.");
            return;
        }
        if (p.length < 4) {
            showAuthError("Password must be at least 4 characters long.");
            return;
        }
        if (p !== c) {
            showAuthError("Passwords do not match.");
            return;
        }

        try {
            const res = await fetch("/api/signup", {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ username: u, password: p })
            });
            const data = await res.json();
            if (res.ok) {
                // Auto-login after successful signup
                document.getElementById("login-username").value = u;
                document.getElementById("login-password").value = p;
                document.getElementById("login-submit").click();
            } else {
                const errMsg = data.detail || "Signup failed. Please try again.";
                showAuthError(errMsg);
            }
        } catch (e) {
            showAuthError("Network error. Please check your connection.");
        }
    };

    // Tab Switching
    const tabVarga = document.getElementById("tab-varga");
    const tabDasha = document.getElementById("tab-dasha");
    const tabAdvanced = document.getElementById("tab-advanced");
    const tabPerson = document.getElementById("tab-person");
    tabPerson.onclick = () => switchTab('person');
    tabVarga.onclick = () => switchTab('chart');
    tabDasha.onclick = () => switchTab('dasha');
    if (tabAdvanced) tabAdvanced.onclick = () => switchTab('advanced');

    function switchTab(t) {
        const sections = ['person', 'chart', 'dasha', 'advanced'];
        sections.forEach(x => {
            const el = document.getElementById(x + '-section');
            if (el) el.style.display = 'none';
        });
        ['tab-person', 'tab-varga', 'tab-dasha', 'tab-advanced'].forEach(x => {
            const el = document.getElementById(x);
            if (el) el.classList.remove('active');
        });
        const targetSection = document.getElementById(t + '-section');
        if (targetSection) {
            // Use flex for chart/dasha/person so their inner scroll containers work
            targetSection.style.display = 'flex';
            targetSection.style.flexDirection = 'column';
        }
        const tabEl = document.getElementById('tab-' + (t === 'chart' ? 'varga' : t));
        if (tabEl) tabEl.classList.add('active');
    }

    // Mobile Visuals Close
    if (closeMenuBtn) {
        closeMenuBtn.onclick = () => visualPanel.classList.remove("menu-open");
    }
});

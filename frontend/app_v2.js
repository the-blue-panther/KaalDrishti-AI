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
    
    // Sidebar & Navigation
    const sidebar = document.getElementById("sidebar");
    const sidebarToggleBtn = document.getElementById("sidebar-toggle-btn");
    const closeSidebarBtn = document.getElementById("close-sidebar-btn");
    const visualPanel = document.getElementById("visual-panel");
    const mobileMenuBtn = document.getElementById("mobile-menu-btn");
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
                // If no profile active, maybe load the first one automatically
                if (!currentProfile) {
                    loadProfile(profilesCache[0].seeker_name);
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
            item.className = "profile-item";
            if (currentProfile && currentProfile.seeker_name === p.seeker_name) {
                item.style.borderColor = "var(--gold-accent)";
                item.style.background = "rgba(255, 184, 108, 0.05)";
            }

            item.innerHTML = `
                <div class="profile-info">
                    <span class="profile-name">${p.seeker_name}</span>
                    <span class="profile-sub">${p.gender} | ${new Date(p.local_time.split(' ')[0]).toLocaleDateString()}</span>
                </div>
                <button class="profile-actions-btn" data-name="${p.seeker_name}">⋮</button>
            `;

            // 1-Click Load
            item.onclick = (e) => {
                if (e.target.classList.contains('profile-actions-btn')) return;
                loadProfile(p.seeker_name);
                if (window.innerWidth < 1200) closeSidebar();
            };

            // 3-Dot Menu — works with both mouse click and mobile touch
            const actionBtn = item.querySelector('.profile-actions-btn');
            const openMenu = (e) => {
                e.stopPropagation();
                e.preventDefault();
                showContextMenu(e, p.seeker_name);
            };
            actionBtn.addEventListener('click', openMenu);
            actionBtn.addEventListener('touchend', openMenu, { passive: false });

            profileListContainer.appendChild(item);
        });
    }

    async function loadProfile(profileName) {
        const profile = profilesCache.find(p => p.seeker_name === profileName);
        if (!profile) return;

        currentProfile = profile;
        renderProfileList(profilesCache); // Update active state in UI

        // 1. Clear UI
        chatOutput.innerHTML = '<div class="message system-msg">Synchronizing with ' + profileName + '\'s celestial alignment...</div>';
        dashaBody.innerHTML = "";
        chartTabs.innerHTML = "";
        kundliImg.style.display = "none";
        kundliSkeleton.style.display = "block";
        document.getElementById("person-section").innerHTML = '<div class="no-selection-msg">Synthesizing charts...</div>';

        // 2. Hydrate History
        try {
            const hRes = await secureFetch(`/api/chat_history?profile=${encodeURIComponent(profileName)}`);
            const history = await hRes.json();
            chatOutput.innerHTML = "";
            if (history && history.length > 0) {
                let initFound = false;
                history.forEach(turn => {
                    if (turn.content === "[INITIALIZATION]") {
                        initFound = true;
                        return; // Skip rendering initialization message
                    }
                    if (initFound && turn.role === 'assistant') {
                        initFound = false;
                        // Replace the initialization error/response with a welcoming greeting
                        addMessage(`**Welcome!** The celestial charts have been successfully cast for ${profileName}.\n\nHow may I guide you today?`, "agent-msg");
                        return;
                    }
                    addMessage(turn.content, turn.role === 'user' ? 'user-msg' : 'agent-msg');
                });
            } else {
                addMessage(`Ready for ${profileName}'s reading. Ask your question below.`, "system-msg");
            }
        } catch (e) { console.warn("History failed", e); }

        // 3. Hydrate Charts/Panels
        try {
            const mRes = await secureFetch(`/api/chart_matrix?profile=${encodeURIComponent(profileName)}`);
            const mData = await mRes.json();
            if (mData.status === "success" && mData.deterministic_astronomy) {
                const astro = mData.deterministic_astronomy;
                renderTabs(astro.divisional_charts);
                renderDasha(astro.dasha_timeline);
                renderPersonalDetails(astro, profile);
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
                refreshProfileList();
            }
        } catch (e) { alert("Deletion failed: " + e.message); }
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

    ctxDeleteBtn.onclick = () => {
        deleteProfile(activeContextMenuProfile);
        contextMenu.style.display = "none";
    };

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

    async function processQuery(question, errorNodeToRemove = null) {
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
                    question: question
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
            } else {
                // If it's an API error, gracefully show the retry button below it
                let errMsg = data.detail || (isErrorString ? data.agent_response : "The system is currently busy analyzing other cosmic energies. Please try again.");
                
                // Truncate overly long technical errors for the UI
                if (errMsg.length > 200) errMsg = errMsg.substring(0, 200) + "...";
                
                showRetryMessage(question, `<strong>API Overload / Busy:</strong> ${errMsg}`);
            }
        } catch (e) {
            removeLoader();
            showRetryMessage(question, "Cosmic alignment lost. Check your connection.");
        } finally {
            sendBtn.disabled = false;
            sendBtn.classList.remove("loading");
            systemStatus.style.animationDuration = "2s";
        }
    }

    sendBtn.onclick = async () => {
        const question = questionInput.value.trim();
        if (!question || !currentProfile) return;

        addMessage(question, "user-msg");
        questionInput.value = "";
        
        await processQuery(question);
    };

    window.retryLastMessage = function(btnElement, questionText) {
        const errorNode = btnElement.closest('.message');
        processQuery(questionText, errorNode);
    };

    function showRetryMessage(questionText, customMsg) {
        // Build an elegant retry button inside the system message
        const escQuestion = questionText.replace(/'/g, "\\'").replace(/"/g, '\\"');
        const btnHtml = `<div style="margin-top: 15px;"><button class="retry-action-btn" onclick="window.retryLastMessage(this, '${escQuestion}')">⟳ Retry Request</button></div>`;
        addMessage(`${customMsg} ${btnHtml}`, "system-msg");
    }

    // --- HELPERS ---
    function addMessage(text, type) {
        const msg = document.createElement("div");
        msg.className = `message ${type}`;
        if (type === 'agent-msg' && window.marked) {
            msg.innerHTML = marked.parse(text);
            
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

    function renderDasha(timeline) {
        dashaBody.innerHTML = "";
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

    document.getElementById("login-submit").onclick = async () => {
        const u = document.getElementById("login-username").value;
        const p = document.getElementById("login-password").value;
        const formData = new URLSearchParams();
        formData.append("username", u); formData.append("password", p);
        const res = await fetch("/api/token", { method: "POST", body: formData });
        const data = await res.json();
        if (res.ok && data.access_token) {
            localStorage.setItem("astra_auth_token", data.access_token);
            jwtToken = data.access_token;
            checkAuth();
        } else alert("Login failed");
    };

    document.getElementById("signup-submit").onclick = async () => {
        const u = document.getElementById("signup-username").value;
        const p = document.getElementById("signup-password").value;
        if (p !== document.getElementById("signup-confirm").value) { alert("Match passwords"); return; }
        const res = await fetch("/api/signup", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({ username: u, password: p })
        });
        if (res.ok) {
            document.getElementById("login-username").value = u;
            document.getElementById("login-password").value = p;
            document.getElementById("login-submit").click();
        } else alert("Signup failed");
    };

    // Tab Switching
    const tabVarga = document.getElementById("tab-varga");
    const tabDasha = document.getElementById("tab-dasha");
    const tabPerson = document.getElementById("tab-person");
    tabPerson.onclick = () => switchTab('person');
    tabVarga.onclick = () => switchTab('chart');
    tabDasha.onclick = () => switchTab('dasha');

    function switchTab(t) {
        const sections = ['person', 'chart', 'dasha'];
        sections.forEach(x => {
            const el = document.getElementById(x + '-section');
            if (el) el.style.display = 'none';
        });
        ['tab-person', 'tab-varga', 'tab-dasha'].forEach(x => {
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
    mobileMenuBtn.onclick = () => {
        visualPanel.classList.add("menu-open");
        // Mutual exclusivity on mobile
        if (window.innerWidth < 768) {
            sidebar.classList.remove("open");
            sidebarOverlay.style.display = "none";
        }
    };
    closeMenuBtn.onclick = () => visualPanel.classList.remove("menu-open");
});

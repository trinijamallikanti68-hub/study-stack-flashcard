/**
 * FlashCard App — Frontend JavaScript
 * All data comes from the Python backend via fetch() REST API calls
 * Backend: http://localhost:5000
 */

const API_BASE = "";   // same origin — Python serves both API + static files

// ── API CLIENT ────────────────────────────────────────────────
const api = {
  async get(path) {
    addLog("GET", path);
    const res = await fetch(API_BASE + "/api" + path);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async post(path, data) {
    addLog("POST", path);
    const res = await fetch(API_BASE + "/api" + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async put(path, data) {
    addLog("PUT", path);
    const res = await fetch(API_BASE + "/api" + path, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async del(path) {
    addLog("DELETE", path);
    const res = await fetch(API_BASE + "/api" + path, { method: "DELETE" });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};

// ── STATE ─────────────────────────────────────────────────────
let allDecks      = [];
let allCards      = [];
let currentView   = "home";
let deckFilter    = "all";
let statusFilter  = "all";

let editingDeckId = null;
let editingCardId = null;
let selEmoji      = "📚";
let selColor      = "blue";

const EMOJIS = ["🧩","💻","🧮","📚","🔬","🌍","⚗️","🎵","🧬","📐","🔭","🎯","🧠","📖","⚽","🌿","🔐","🧪"];
const COLORS  = ["blue","green","amber","purple","red"];
const CHEX    = { blue:"#2d6be4", green:"#1f8a5e", amber:"#b07820", purple:"#6b3fa0", red:"#c0392b" };

const study = {
  deckId:     null,
  queue:      [],
  idx:        0,
  knowCount:  0,
  againCount: 0,
  isFlipped:  false,
  shuffleOn:  false,
};

// ── NAVIGATION ────────────────────────────────────────────────
function goto(view) {
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
  document.getElementById("view-" + view).classList.add("active");
  document.getElementById("tab-" + view).classList.add("active");
  currentView = view;

  if (view === "home")  loadHome();
  if (view === "decks") loadDecks();
  if (view === "study") loadStudySidebar();
}

// ── HOME ──────────────────────────────────────────────────────
async function loadHome() {
  // Parallel API calls
  const [stats, decks] = await Promise.all([
    api.get("/stats"),
    api.get("/decks"),
  ]);
  allDecks = decks;

  // Stats
  document.getElementById("home-stats").innerHTML = `
    <div class="stat-card">
      <div class="stat-val" style="color:var(--blue)">${stats.total_decks}</div>
      <div class="stat-lbl">📚 Decks</div>
    </div>
    <div class="stat-card">
      <div class="stat-val" style="color:var(--purple)">${stats.total_cards}</div>
      <div class="stat-lbl">🃏 Cards</div>
    </div>
    <div class="stat-card">
      <div class="stat-val" style="color:var(--green)">${stats.known}</div>
      <div class="stat-lbl">✓ Mastered</div>
    </div>
    <div class="stat-card">
      <div class="stat-val" style="color:var(--amber)">${stats.mastered_pct}%</div>
      <div class="stat-lbl">📈 Progress</div>
    </div>`;

  // Decks grid
  document.getElementById("home-decks").innerHTML =
    decks.map(d => deckCardHTML(d)).join("") +
    `<div class="add-deck-card" onclick="openDeckModal()">
      <div style="font-size:30px">＋</div>New Deck
    </div>`;
}

function deckCardHTML(d) {
  return `
  <div class="deck-card dc-${d.color}">
    <div class="dc-top">
      <div class="dc-emoji">${d.emoji}</div>
      <div class="dc-menu">
        <button class="dc-menu-btn" onclick="event.stopPropagation();editDeck('${d.id}')" title="Edit">✏️</button>
        <button class="dc-menu-btn" onclick="event.stopPropagation();deleteDeck('${d.id}')" title="Delete">🗑</button>
      </div>
    </div>
    <div class="dc-name">${esc(d.name)}</div>
    <div class="dc-meta">${d.card_count} card${d.card_count !== 1 ? "s" : ""} · ${d.mastered_pct}% mastered</div>
    <div class="dc-pbar"><div class="dc-pbar-fill" style="width:${d.mastered_pct}%"></div></div>
    <div class="dc-btns">
      <button class="dc-btn" onclick="event.stopPropagation();openDeckCards('${d.id}')">📋 Cards</button>
      <button class="dc-btn study" onclick="event.stopPropagation();startStudy('${d.id}')">▶ Study</button>
    </div>
  </div>`;
}

// ── DECKS PAGE ────────────────────────────────────────────────
async function loadDecks() {
  const [decks, cards] = await Promise.all([
    api.get("/decks"),
    api.get("/cards"),
  ]);
  allDecks = decks;
  allCards = cards;

  // Deck grid
  document.getElementById("decks-grid").innerHTML =
    decks.map(d => deckCardHTML(d)).join("") +
    `<div class="add-deck-card" onclick="openDeckModal()"><div style="font-size:30px">＋</div>New Deck</div>`;

  // Deck filter chips
  document.getElementById("deck-chips").innerHTML =
    `<button class="chip${deckFilter==="all"?" active":""}" onclick="setDeckFilter('all',this)">All Decks</button>` +
    decks.map(d =>
      `<button class="chip${deckFilter===d.id?" active":""}" onclick="setDeckFilter('${d.id}',this)">${d.emoji} ${esc(d.name)}</button>`
    ).join("");

  renderCardsTable();
}

function setDeckFilter(id, btn) {
  deckFilter = id;
  document.querySelectorAll("#deck-chips .chip").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  renderCardsTable();
}

function setStatusFilter(s, btn) {
  statusFilter = s;
  document.querySelectorAll(".status-chips .chip").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  renderCardsTable();
}

function openDeckCards(deckId) {
  deckFilter = deckId;
  goto("decks");
}

function renderCardsTable() {
  let cards = allCards;
  if (deckFilter !== "all")   cards = cards.filter(c => c.deck_id === deckFilter);
  if (statusFilter !== "all") cards = cards.filter(c => c.status  === statusFilter);

  const el = document.getElementById("cards-table");
  if (!cards.length) {
    el.innerHTML = `<div class="empty-state"><div class="ei">🃏</div><h3>No cards here</h3><p>Add a card to get started</p><button class="btn btn-primary" onclick="openCardModal()">＋ Add Card</button></div>`;
    return;
  }

  el.innerHTML = cards.map(c => {
    const dotCls  = c.status === "known" ? "dot-known" : c.status === "again" ? "dot-again" : "dot-new";
    const statLbl = c.status === "known" ? "✓ Known"   : c.status === "again" ? "↺ Again"   : "🆕 New";
    return `
    <div class="card-row">
      <div class="cr-dot ${dotCls}"></div>
      <div class="cr-body">
        <div class="cr-q">${esc(c.question)}</div>
        <div class="cr-a">${esc(c.answer)}</div>
      </div>
      ${c.tag ? `<span class="cr-tag">#${esc(c.tag)}</span>` : ""}
      <span class="cr-status ${c.status}">${statLbl}</span>
      <div class="cr-actions">
        <button class="icon-btn" onclick="editCard('${c.id}')">✏️</button>
        <button class="icon-btn del" onclick="deleteCard('${c.id}')">🗑</button>
      </div>
    </div>`;
  }).join("");
}

// ── STUDY ─────────────────────────────────────────────────────
async function loadStudySidebar() {
  const decks = await api.get("/decks");
  allDecks = decks;

  document.getElementById("aside-decks").innerHTML = decks.map(d => `
    <div class="aside-deck-item${study.deckId === d.id ? " active" : ""}" onclick="selectStudyDeck('${d.id}')">
      <div class="adi-emoji">${d.emoji}</div>
      <div class="adi-body">
        <div class="adi-name">${esc(d.name)}</div>
        <div class="adi-meta">${d.card_count} cards · ${d.mastered_pct}%</div>
      </div>
    </div>`).join("");

  // Auto-select first deck
  if (!study.deckId && decks.length) selectStudyDeck(decks[0].id);
}

async function selectStudyDeck(deckId) {
  study.deckId = deckId;
  document.querySelectorAll(".aside-deck-item").forEach(el => el.classList.remove("active"));
  document.querySelectorAll(".aside-deck-item").forEach(el => {
    if (el.getAttribute("onclick")?.includes(deckId)) el.classList.add("active");
  });
  await startStudy(deckId);
}

async function startStudy(deckId) {
  if (currentView !== "study") { goto("study"); return; }
  study.deckId     = deckId;
  study.isFlipped  = false;
  study.idx        = 0;
  study.knowCount  = 0;
  study.againCount = 0;

  const cards = await api.get(`/cards?deck_id=${deckId}`);

  // Priority order: new → again → known
  const ordered = [
    ...cards.filter(c => c.status === "new"),
    ...cards.filter(c => c.status === "again"),
    ...cards.filter(c => c.status === "known"),
  ];

  study.queue = study.shuffleOn ? shuffle(ordered) : ordered;

  hideAllStudyStates();
  if (!cards.length) { document.getElementById("st-empty").style.display = "block"; return; }
  document.getElementById("st-card").style.display = "flex";

  const deck = allDecks.find(d => d.id === deckId);
  document.getElementById("deck-label").textContent = deck ? `${deck.emoji}  ${deck.name}` : "";

  showStudyCard();
  updateSidebarStats();
}

function showStudyCard() {
  const { queue, idx } = study;
  if (!queue.length || idx >= queue.length) { showCompletion(); return; }

  study.isFlipped = false;
  document.getElementById("flashcard").classList.remove("flipped");
  document.getElementById("sc-know").disabled  = true;
  document.getElementById("sc-again").disabled = true;

  const c     = queue[idx];
  const total = queue.length;
  const pct   = Math.round((idx / total) * 100);

  document.getElementById("fc-q").textContent    = c.question;
  document.getElementById("fc-a").textContent    = c.answer;
  document.getElementById("fc-tag-f").textContent = c.tag || "Card";
  document.getElementById("fc-tag-b").textContent = c.tag || "Card";
  document.getElementById("prog-text").textContent = `${idx + 1} / ${total}`;
  document.getElementById("prog-pct").textContent  = pct + "%";
  document.getElementById("prog-bar").style.width  = pct + "%";

  renderDots();
  updateSidebarStats();
  document.getElementById("sess-know").textContent  = study.knowCount;
  document.getElementById("sess-again").textContent = study.againCount;
  document.getElementById("sess-left").textContent  = total - idx;
}

function flipCard() {
  if (!study.queue.length || study.idx >= study.queue.length) return;
  study.isFlipped = !study.isFlipped;
  document.getElementById("flashcard").classList.toggle("flipped", study.isFlipped);
  document.getElementById("sc-know").disabled  = !study.isFlipped;
  document.getElementById("sc-again").disabled = !study.isFlipped;
}

async function rateCard(result) {
  const card = study.queue[study.idx];
  const newStatus = result === "know" ? "known" : "again";

  // PUT to Python backend
  await api.put(`/cards/${card.id}`, { status: newStatus });
  card.status = newStatus;   // update local copy too

  if (result === "know") study.knowCount++;
  else study.againCount++;

  study.idx++;
  if (study.idx >= study.queue.length) showCompletion();
  else showStudyCard();
}

function skipCard() {
  study.idx++;
  if (study.idx >= study.queue.length) showCompletion();
  else showStudyCard();
}

function restartStudy() {
  hideAllStudyStates();
  document.getElementById("st-card").style.display = "flex";
  startStudy(study.deckId);
}

async function retryWrong() {
  const cards = await api.get(`/cards?deck_id=${study.deckId}&status=again`);
  if (!cards.length) { showToast("🎉 No wrong cards — all mastered!"); return; }
  study.queue      = shuffle(cards);
  study.idx        = 0;
  study.knowCount  = 0;
  study.againCount = 0;
  study.isFlipped  = false;
  hideAllStudyStates();
  document.getElementById("st-card").style.display = "flex";
  showStudyCard();
}

function showCompletion() {
  hideAllStudyStates();
  const total = study.queue.length || 1;
  const kPct  = Math.round((study.knowCount  / total) * 100);
  const aPct  = Math.round((study.againCount / total) * 100);

  let icon, title, sub;
  if (kPct === 100)    { icon = "🏆"; title = "Perfect Score!";    sub = "Every single card nailed. Outstanding!"; }
  else if (kPct >= 75) { icon = "🎉"; title = "Great Job!";         sub = `${study.knowCount} of ${total} correct. Keep it up!`; }
  else if (kPct >= 50) { icon = "💪"; title = "Good Effort!";       sub = `${study.knowCount} of ${total}. Review the ones you missed.`; }
  else                  { icon = "📖"; title = "Keep Practicing!";   sub = `${study.knowCount} of ${total}. Practice makes perfect!`; }

  document.getElementById("comp-icon").textContent  = icon;
  document.getElementById("comp-title").textContent = title;
  document.getElementById("comp-sub").textContent   = sub;
  document.getElementById("rb-know-val").textContent  = `${study.knowCount}/${total}`;
  document.getElementById("rb-again-val").textContent = `${study.againCount}/${total}`;
  document.getElementById("st-done").style.display = "flex";
  document.getElementById("st-done").style.flexDirection = "column";
  document.getElementById("st-done").style.alignItems = "center";

  document.getElementById("prog-bar").style.width = "100%";
  document.getElementById("prog-pct").textContent = "100%";
  renderDots();

  setTimeout(() => {
    document.getElementById("rb-know").style.width  = kPct + "%";
    document.getElementById("rb-again").style.width = aPct + "%";
  }, 100);
}

function hideAllStudyStates() {
  ["st-pick","st-empty","st-card","st-done"].forEach(id => {
    document.getElementById(id).style.display = "none";
  });
}

function renderDots() {
  const el = document.getElementById("dots-row");
  el.innerHTML = study.queue.map((c, i) => {
    let cls = "dot";
    if (i < study.idx)      cls += c.status === "known" ? " known" : " again";
    else if (i === study.idx) cls += " curr";
    return `<div class="${cls}"></div>`;
  }).join("");
}

function updateSidebarStats() {
  document.getElementById("sb-know").textContent  = study.knowCount;
  document.getElementById("sb-again").textContent = study.againCount;
  document.getElementById("sb-rem").textContent   = Math.max(0, study.queue.length - study.idx);
}

function toggleShuffle() {
  study.shuffleOn = !study.shuffleOn;
  const el = document.getElementById("shuffle-val");
  el.textContent = study.shuffleOn ? "ON" : "OFF";
  el.classList.toggle("on", study.shuffleOn);
  if (study.deckId) { showToast(study.shuffleOn ? "Shuffle ON 🔀" : "Shuffle OFF"); startStudy(study.deckId); }
}

// ── DECK MODAL ────────────────────────────────────────────────
function openDeckModal(id = null) {
  editingDeckId = id;
  const deck = id ? allDecks.find(d => d.id === id) : null;
  selEmoji = deck?.emoji || EMOJIS[0];
  selColor = deck?.color || "blue";

  document.getElementById("dm-title").textContent = deck ? "Edit Deck" : "New Deck";
  document.getElementById("dm-name").value = deck?.name || "";

  document.getElementById("dm-emoji-grid").innerHTML = EMOJIS.map(e =>
    `<div class="emoji-opt${e === selEmoji ? " on" : ""}" onclick="pickEmoji('${e}')">${e}</div>`
  ).join("");

  document.getElementById("dm-color-row").innerHTML = COLORS.map(c =>
    `<div class="color-dot${c === selColor ? " on" : ""}" style="background:${CHEX[c]}" onclick="pickColor('${c}')"></div>`
  ).join("");

  document.getElementById("deck-overlay").classList.add("show");
  setTimeout(() => document.getElementById("dm-name").focus(), 80);
}

function editDeck(id) { openDeckModal(id); }
function closeDeckModal() { document.getElementById("deck-overlay").classList.remove("show"); }
function pickEmoji(e) { selEmoji = e; document.querySelectorAll("#dm-emoji-grid .emoji-opt").forEach(el => el.classList.toggle("on", el.textContent === e)); }
function pickColor(c) { selColor = c; document.querySelectorAll("#dm-color-row .color-dot").forEach((el, i) => el.classList.toggle("on", COLORS[i] === c)); }

async function saveDeck() {
  const name = document.getElementById("dm-name").value.trim();
  if (!name) { showToast("Enter a deck name!"); return; }
  const payload = { name, emoji: selEmoji, color: selColor };

  try {
    if (editingDeckId) {
      await api.put(`/decks/${editingDeckId}`, payload);
      showToast("Deck updated ✓");
    } else {
      await api.post("/decks", payload);
      showToast("Deck created 🎉");
    }
    closeDeckModal();
    if (currentView === "home")  loadHome();
    if (currentView === "decks") loadDecks();
    if (currentView === "study") loadStudySidebar();
  } catch (e) { showToast("Error saving deck"); }
}

async function deleteDeck(id) {
  if (!confirm("Delete this deck and all its cards?")) return;
  try {
    await api.del(`/decks/${id}`);
    showToast("Deck deleted.");
    if (study.deckId === id) study.deckId = null;
    if (currentView === "home")  loadHome();
    if (currentView === "decks") loadDecks();
  } catch (e) { showToast("Error deleting deck"); }
}

// ── CARD MODAL ────────────────────────────────────────────────
function openCardModal(deckId = null) {
  editingCardId = null;
  document.getElementById("cm-title").textContent = "Add Card";
  document.getElementById("cm-q").value = "";
  document.getElementById("cm-a").value = "";
  document.getElementById("cm-tag").value = "";

  const preferred = deckId || deckFilter !== "all" ? deckFilter : allDecks[0]?.id;
  document.getElementById("cm-deck").innerHTML = allDecks.map(d =>
    `<option value="${d.id}" ${d.id === preferred ? "selected" : ""}>${d.emoji} ${esc(d.name)}</option>`
  ).join("");

  document.getElementById("card-overlay").classList.add("show");
  setTimeout(() => document.getElementById("cm-q").focus(), 80);
}

function editCard(id) {
  const card = allCards.find(c => c.id === id);
  if (!card) return;
  editingCardId = id;

  document.getElementById("cm-title").textContent = "Edit Card";
  document.getElementById("cm-q").value   = card.question;
  document.getElementById("cm-a").value   = card.answer;
  document.getElementById("cm-tag").value = card.tag || "";

  document.getElementById("cm-deck").innerHTML = allDecks.map(d =>
    `<option value="${d.id}" ${d.id === card.deck_id ? "selected" : ""}>${d.emoji} ${esc(d.name)}</option>`
  ).join("");

  document.getElementById("card-overlay").classList.add("show");
  setTimeout(() => document.getElementById("cm-q").focus(), 80);
}

function closeCardModal() { document.getElementById("card-overlay").classList.remove("show"); }

async function saveCard() {
  const question = document.getElementById("cm-q").value.trim();
  const answer   = document.getElementById("cm-a").value.trim();
  const deck_id  = document.getElementById("cm-deck").value;
  const tag      = document.getElementById("cm-tag").value.trim();

  if (!question || !answer) { showToast("Fill in question and answer!"); return; }

  try {
    if (editingCardId) {
      await api.put(`/cards/${editingCardId}`, { question, answer, deck_id, tag });
      showToast("Card updated ✓");
    } else {
      await api.post("/cards", { question, answer, deck_id, tag });
      showToast("Card added 🃏");
    }
    closeCardModal();
    loadDecks();
  } catch (e) { showToast("Error saving card"); }
}

async function deleteCard(id) {
  if (!confirm("Delete this card?")) return;
  try {
    await api.del(`/cards/${id}`);
    showToast("Card deleted.");
    loadDecks();
  } catch (e) { showToast("Error deleting card"); }
}

// ── API LOG ────────────────────────────────────────────────────
function addLog(method, path) {
  const el = document.createElement("div");
  el.className = `log-entry log-${method.toLowerCase()}`;
  el.textContent = `${new Date().toLocaleTimeString()}  ${method.padEnd(6)}  /api${path}`;
  const body = document.getElementById("api-log-body");
  body.prepend(el);
  while (body.children.length > 30) body.removeChild(body.lastChild);
}

function toggleApiLog() {
  document.getElementById("api-log").classList.toggle("show");
}

// ── UTILS ─────────────────────────────────────────────────────
function esc(s) { return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }
function shuffle(arr) { return [...arr].sort(() => Math.random() - 0.5); }

function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(t._t);
  t._t = setTimeout(() => t.classList.remove("show"), 2400);
}

// ── KEYBOARD ──────────────────────────────────────────────────
document.addEventListener("keydown", e => {
  if (["INPUT","TEXTAREA","SELECT"].includes(e.target.tagName)) return;
  if (currentView !== "study") return;
  if (e.key === " " || e.key === "ArrowUp") { e.preventDefault(); flipCard(); }
  if (e.key === "ArrowRight") skipCard();
  if ((e.key === "k" || e.key === "K") && study.isFlipped) rateCard("know");
  if ((e.key === "l" || e.key === "L") && study.isFlipped) rateCard("again");
});

// ── CLOSE OVERLAYS ON BACKDROP CLICK ─────────────────────────
document.querySelectorAll(".overlay").forEach(o => {
  o.addEventListener("click", e => { if (e.target === o) o.classList.remove("show"); });
});

// ── BOOT ──────────────────────────────────────────────────────
window.addEventListener("load", () => loadHome());
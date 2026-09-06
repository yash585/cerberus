(function () {
  "use strict";


  const state = {
    sessionId: generateSessionId(),
    messages: [],
    sending: false
  };


  document.getElementById("session-id").textContent =
    state.sessionId;


  function generateSessionId() {
    return "sess_" +
      Math.random().toString(36).slice(2, 8);
  }


  function nowTime() {
    const d = new Date();

    return d.toLocaleTimeString(
      [],
      {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit"
      }
    );
  }


  function escapeHtml(str) {

    const div = document.createElement("div");

    div.textContent = str;

    return div.innerHTML;
  }


  async function checkBackendStatus() {

    try {

      const response = await fetch("/health");

      if (!response.ok) {
        throw new Error();
      }


      const modelStatus =
        document.querySelector(
          ".status-row:nth-last-child(4) .v"
        );

      const kbStatus =
        document.querySelector(
          ".status-row:nth-last-child(3) .v"
        );

      const toolsStatus =
        document.querySelector(
          ".status-row:nth-last-child(2) .v"
        );


      if (modelStatus) {

        modelStatus.innerHTML =
          '<span class="dot"></span>ONLINE';

      }


      if (kbStatus) {

        kbStatus.innerHTML =
          '<span class="dot"></span>CONNECTED';

      }


      if (toolsStatus) {

        toolsStatus.innerHTML =
          '<span class="dot"></span>5 ENABLED';

      }

    } catch (error) {

      console.error(
        "Backend health check failed:",
        error
      );

    }

  }


  checkBackendStatus();


  /* ---------------- VIEW SWITCHING ---------------- */


  const navItems =
    document.querySelectorAll(
      ".nav-item[data-view]"
    );


  const views = {
    chat:
      document.getElementById("view-chat"),

    kb:
      document.getElementById("view-kb"),

    incidents:
      document.getElementById("view-incidents"),

    employees:
      document.getElementById("view-employees")
  };


  navItems.forEach((btn) => {

    btn.addEventListener("click", () => {

      navItems.forEach((item) => {
        item.classList.remove("active");
      });


      btn.classList.add("active");


      Object.values(views).forEach((view) => {
        view.classList.remove("active");
      });


      views[
        btn.dataset.view
      ].classList.add("active");

    });

  });


  /* ---------------- CHAT ---------------- */


  const messagesEl =
    document.getElementById("messages");

  const inputEl =
    document.getElementById("composer-input");

  const sendBtn =
    document.getElementById("send-btn");


  function addMessage(role, html, opts = {}) {

    const wrap =
      document.createElement("div");

    wrap.className =
      "msg " + role;


    const avatar =
      document.createElement("div");

    avatar.className =
      "avatar " + role;

    avatar.textContent =
      role === "user"
        ? "YOU"
        : "C";


    const bubble =
      document.createElement("div");

    bubble.className =
      "bubble";

    bubble.innerHTML = html;


    if (opts.meta) {

      const meta =
        document.createElement("div");

      meta.className =
        "meta-line";

      meta.textContent =
        opts.meta;

      bubble.appendChild(meta);

    }


    wrap.appendChild(avatar);
    wrap.appendChild(bubble);

    messagesEl.appendChild(wrap);


    messagesEl.scrollTop =
      messagesEl.scrollHeight;


    return wrap;

  }


  function addTypingIndicator() {

    const wrap =
      document.createElement("div");

    wrap.className =
      "msg agent";

    wrap.id =
      "typing-indicator";


    wrap.innerHTML =
      '<div class="avatar agent">C</div>' +
      '<div class="bubble">' +
      '<div class="typing">' +
      '<span></span>' +
      '<span></span>' +
      '<span></span>' +
      '</div>' +
      '</div>';


    messagesEl.appendChild(wrap);


    messagesEl.scrollTop =
      messagesEl.scrollHeight;

  }


  function removeTypingIndicator() {

    const element =
      document.getElementById(
        "typing-indicator"
      );


    if (element) {
      element.remove();
    }

  }


  addMessage(
    "agent",

    "<p>CERBERUS online. I can answer security questions, search the internal knowledge base, retrieve incident records, and access asset information.</p>" +

    "<p>Ask me about a specific incident, asset, MITRE technique, or security procedure.</p>"
  );


  async function handleSend() {

    const text =
      inputEl.value.trim();


    if (!text || state.sending) {
      return;
    }


    state.sending = true;

    sendBtn.disabled = true;

    inputEl.value = "";

    inputEl.style.height = "auto";


    addMessage(
      "user",
      escapeHtml(text)
    );


    addTypingIndicator();


    try {

      const response =
        await fetch("/chat", {

          method: "POST",

          headers: {
            "Content-Type":
              "application/json"
          },

          body: JSON.stringify({
            message: text
          })

        });


      if (!response.ok) {

        throw new Error(
          "Failed to contact CERBERUS backend"
        );

      }


      const data =
        await response.json();


      removeTypingIndicator();


      if (
        data.tool_calls &&
        data.tool_calls.length
      ) {

        data.tool_calls.forEach((tool) => {

          logToolEvent(
            tool.name,
            tool.status,
            tool.detail
          );

        });

      }


      addMessage(
        "agent",
        formatResponse(data.response),
        {
          meta:
            data.tool_calls &&
            data.tool_calls.length

              ? `tools used · ${nowTime()}`

              : `direct response · ${nowTime()}`
        }
      );


    } catch (error) {

      console.error(error);


      removeTypingIndicator();


      addMessage(
        "agent",

        "<p>Unable to connect to the CERBERUS backend.</p>" +

        "<p>Please verify that the FastAPI server is running and try again.</p>",

        {
          meta:
            `connection error · ${nowTime()}`
        }
      );

    } finally {

      state.sending = false;

      sendBtn.disabled = false;

      inputEl.focus();

    }

  }


  function formatResponse(text) {

    if (!text) {
      return "<p>No response received.</p>";
    }


    let safeText =
      escapeHtml(text);


    safeText =
      safeText.replace(
        /\n\n/g,
        "</p><p>"
      );


    safeText =
      safeText.replace(
        /\n/g,
        "<br>"
      );


    return "<p>" +
      safeText +
      "</p>";

  }


  sendBtn.addEventListener(
    "click",
    handleSend
  );


  inputEl.addEventListener(
    "keydown",

    (event) => {

      if (
        event.key === "Enter" &&
        !event.shiftKey
      ) {

        event.preventDefault();

        handleSend();

      }

    }
  );


  inputEl.addEventListener(
    "input",

    () => {

      inputEl.style.height =
        "auto";


      inputEl.style.height =
        Math.min(
          inputEl.scrollHeight,
          140
        ) + "px";

    }
  );


  document
    .querySelectorAll(".quick-chip")
    .forEach((chip) => {

      chip.addEventListener(
        "click",

        () => {

          inputEl.value =
            chip.dataset.prompt;

          handleSend();

        }
      );

    });


  /* ---------------- TOOL ACTIVITY ---------------- */


  const activityFeed =
    document.getElementById(
      "activity-feed"
    );


  let activityStarted =
    false;


  function logToolEvent(
    name,
    status,
    detail
  ) {

    if (!activityStarted) {

      activityFeed.innerHTML = "";

      activityStarted = true;

    }


    const entry =
      document.createElement("div");


    entry.className =
      "tool-event " + status;


    entry.innerHTML = `

      <div class="tool-event-head">

        <span class="tool-name">
          ${escapeHtml(name)}
        </span>

        <span class="tool-status ${status}">
          ${escapeHtml(status.toUpperCase())}
        </span>

      </div>

      <div class="tool-detail">
        ${escapeHtml(detail || "")}
      </div>

      <div
        class="tool-time"
        style="margin-top:4px;"
      >
        ${nowTime()}
      </div>

    `;


    activityFeed.appendChild(entry);


    activityFeed.scrollTop =
      activityFeed.scrollHeight;

  }


  /* ---------------- KNOWLEDGE BASE ---------------- */


  const kbList =
    document.getElementById("kb-list");

  const kbSearchInput =
    document.getElementById(
      "kb-search-input"
    );

  const kbSearchBtn =
    document.getElementById(
      "kb-search-btn"
    );


  function renderKbList(items) {

    kbList.innerHTML = "";


    if (!items.length) {

      kbList.innerHTML =
        '<div class="empty-state">' +
        'No matching documents.' +
        '</div>';

      return;

    }


    items.forEach((doc) => {

      const card =
        document.createElement("div");


      card.className =
        "list-card";


      card.innerHTML = `

        <div class="list-card-title">

          ${escapeHtml(doc.title)}

        </div>

        <div class="list-card-meta">

          <span>
            ${escapeHtml(doc.id)}
          </span>

        </div>

        <div class="list-card-snippet">

          ${escapeHtml(doc.content)}

        </div>

      `;


      kbList.appendChild(card);

    });

  }


  async function loadKnowledgeBase(query = "") {

    try {

      let url =
        "/api/knowledge-base";


      if (query) {

        url +=
          "?q=" +
          encodeURIComponent(query);

      }


      const response =
        await fetch(url);


      if (!response.ok) {

        throw new Error(
          "Failed to load knowledge base"
        );

      }


      const data =
        await response.json();


      renderKbList(data);


    } catch (error) {

      console.error(error);


      kbList.innerHTML =
        '<div class="empty-state">' +
        'Unable to load knowledge base.' +
        '</div>';

    }

  }


  function searchKb() {

    const query =
      kbSearchInput.value.trim();


    loadKnowledgeBase(query);

  }


  kbSearchBtn.addEventListener(
    "click",
    searchKb
  );


  kbSearchInput.addEventListener(
    "keydown",

    (event) => {

      if (event.key === "Enter") {
        searchKb();
      }

    }
  );


  loadKnowledgeBase();


  /* ---------------- INCIDENTS ---------------- */


  const incidentList =
    document.getElementById(
      "incident-list"
    );


  function renderIncidents(items) {

    incidentList.innerHTML = "";


    if (!items.length) {

      incidentList.innerHTML =
        '<div class="empty-state">' +
        'No incident records found.' +
        '</div>';

      return;

    }


    items.forEach((incident) => {

      const card =
        document.createElement("div");


      card.className =
        "list-card";


      const severity =
        incident.severity.toLowerCase();


      card.innerHTML = `

        <div
          class="list-card-meta"
          style="margin-bottom:6px;"
        >

          <span>
            ${escapeHtml(incident.id)}
          </span>

          <span
            class="severity-pill ${severity}"
          >

            ${escapeHtml(
              incident.severity.toUpperCase()
            )}

          </span>

          <span>
            ${escapeHtml(incident.status)}
          </span>

          <span>
            ${escapeHtml(
              incident.affected_asset
            )}
          </span>

        </div>


        <div class="list-card-title">

          ${escapeHtml(incident.title)}

        </div>


        <div
          class="list-card-snippet"
          style="margin-top:6px;"
        >

          ${escapeHtml(
            incident.description
          )}

        </div>


        <div
          class="list-card-meta"
          style="margin-top:8px;"
        >

          <span>
            MITRE:
            ${escapeHtml(
              incident.mitre_technique
            )}
          </span>

          <span>
            Assigned:
            ${escapeHtml(
              incident.assigned_to
            )}
          </span>

        </div>

      `;


      incidentList.appendChild(card);

    });

  }


  async function loadIncidents() {

    try {

      const response =
        await fetch("/api/incidents");


      if (!response.ok) {

        throw new Error(
          "Failed to load incidents"
        );

      }


      const data =
        await response.json();


      renderIncidents(data);


    } catch (error) {

      console.error(error);


      incidentList.innerHTML =
        '<div class="empty-state">' +
        'Unable to load incident records.' +
        '</div>';

    }

  }


  loadIncidents();


  /* ---------------- ASSETS ---------------- */


  const employeeList =
    document.getElementById(
      "employee-list"
    );


  const empSearchInput =
    document.getElementById(
      "emp-search-input"
    );


  const empSearchBtn =
    document.getElementById(
      "emp-search-btn"
    );


  function renderAssets(items) {

    employeeList.innerHTML = "";


    if (!items.length) {

      employeeList.innerHTML =
        '<div class="empty-state">' +
        'No matching assets.' +
        '</div>';

      return;

    }


    items.forEach((asset) => {

      const card =
        document.createElement("div");


      card.className =
        "list-card";


      card.innerHTML = `

        <div class="list-card-meta">

          <span>
            ${escapeHtml(asset.hostname)}
          </span>

          <span>
            ${escapeHtml(asset.ip_address)}
          </span>

        </div>


        <div class="list-card-title">

          ${escapeHtml(
            asset.operating_system
          )}

          <span
            style="
              color:var(--text-dim);
              font-weight:400;
            "
          >

            —
            ${escapeHtml(
              asset.department
            )}

          </span>

        </div>


        <div
          class="list-card-snippet"
          style="margin-top:6px;"
        >

          Criticality:
          ${escapeHtml(asset.criticality)}

          · Owner:
          ${escapeHtml(asset.owner)}

        </div>

      `;


      employeeList.appendChild(card);

    });

  }


  async function loadAssets(query = "") {

    try {

      let url =
        "/api/assets";


      if (query) {

        url =
          "/api/assets/search?q=" +
          encodeURIComponent(query);

      }


      const response =
        await fetch(url);


      if (!response.ok) {

        throw new Error(
          "Failed to load assets"
        );

      }


      const data =
        await response.json();


      renderAssets(data);


    } catch (error) {

      console.error(error);


      employeeList.innerHTML =
        '<div class="empty-state">' +
        'Unable to load asset records.' +
        '</div>';

    }

  }


  function searchAssets() {

    const query =
      empSearchInput.value.trim();


    loadAssets(query);

  }


  empSearchBtn.addEventListener(
    "click",
    searchAssets
  );


  empSearchInput.addEventListener(
    "keydown",

    (event) => {

      if (event.key === "Enter") {
        searchAssets();
      }

    }
  );


  loadAssets();


  /* ---------------- PUBLIC API ---------------- */


  window.CERBERUS = {

    logToolEvent,

    addMessage,

    state

  };


})();
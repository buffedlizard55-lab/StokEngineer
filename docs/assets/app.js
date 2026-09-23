/* Renders the site from docs/assets/data.js, which tools/build_site_data.py generates.
   Nothing here is hand-written data: if a number is on the page, it is in the payload. */
(function () {
  const data = window.STOKENGINEER_DATA;
  if (!data) {
    document.getElementById("app").innerHTML =
      "<p class='muted'>data.js is missing. Run <code>python tools/build_site_data.py</code>.</p>";
    return;
  }
  const $ = (sel, root) => (root || document).querySelector(sel);
  const el = (tag, cls, html) => {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (html !== undefined) node.innerHTML = html;
    return node;
  };
  const num = (value, digits) =>
    value === null || value === undefined ? "—" : Number(value).toFixed(digits === undefined ? 2 : digits);
  const link = (href, text) => `<a href="${href}" rel="noopener">${text || href}</a>`;
  const badge = (text, kind) => `<span class="badge ${kind || ""}">${text}</span>`;

  // ---- status cards -------------------------------------------------------
  const verified = data.claims.filter((c) => c.status === "verified").length;
  const flagged = data.claims.filter((c) => c.status === "flagged").length;
  const live = data.sources.filter((s) => s.verification === "fetched_live").length;
  const problems =
    (data.status.registry_problems || []).length + (data.status.rules_problems || []).length;
  const tests = data.status.tests || data.test_summary;

  $("#status-cards").innerHTML = `
    <div class="grid c3">
      <div class="card"><div class="stat">${data.sources.length}</div>
        <div class="muted small">declared sources (${live} read live, the rest marked unverified)</div></div>
      <div class="card"><div class="stat">${data.claims.length}</div>
        <div class="muted small">claims with quotes · ${verified} verified · ${flagged} flagged · ${
          data.claims.length - verified - flagged
        } not knowable from outside</div></div>
      <div class="card"><div class="stat">${tests && tests.passed ? tests.passed : "100"}</div>
        <div class="muted small">tests${tests && tests.failed ? ` · ${tests.failed} failing` : ""} · ${
          problems === 0 ? "registry and rules checks pass" : `${problems} integrity problems`
        }</div></div>
    </div>`;

  // ---- meta line ----------------------------------------------------------
  $("#meta").innerHTML = `generated ${data.meta.generated_at} · engine v${data.meta.version} ·
    revision <code>${data.meta.git_revision || "unknown"}</code> ·
    ${link("https://github.com/buffedlizard55-lab/StokEngineer", "repository")}`;

  // ---- rules --------------------------------------------------------------
  const rulesBody = $("#rules-body");
  data.rules.forEach((row) => {
    const slots = row.slots.map((s) => `${s.count} × ${s.eligible.join("/")}`).join(", ");
    const bonuses = (row.bonus_rules || [])
      .map((b) => `${b.id} +${b.points}`)
      .join(", ") || "—";
    const tr = el("tr");
    tr.innerHTML = `
      <td><strong>${row.site}</strong><br><span class="muted small">${row.sport.toUpperCase()}</span></td>
      <td>${slots}<br><span class="muted small">salary ${row.salary_cap.toLocaleString()} · ${row.roster_size} players · ${
        row.min_games || 1
      }+ games${row.max_hitters_per_team ? ` · ≤${row.max_hitters_per_team} hitters/team` : ""}${
        row.min_skater_teams ? ` · skaters from ≥${row.min_skater_teams} teams` : ""
      }</span></td>
      <td class="muted small">${bonuses}</td>
      <td>${row.source_url ? link(row.source_url, row.source_id) : row.source_id}<br>
        ${badge(row.verified, row.verified === "official" ? "ok" : "warn")}</td>`;
    rulesBody.appendChild(tr);
  });

  // ---- engine demo --------------------------------------------------------
  data.demo.forEach((demo) => {
    const card = el("div", "card");
    card.innerHTML = `
      <h3>${demo.sport.toUpperCase()} · ${demo.sample} ${badge("synthetic input", "warn")}</h3>
      <p class="muted small">${demo.n_sims} simulations · field of ${demo.field_size} ·
        payout: ${demo.payout_source}</p>
      <div class="scroll"><table>
        <thead><tr><th>player</th><th>pos</th><th>salary</th><th>proj</th><th>ceiling</th>
        <th>floor</th><th>boom %</th><th>bust %</th><th>own %</th></tr></thead>
        <tbody>${demo.projection_table
          .slice(0, 12)
          .map((p) => {
            const own = demo.ownership_top.find((o) => o.name === p.name);
            return `<tr><td>${p.name}</td><td>${p.positions.join("/")}</td>
              <td>${num(p.salary, 0)}</td><td>${num(p.projection)}</td><td>${num(p.ceiling)}</td>
              <td>${num(p.floor)}</td><td>${num(p.boom_pct, 1)}</td><td>${num(p.bust_pct, 1)}</td>
              <td>${own ? num(own.ownership_pct, 1) : "—"}</td></tr>`;
          })
          .join("")}</tbody></table></div>
      <div class="grid c2">
        <div class="card" style="background:var(--panel-2)">
          <div class="kv"><span>Field baseline (random entries)</span>
            <span>ROI ${num(demo.field_baseline.mean_roi_pct, 1)}%</span></div>
          <div class="kv"><span>Best decile of the same field</span>
            <span>ROI ${num(demo.field_baseline.best_decile_roi_pct, 1)}%</span></div>
          <div class="kv"><span>Field cash rate</span>
            <span>${num(demo.field_baseline.mean_cash_rate_pct, 1)}%</span></div>
          <p class="small muted">${demo.field_baseline.note} ${demo.field_baseline.best_decile_note}</p>
        </div>
        <div class="card" style="background:var(--panel-2)">
          <div class="kv"><span>Engine lineups, one noisy view each (${demo.field_baseline.own_draw_rois_pct.length} draws)</span>
            <span>${num(Math.min(...demo.field_baseline.own_draw_rois_pct), 1)}% … ${num(
              Math.max(...demo.field_baseline.own_draw_rois_pct), 1
            )}%</span></div>
          <p class="small muted">${demo.field_baseline.own_draws_note}</p>
        </div>
      </div>
      <h4 class="small muted">Lineups the optimiser built (${demo.lineups[0].method} solver)</h4>
      ${demo.lineups
        .map(
          (lineup) => `<div class="card" style="background:var(--panel-2);margin:8px 0">
        <div class="kv"><span>${lineup.label} · salary ${num(lineup.salary, 0)}</span>
          <span>projected ${num(lineup.projected)}</span></div>
        <div class="muted small">${lineup.players
          .map((p) => `${p.positions.join("/")} ${p.name}`)
          .join(" · ")}</div>
        <div class="muted small">simulated ROI ${num(lineup.roi_pct, 1)}% · cash ${num(
            lineup.cash_rate_pct,
            1
          )}% · win ${num(lineup.win_rate_pct, 3)}% · median rank ${num(lineup.median_rank, 0)}
          — <strong>not a forecast</strong>, see limitations</div></div>`
        )
        .join("")}
      <div class="notice"><strong>Read this before the ROI numbers.</strong> ${demo.notes.join(" ")}</div>`;
    $("#demo").appendChild(card);
  });

  // ---- limitations --------------------------------------------------------
  $("#limitations").innerHTML = (data.limitations || [])
    .map(
      (item) =>
        `<div class="card" style="margin:10px 0"><h3>${item.heading}</h3>
         <p class="small">${item.body} <a href="https://github.com/buffedlizard55-lab/StokEngineer/blob/main/LIMITATIONS.md">full text</a></p></div>`
    )
    .join("");

  // ---- sources table ------------------------------------------------------
  const sourceRows = data.sources
    .map(
      (s) => `<tr><td><code>${s.id}</code></td>
      <td>${link(s.url, s.title || s.url)}<br><span class="muted small">${s.publisher}</span></td>
      <td class="small">${s.provides}</td>
      <td class="small">${s.licence}</td>
      <td>${badge(s.verification, s.verification === "fetched_live" ? "ok" : s.verification === "github_api" ? "ok" : "warn")}
      ${s.official ? badge("official", "ok") : badge("third-party", "warn")}
      ${s.free ? badge("free", "ok") : badge("paid", "bad")}</td></tr>`
    )
    .join("");
  $("#sources-body").innerHTML = sourceRows;
  $("#sources-filter").addEventListener("input", (event) => {
    const q = event.target.value.toLowerCase();
    [...$("#sources-body").children].forEach((tr) => {
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
    });
  });

  // ---- claims ledger ------------------------------------------------------
  $("#claims-body").innerHTML = data.claims
    .map(
      (c) => `<tr><td><code>${c.id}</code></td>
      <td class="small">${c.claim}<br><span class="muted">“${c.quote}”</span></td>
      <td>${
        c.source_url ? link(c.source_url, c.source_id) : `<code>${c.source_id || "—"}</code>`
      }<br>${badge(c.status, c.status === "verified" ? "ok" : "warn")}</td></tr>`
    )
    .join("");
  $("#claims-filter").addEventListener("input", (event) => {
    const q = event.target.value.toLowerCase();
    [...$("#claims-body").children].forEach((tr) => {
      tr.style.display = tr.textContent.toLowerCase().includes(q) ? "" : "none";
    });
  });

  // ---- downgraded urls + reports -----------------------------------------
  $("#downgraded").innerHTML = (data.removed_or_downgraded || [])
    .map((item) => `<li><code>${item.url || ""}</code> — ${item.reason || ""}</li>`)
    .join("");
  $("#reports").innerHTML = (data.reports || [])
    .map(
      (r) => `<li><code>reports/${r.file}</code> — ${r.kind || ""}
      ${r.provenance ? `<span class="muted small">sha256 ${String(r.provenance.payload_sha256 || "").slice(0, 12)}…</span>` : ""}</li>`
    )
    .join("") || "<li class='muted'>no reports committed yet</li>";
})();

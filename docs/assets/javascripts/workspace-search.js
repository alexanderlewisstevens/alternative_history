(function () {
  const app = document.querySelector(".ah-search-app");
  if (!app) return;

  const queryInput = app.querySelector("#ah-workspace-query");
  const kindFilter = app.querySelector("#ah-kind-filter");
  const tagFilter = app.querySelector("#ah-tag-filter");
  const constellationFilter = app.querySelector("#ah-constellation-filter");
  const summary = app.querySelector(".ah-search-summary");
  const results = app.querySelector(".ah-search-results");
  const indexUrl = app.getAttribute("data-index");

  function option(label, value, count) {
    const item = document.createElement("option");
    item.value = value;
    item.textContent = count == null ? label : `${label} (${count})`;
    return item;
  }

  function fillSelect(select, values, allLabel) {
    select.replaceChildren(option(allLabel, "", null));
    Object.entries(values || {}).forEach(([value, count]) => {
      select.appendChild(option(value, value, count));
    });
  }

  function card(item) {
    const node = document.createElement("article");
    node.className = "ah-search-result";

    const kicker = document.createElement("div");
    kicker.className = "ah-search-result-kicker";
    kicker.textContent = item.kind;

    const title = document.createElement("h3");
    const anchor = document.createElement("a");
    anchor.href = item.url;
    anchor.textContent = item.title;
    title.appendChild(anchor);

    const summaryText = document.createElement("p");
    summaryText.textContent = item.summary || "";

    const meta = document.createElement("div");
    meta.className = "ah-search-result-meta";
    const chips = [
      item.thinker,
      item.status,
      ...(item.constellations || []),
      ...(item.tags || []).slice(0, 5),
    ].filter(Boolean);
    chips.forEach((value) => {
      const chip = document.createElement("span");
      chip.textContent = value;
      meta.appendChild(chip);
    });

    node.append(kicker, title, summaryText, meta);
    return node;
  }

  function matches(item) {
    const query = queryInput.value.trim().toLowerCase();
    const kind = kindFilter.value;
    const tag = tagFilter.value;
    const constellation = constellationFilter.value;
    if (query && !item.search_text.includes(query)) return false;
    if (kind && item.kind !== kind) return false;
    if (tag && !(item.tags || []).includes(tag)) return false;
    if (constellation && !(item.constellations || []).includes(constellation)) return false;
    return true;
  }

  function render(entries) {
    const filtered = entries.filter(matches);
    summary.textContent = `${filtered.length} of ${entries.length} workspace entries`;
    results.replaceChildren(...filtered.map(card));
  }

  fetch(indexUrl)
    .then((response) => {
      if (!response.ok) throw new Error(`index request failed: ${response.status}`);
      return response.json();
    })
    .then((payload) => {
      fillSelect(kindFilter, payload.filters.kinds, "All types");
      fillSelect(tagFilter, payload.filters.tags, "All tags");
      fillSelect(constellationFilter, payload.filters.constellations, "All constellations");
      const entries = payload.entries || [];
      [queryInput, kindFilter, tagFilter, constellationFilter].forEach((control) => {
        control.addEventListener("input", () => render(entries));
        control.addEventListener("change", () => render(entries));
      });
      render(entries);
    })
    .catch((error) => {
      summary.textContent = "Workspace search index could not be loaded.";
      const detail = document.createElement("p");
      detail.textContent = error.message;
      results.replaceChildren(detail);
    });
})();

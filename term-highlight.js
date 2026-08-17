/* Special-term highlighting.
 *
 * CCL candidates lose marks on named entities far more than on grammar --
 * Centrelink, bulk billing, ABN, Medicare. The spoken script keeps whichever
 * form a real speaker would use, so the learner needs a second channel telling
 * them "this one is a trap, and here is the other side of it".
 *
 * Two deliberate constraints:
 *
 * 1. It walks TEXT NODES and uses createElement/textContent. It never builds
 *    HTML from dialogue content, so no amount of odd punctuation in a segment
 *    can produce markup.
 * 2. It never touches the meeting/exam view. There the source script is hidden
 *    on purpose; highlighting terms there would leak the answer.
 */
(function () {
  const STATE = { terms: null, loading: null };

  const CRITICAL_ONLY = false;      // set true to mark only Australian entities
  const CONTAINERS = ".question-source, .question-answer, .study-content, .vocab-card";

  function loadTerms() {
    if (STATE.terms) return Promise.resolve(STATE.terms);
    if (STATE.loading) return STATE.loading;
    STATE.loading = fetch("/data/terms.json", { cache: "force-cache" })
      .then((r) => (r.ok ? r.json() : []))
      .then((list) => {
        // Build one matcher per script. Longest alias first so a long name is
        // never chopped up by one of its own abbreviations.
        const entries = [];
        (list || []).forEach((t) => {
          if (CRITICAL_ONLY && !t.critical) return;
          (t.enAliases || []).forEach((a) => entries.push({ alias: a, term: t, latin: true }));
          (t.yueAliases || []).forEach((a) => entries.push({ alias: a, term: t, latin: false }));
        });
        entries.sort((a, b) => b.alias.length - a.alias.length);
        STATE.terms = entries.filter((e) => e.alias && e.alias.length >= 2);
        return STATE.terms;
      })
      .catch(() => (STATE.terms = []));
    return STATE.loading;
  }

  const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

  function buildPattern(entries) {
    if (!entries.length) return null;
    // Latin aliases get word boundaries so "GP" does not match inside "GPS".
    // Han aliases get none -- Chinese has no word delimiters.
    const parts = entries.map((e) =>
      e.latin ? `\\b${escapeRe(e.alias)}\\b` : escapeRe(e.alias)
    );
    return new RegExp(`(${parts.join("|")})`, "gi");
  }

  function findTerm(entries, matched) {
    const low = matched.toLowerCase();
    return (entries.find((e) => e.alias.toLowerCase() === low) || {}).term || null;
  }

  function decorate(root, entries, pattern) {
    if (!pattern) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        if (!node.nodeValue || node.nodeValue.trim().length < 2) return NodeFilter.FILTER_REJECT;
        // Never nest a highlight inside another, and never touch controls.
        if (node.parentElement.closest(".ccl-term, button, select, textarea, input"))
          return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      },
    });
    const targets = [];
    let n;
    while ((n = walker.nextNode())) targets.push(n);

    targets.forEach((node) => {
      const text = node.nodeValue;
      pattern.lastIndex = 0;
      if (!pattern.test(text)) return;
      pattern.lastIndex = 0;

      const frag = document.createDocumentFragment();
      let last = 0, m;
      while ((m = pattern.exec(text)) !== null) {
        const term = findTerm(entries, m[0]);
        if (!term) continue;
        if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
        const mark = document.createElement("mark");
        mark.className = "ccl-term" + (term.critical ? " ccl-term-critical" : "");
        mark.textContent = m[0];               // never innerHTML
        mark.setAttribute("tabindex", "0");
        mark.setAttribute("role", "button");
        mark.dataset.en = term.en;
        mark.dataset.yue = term.yue;
        mark.setAttribute("aria-label", `Special term: ${term.en} — ${term.yue}`);
        mark.title = `${term.en}  ⇄  ${term.yue}`;
        frag.appendChild(mark);
        last = m.index + m[0].length;
      }
      if (!frag.childNodes.length) return;
      if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
  }

  function inExamView() {
    return !!document.querySelector(".meeting-exam");
  }

  function run() {
    if (inExamView()) return;                  // never leak the hidden script
    const blocks = document.querySelectorAll(CONTAINERS);
    if (!blocks.length) return;
    loadTerms().then((entries) => {
      const pattern = buildPattern(entries);
      blocks.forEach((b) => {
        if (b.dataset.termsDone === "1") return;
        b.dataset.termsDone = "1";
        decorate(b, entries, pattern);
      });
      mountLegend();
    });
  }

  function mountLegend() {
    const page = document.querySelector(".questions-page");
    if (!page || page.querySelector(".ccl-term-legend")) return;
    const note = document.createElement("p");
    note.className = "ccl-term-legend";
    const strong = document.createElement("strong");
    strong.textContent = "special terms";
    note.append(
      document.createTextNode("Highlighted words are "),
      strong,
      document.createTextNode(
        " — named services, schemes and official titles that are scored " +
        "strictly. Hover or tap one to see the other language."
      )
    );
    const head = page.querySelector(".question-summary") || page.firstElementChild;
    if (head) head.insertAdjacentElement("afterend", note);
  }

  // Tap-to-reveal on touch devices, where :hover never fires.
  document.addEventListener("click", (e) => {
    const mark = e.target.closest(".ccl-term");
    document.querySelectorAll(".ccl-term.open").forEach((m) => {
      if (m !== mark) m.classList.remove("open");
    });
    if (mark) mark.classList.toggle("open");
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" && e.key !== " ") return;
    const mark = document.activeElement;
    if (mark && mark.classList && mark.classList.contains("ccl-term")) {
      e.preventDefault();
      mark.classList.toggle("open");
    }
    if (e.key === "Escape")
      document.querySelectorAll(".ccl-term.open").forEach((m) => m.classList.remove("open"));
  });

  // The app re-renders by replacing #app.innerHTML, so there is no render hook
  // to subscribe to. Observing the subtree catches every view change, including
  // dialogues expanded later.
  const app = document.getElementById("app");
  if (app) {
    let queued = false;
    new MutationObserver(() => {
      if (queued) return;
      queued = true;
      requestAnimationFrame(() => { queued = false; run(); });
    }).observe(app, { childList: true, subtree: true });
  }
  document.addEventListener("DOMContentLoaded", run);
  run();
})();

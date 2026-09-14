/* Progressive enhancement only: semantic HTML remains useful without JavaScript. */
(() => {
  'use strict';
  const all = (selector) => [...document.querySelectorAll(selector)];
  const theme = document.querySelector('[data-theme-toggle]');
  if (theme) {
    theme.hidden = false;
    const systemTheme = matchMedia('(prefers-color-scheme: dark)');
    const refreshTheme = () => {
      const dark = document.documentElement.dataset.theme
        ? document.documentElement.dataset.theme === 'dark' : systemTheme.matches;
      theme.setAttribute('aria-pressed', String(dark));
      theme.querySelectorAll('[data-theme-icon]').forEach(icon => {
        icon.hidden = icon.dataset.themeIcon !== (dark ? 'dark' : 'light');
        icon.toggleAttribute('hidden', icon.hidden);
      });
      theme.title = dark ? 'Dark theme · switch to light' : 'Light theme · switch to dark';
    };
    theme.addEventListener('click', () => {
      const dark = document.documentElement.dataset.theme
        ? document.documentElement.dataset.theme === 'dark'
        : matchMedia('(prefers-color-scheme: dark)').matches;
      document.documentElement.dataset.theme = dark ? 'light' : 'dark';
      theme.setAttribute('aria-pressed', String(!dark));
      refreshTheme();
    });
    refreshTheme();
    systemTheme.addEventListener('change', refreshTheme);
  }
  all('[data-print]').forEach(button => {button.hidden = false; button.onclick = () => window.print();});
  const disclosures = all('details.disclosure');
  all('[data-expand]').forEach(button => {
    button.hidden = false;
    button.onclick = () => {disclosures.forEach(item => {item.open = button.dataset.expand === 'all';});};
  });
  const revealHash = () => {
    const id = decodeURIComponent(location.hash.slice(1));
    const target = document.getElementById(id);
    if (!target) return;
    let node = target;
    while (node) {if (node.tagName === 'DETAILS') node.open = true; node = node.parentElement;}
  };
  try {revealHash();} catch {}
  window.addEventListener('hashchange', () => {try {revealHash();} catch {}});
  let printState;
  window.addEventListener('beforeprint', () => {
    if (!printState) printState = disclosures.map(item => item.open);
    disclosures.forEach(item => {item.open = true;});
  });
  window.addEventListener('afterprint', () => {
    if (printState) disclosures.forEach((item, index) => {item.open = printState[index];});
    printState = undefined;
  });
  const filter = document.querySelector('[data-filter]');
  if (filter) {
    filter.closest('.filter-bar').hidden = false;
    const items = all('[data-finding]');
    const status = document.querySelector('[data-filter-status]');
    filter.addEventListener('input', () => {
      const query = filter.value.trim().toLocaleLowerCase();
      let count = 0;
      items.forEach(item => {
        item.hidden = !item.textContent.toLocaleLowerCase().includes(query);
        if (!item.hidden) count++;
      });
      status.textContent = count + ' of ' + items.length + ' findings shown';
      const empty = document.querySelector('[data-empty]');
      if (empty) empty.hidden = count !== 0;
    });
    // Printing must not silently omit filtered-out findings.
    let hiddenState;
    window.addEventListener('beforeprint', () => {
      if (!hiddenState) hiddenState = items.map(item => item.hidden);
      items.forEach(item => {item.hidden = false;});
    });
    window.addEventListener('afterprint', () => {
      if (hiddenState) items.forEach((item, index) => {item.hidden = hiddenState[index];});
      hiddenState = undefined;
    });
  }
})();

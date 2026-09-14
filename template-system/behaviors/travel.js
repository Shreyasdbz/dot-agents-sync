  const tripBar = document.querySelector('.trip-topbar');
  if (tripBar) {
    const resizeBar = () => document.documentElement.style.setProperty('--trip-bar-height', tripBar.offsetHeight + 'px');
    const scrollBar = () => tripBar.classList.toggle('is-scrolled', window.scrollY > 4);
    new ResizeObserver(resizeBar).observe(tripBar);
    window.addEventListener('scroll', scrollBar, {passive:true});
    resizeBar(); scrollBar();
  }
  // Copy only on an explicit click; failure never announces success.
  all('[data-copy-target]').forEach(button => {
    const target = document.getElementById(button.dataset.copyTarget);
    if (!target || !target.textContent.trim()) return;
    button.hidden = false;
    button.addEventListener('click', async () => {
      const feedback = button.closest('.booking-copy').querySelector('.copy-feedback');
      button.disabled = true;
      try {
        if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
        await navigator.clipboard.writeText(target.textContent.trim());
        feedback.textContent = 'Copied to clipboard.';
      } catch {
        const selection = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(target);
        selection.removeAllRanges();
        selection.addRange(range);
        feedback.textContent = 'Copy unavailable. Text selected; use your device’s Copy command.';
      } finally {button.disabled = false;}
    });
  });
  // Immutable USD estimates; changing currency never compounds rounding.
  const currencyControl = document.querySelector('[data-currency-control]');
  if (currencyControl) {
    const select = currencyControl.querySelector('[data-currency]');
    const amounts = all('[data-money-usd]');
    const note = document.querySelector('[data-currency-note]');
    const initialNote = note ? note.textContent : '';
    const valid = option => /^[A-Z]{3}$/.test(option.value) && Number.isFinite(Number(option.dataset.rate)) && Number(option.dataset.rate) > 0;
    [...select.options].forEach(option => {option.disabled = !valid(option);});
    const updateCurrency = () => {
      const option = select.selectedOptions[0];
      if (!option || !valid(option)) return;
      currencyControl.title = 'Currency: ' + option.value;
      const formatter = new Intl.NumberFormat('en-US', {style:'currency',currency:option.value,currencyDisplay:'code',maximumFractionDigits:0});
      amounts.forEach(node => {
        const value = Number(node.dataset.moneyUsd);
        node.textContent = node.dataset.moneyUsd.trim() && Number.isFinite(value) && value >= 0 ? formatter.format(value * Number(option.dataset.rate)) : 'Not yet priced';
      });
      if (note) note.textContent = option.value === 'USD' ? initialNote : 'Estimated conversion · 1 USD = ' + option.dataset.rate + ' ' + option.value + '. See exchange-rate details below.';
    };
    if ([...select.options].filter(valid).length > 1) currencyControl.hidden = false;
    select.addEventListener('change', updateCurrency);
  }

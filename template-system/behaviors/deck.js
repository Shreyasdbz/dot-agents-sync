  const slides = all('.slide');
  const controls = document.querySelector('.deck-controls');
  if (controls && slides.length) {
    controls.hidden = false;
    const previous = controls.querySelector('[data-prev]'), next = controls.querySelector('[data-next]');
    const select = controls.querySelector('select'), status = controls.querySelector('[role=status]');
    const progress = controls.querySelector('progress'), view = document.querySelector('[data-deck-view]');
    let index = 0, readAll = false, printing = false;
    slides.forEach((slide, i) => {
      slide.tabIndex = -1;
      const option = document.createElement('option'); option.value = String(i);
      option.textContent = slide.querySelector('h1,h2').textContent; select.append(option);
    });
    const state = () => {
      slides.forEach((slide,i) => {slide.hidden = !readAll && !printing && i !== index;});
      document.body.dataset.deckMode = readAll ? 'document' : 'slides';
      previous.disabled = index === 0; next.disabled = index === slides.length - 1;
      select.value = String(index); status.textContent = (index + 1) + ' / ' + slides.length;
      progress.max = slides.length; progress.value = index + 1;
    };
    const go = (i) => {
      index = Math.max(0, Math.min(slides.length - 1, i));
      const focused = slides.some(slide => slide.contains(document.activeElement));
      state();
      if (focused) slides[index].focus({preventScroll:true});
      slides[index].scrollIntoView({block:'start',behavior:'instant'});
    };
    previous.onclick = () => go(index - 1); next.onclick = () => go(index + 1);
    select.onchange = () => go(Number(select.value));
    if (view) {
      view.hidden = false; view.setAttribute('aria-pressed','false');
      view.onclick = () => {
        readAll = !readAll;
        view.setAttribute('aria-pressed',String(readAll));
        view.title = readAll ? 'All slides shown · switch to presentation' : 'Read all slides';
        state();
      };
    }
    document.addEventListener('keydown', event => {
      // Native value-editing controls and nested sequence players own their arrow keys.
      if (event.altKey || event.ctrlKey || event.metaKey || event.target.closest('input,textarea,select,[contenteditable],[data-sequence]')) return;
      const destinations = {ArrowRight:index + 1,PageDown:index + 1,ArrowLeft:index - 1,PageUp:index - 1,Home:0,End:slides.length - 1};
      if (event.key in destinations) {event.preventDefault(); go(destinations[event.key]);}
    });
    window.addEventListener('beforeprint', () => {printing = true; state();});
    window.addEventListener('afterprint', () => {printing = false; state();});
    state();
  }

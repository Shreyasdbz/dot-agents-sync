  const slides = all('.slide');
  const controls = document.querySelector('.deck-controls');
  if (controls && slides.length) {
    controls.hidden = false;
    const previous = controls.querySelector('[data-prev]'), next = controls.querySelector('[data-next]');
    const select = controls.querySelector('select'), status = controls.querySelector('[role=status]');
    const progress = controls.querySelector('progress'), view = document.querySelector('[data-deck-view]');
    let index = 0, readAll = false, printing = false;
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    let entrance;
    const cancelEntrance = () => {if (entrance) entrance.cancel(); entrance = undefined;};
    motion.addEventListener('change', cancelEntrance);
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
      const before = index;
      index = Math.max(0, Math.min(slides.length - 1, i));
      cancelEntrance();
      const focused = slides.some(slide => slide.contains(document.activeElement));
      state();
      if (focused) slides[index].focus({preventScroll:true});
      slides[index].scrollIntoView({block:'start',behavior:'instant'});
      // State is already selected: animation must never own navigation or visibility.
      if (index !== before && !readAll && !printing && !motion.matches && slides[index].animate) {
        const style = getComputedStyle(slides[index]);
        const duration = parseFloat(style.getPropertyValue('--motion-scene')) || 240;
        entrance = slides[index].animate([
          {opacity:.35,transform:'translateX(' + (index > before ? 12 : -12) + 'px)'},
          {opacity:1,transform:'translateX(0)'}
        ],{duration,easing:style.getPropertyValue('--ease-scene').trim() || 'ease-out'});
      }
    };
    previous.onclick = () => go(index - 1); next.onclick = () => go(index + 1);
    select.onchange = () => go(Number(select.value));
    if (view) {
      view.hidden = false; view.setAttribute('aria-pressed','false');
      view.onclick = () => {
        cancelEntrance();
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
    window.addEventListener('beforeprint', () => {cancelEntrance(); printing = true; state();});
    window.addEventListener('afterprint', () => {printing = false; state();});
    state();
  }

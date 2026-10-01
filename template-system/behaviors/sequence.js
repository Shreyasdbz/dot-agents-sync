  all('[data-sequence]').forEach(sequence => {
    const steps = [...sequence.querySelectorAll('[data-step]')];
    const controls = sequence.querySelector('[data-sequence-controls]');
    if (!steps.length || !controls) return;
    controls.hidden = false;
    const play = controls.querySelector('[data-play]'), next = controls.querySelector('[data-step-next]');
    const back = controls.querySelector('[data-step-back]'), status = controls.querySelector('[role=status]');
    let index = 0, timer, movement;
    const motion = matchMedia('(prefers-reduced-motion: reduce)');
    const token = sequence.querySelector('[data-identity-token]');
    const readout = sequence.querySelector('[data-scene-readout]');
    const positions = [[150,70],[450,70],[750,70],[150,70]];
    const cancelMovement = () => {if (movement) movement.cancel(); movement = undefined;};
    motion.addEventListener('change', cancelMovement);
    const actors = [...sequence.querySelectorAll('[data-phases]')];
    const state = () => {
      const previous = Number(sequence.dataset.sceneIndex || 0);
      sequence.dataset.sceneIndex = String(index);
      cancelMovement();
      if (readout) readout.textContent = steps[index].dataset.scene || steps[index].textContent;
      if (token) {
        const destination = positions[index];
        const transform = point => 'translate(' + point[0] + 'px,' + point[1] + 'px)';
        token.style.transform = transform(destination);
        // Keep the committed endpoint in style; cancellation never restores a stale position.
        if (previous !== index && !motion.matches) {
          let route = [positions[previous],destination];
          if (previous === 2 && index === 3) route = [[750,70],[750,135],[150,135],[150,70]];
          if (previous === 3 && index === 2) route = [[150,70],[150,135],[750,135],[750,70]];
          movement = token.animate(route.map(point => ({transform:transform(point)})),
            {duration:720,easing:'cubic-bezier(.4,0,.2,1)'});
        }
      }
      steps.forEach((step,i) => {
        step.dataset.active = String(i === index);
        if (i === index) step.setAttribute('aria-current','step'); else step.removeAttribute('aria-current');
      });
      actors.forEach(actor => {actor.dataset.sceneActive = String(actor.dataset.phases.split(' ').includes(String(index)));});
      status.textContent = 'Step ' + (index+1) + ' of ' + steps.length;
      back.disabled = index === 0; next.disabled = index === steps.length-1;
    };
    const stop = () => {cancelMovement(); clearInterval(timer); timer = undefined; play.textContent = 'Play'; play.setAttribute('aria-pressed','false');};
    play.onclick = () => {
      if (timer) return stop();
      if (index === steps.length-1) index = 0;
      play.textContent = 'Pause'; play.setAttribute('aria-pressed','true'); state();
      timer = setInterval(() => {index++; state(); if(index === steps.length-1) stop();},1800);
    };
    next.onclick = () => {stop(); index = Math.min(steps.length-1,index+1); state();};
    back.onclick = () => {stop(); index = Math.max(0,index-1); state();};
    document.addEventListener('visibilitychange', () => {if(document.hidden) stop();});
    window.addEventListener('beforeprint',stop);
    // Disclosure hiding does not set owner.hidden; stop rather than announcing invisible steps.
    for (let parent = sequence.parentElement; parent; parent = parent.parentElement) {
      if (parent.tagName === 'DETAILS') {
        const disclosure = parent;
        disclosure.addEventListener('toggle', () => {if (!disclosure.open) stop();});
      }
    }
    const owner = sequence.closest('.slide');
    if (owner) new MutationObserver(() => {if(owner.hidden) stop();}).observe(owner,{attributes:true,attributeFilter:['hidden']});
    state();
  });

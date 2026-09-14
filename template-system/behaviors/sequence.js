  all('[data-sequence]').forEach(sequence => {
    const steps = [...sequence.querySelectorAll('[data-step]')];
    const controls = sequence.querySelector('[data-sequence-controls]');
    if (!steps.length || !controls) return;
    controls.hidden = false;
    const play = controls.querySelector('[data-play]'), next = controls.querySelector('[data-step-next]');
    const back = controls.querySelector('[data-step-back]'), status = controls.querySelector('[role=status]');
    let index = 0, timer;
    const state = () => {
      steps.forEach((step,i) => {step.dataset.active = String(i === index);});
      status.textContent = 'Step ' + (index+1) + ' of ' + steps.length;
      back.disabled = index === 0; next.disabled = index === steps.length-1;
    };
    const stop = () => {clearInterval(timer); timer = undefined; play.textContent = 'Play'; play.setAttribute('aria-pressed','false');};
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
    const owner = sequence.closest('.slide');
    if (owner) new MutationObserver(() => {if(owner.hidden) stop();}).observe(owner,{attributes:true,attributeFilter:['hidden']});
    state();
  });

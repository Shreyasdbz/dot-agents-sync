/* Learning state is local to each question and lasts only for this page session. */
all('[data-quiz-snapshot]').forEach(snapshot => {
  const questions = [...snapshot.querySelectorAll('[data-quiz-question]')];
  const valid = [];
  const progress = snapshot.querySelector('[data-quiz-progress]');
  const refreshProgress = () => {
    const answered = valid.filter(q => q.querySelector('input:checked')).length;
    if (progress) {
      progress.textContent = answered + ' of ' + valid.length + ' questions answered';
      progress.style.setProperty('--quiz-progress', valid.length ? answered / valid.length : 0);
    }
  };
  questions.forEach(question => {
    const inputs = [...question.querySelectorAll('input[type="radio"]')];
    const feedback = question.querySelector('[data-quiz-feedback]');
    const result = question.querySelector('[data-quiz-result]');
    const retry = question.querySelector('[data-quiz-retry]');
    const explanations = [...question.querySelectorAll('[data-explanation]')];
    const values = inputs.map(input => input.value);
    const names = inputs.map(input => input.name);
    const correct = inputs.filter(input => input.dataset.correct === 'true');
    const shapeValid = inputs.length === 4 && new Set(values).size === 4
      && new Set(names).size === 1 && names[0]
      && [...document.querySelectorAll('input[type="radio"]')].filter(input => input.name === names[0]).length === 4
      && inputs.every(input => ['true', 'false'].includes(input.dataset.correct))
      && correct.length === 1 && explanations.length === 4
      && values.every(value => explanations.filter(item => item.dataset.explanation === value).length === 1)
      && feedback && result && retry
      && explanations.every(item => feedback.contains(item) && item.textContent.trim());
    if (!shapeValid) {
      inputs.forEach(input => { input.disabled = true; });
      const error = document.createElement('p');
      error.dataset.quizError = '';
      error.textContent = 'Question unavailable: repair its four unique choices, single answer, explanations and controls.';
      question.append(error);
      return;
    }
    valid.push(question);
    inputs.forEach(input => { input.checked = false; });
    feedback.hidden = true;
    retry.hidden = false;
    const choose = () => {
      const selected = inputs.find(input => input.checked);
      if (!selected) return;
      feedback.hidden = false;
      const letter = String.fromCharCode(65 + inputs.indexOf(selected));
      const answer = String.fromCharCode(65 + inputs.indexOf(correct[0]));
      result.dataset.outcome = selected === correct[0] ? 'correct' : 'incorrect';
      inputs.forEach(input => {
        const label = input.closest('label');
        if (!label) return;
        if (input === selected) label.dataset.answerState = result.dataset.outcome;
        else delete label.dataset.answerState;
      });
      result.textContent = selected === correct[0]
        ? 'Correct — you selected ' + letter + '. All four explanations follow.'
        : 'You selected ' + letter + '. Correct answer: ' + answer + '. All four explanations follow.';
      explanations.forEach(item => { item.dataset.selected = String(item.dataset.explanation === selected.value); });
      refreshProgress();
    };
    inputs.forEach(input => { input.addEventListener('change', choose); });
    retry.addEventListener('click', () => {
      inputs.forEach(input => {
        input.checked = false;
        const label = input.closest('label');
        if (label) delete label.dataset.answerState;
      });
      explanations.forEach(item => { delete item.dataset.selected; });
      feedback.hidden = true;
      result.textContent = '';
      delete result.dataset.outcome;
      refreshProgress();
      inputs[0].focus();
    });
  });
  refreshProgress();
});
// Print every explanation, then restore the learner's precise screen state.
let quizPrintState;
window.addEventListener('beforeprint', () => {
  if (!quizPrintState) quizPrintState = all('[data-quiz-feedback]').map(node => [node, node.hidden]);
  all('[data-quiz-feedback]').forEach(node => { node.hidden = false; });
});
window.addEventListener('afterprint', () => {
  if (quizPrintState) quizPrintState.forEach(([node, hidden]) => { node.hidden = hidden; });
  quizPrintState = undefined;
});

const fixture = (() => {
  function container(parent, attributes = {}) {
    const element = document.createElement('div');
    for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
    parent.append(element);
    return element;
  }

  function conversation(parent) {
    const pane = container(parent, { 'data-testid': 'conversation-view' });
    const overlay = container(pane, { 'data-autoscroll-overlay-host': '' });
    const viewport = container(overlay, { 'data-testid': 'autoscroll-viewport' });
    return container(container(viewport));
  }

  function steps(list) {
    const root = container(list, { 'data-quotable-root': '' });
    const frame = container(container(container(root)));
    const response = container(frame, { 'data-testid': 'agent-response', 'data-quotable': 'true' });
    return container(response, { 'data-step-list': '' });
  }

  function status(label, id = 'worked-for-collapsible') {
    const button = document.createElement('button');
    button.setAttribute('data-testid', id);
    button.setAttribute('aria-expanded', 'false');
    button.textContent = label;
    return button;
  }

  function mountStatus(list, button) {
    container(list, { class: 'relative' }).append(button);
  }

  function yieldAfterVisiting(element, change) {
    const closest = Element.prototype.closest;
    Element.prototype.closest = function (...args) {
      const result = closest.apply(this, args);
      if (this === element) {
        Element.prototype.closest = closest;
        const now = performance.now;
        performance.now = () => now.call(performance) + 100;
        queueMicrotask(() => {
          performance.now = now;
          change();
        });
      }
      return result;
    };
  }

  return { container, conversation, steps, status, mountStatus, yieldAfterVisiting };
})();

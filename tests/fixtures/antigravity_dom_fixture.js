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
    const getAttribute = Element.prototype.getAttribute;
    const hasAttributes = Element.prototype.hasAttributes;
    let fired = false;
    function triggerIfTarget(node) {
      if (fired || node !== element) return;
      fired = true;
      Element.prototype.closest = closest;
      Element.prototype.getAttribute = getAttribute;
      Element.prototype.hasAttributes = hasAttributes;
      const now = performance.now;
      performance.now = () => now.call(performance) + 100;
      queueMicrotask(() => {
        performance.now = now;
        change();
      });
    }
    Element.prototype.closest = function (...args) {
      const result = closest.apply(this, args);
      triggerIfTarget(this);
      return result;
    };
    Element.prototype.getAttribute = function (...args) {
      const result = getAttribute.apply(this, args);
      triggerIfTarget(this);
      return result;
    };
    Element.prototype.hasAttributes = function (...args) {
      const result = hasAttributes.apply(this, args);
      triggerIfTarget(this);
      return result;
    };
  }

  return { container, conversation, steps, status, mountStatus, yieldAfterVisiting };
})();

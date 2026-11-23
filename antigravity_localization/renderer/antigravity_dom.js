const dom = (() => {
  const testId = (node) => node?.getAttribute('data-testid');
  const view = '[data-testid="conversation-view"]';
  const viewport = '[data-testid="autoscroll-viewport"]';
  const turnRoot = '[data-quotable-root]';
  const responseBranch = '[data-testid="agent-response"][data-quotable]';
  const stepContainer = '[data-step-list], [data-step-rows]';
  const statusInteriorMarker = stepContainer + ', ' + responseBranch;
  const artifact = '[data-testid="artifact-view"], [data-artifact-content], [data-artifact-preview], .artifact-preview';
  const protectedContent = [
    'script', 'style', 'pre', 'code', 'svg', 'math', 'iframe', 'object', 'embed', 'canvas',
    'noscript', 'template', 'option', '.monaco-editor', '.xterm', '.katex',
    'article', 'blockquote', '.prose', '[data-markdown]', '[data-markdown-root]',
    '[data-message-content]', '[data-testid="user-message"]', '[data-testid="user-input-step"]',
    '[class~="group/user-input-step"]', '[data-testid="inline-permission-error"]', '[data-diagnostic]',
    '[class*="thought-content"]', '[class*="thinking-content"]', '[class*="reasoning-content"]',
    '.bleed-contain',
    '#agy-monitor-footer-host', '#agy-monitor-popover-host', '[data-agy-turn-host]',
    '[contenteditable]:not([contenteditable="false"])', '[data-lexical-editor]', '[role="textbox"]', artifact,
  ].join(', ');
  const statusIds = new Set([
    'worked-for-collapsible', 'thinking-collapsible-trigger',
    'progress-updates-collapsible', 'tool-group-collapsible',
  ]);
  const permissionButtons = new Set([
    'inline-permission-allow', 'inline-permission-deny', 'inline-permission-add-note',
  ]);
  const shell = [
    '[data-testid="settings-sidebar"]', '[data-testid="settings-app-version-card"]',
    '[data-testid="settings-button"]', '[data-testid="app-update-button"]',
    '[data-testid="overview-panel-host-header"]',
    '[data-testid="plugins-tabs"]', '[data-testid="plugins-section-header"]',
    '[data-testid="plugin-detail"]', '[data-testid="marketplace-filter-menu"]',
    '[data-testid="permissions-menu"]', '[data-testid="model-selector-panel"]',
    '[data-testid="mcp-config-modal"]', '[role="dialog"].settings-modal-container',
  ].join(', ');
  const shellToolbar = '[data-testid="sidebar-navigation-items"], [data-testid="pane-titlebar-toolbar"]';
  const sidebarActions = new Set(['new-conversation-button', 'automations-button', 'plugins-button']);
  const titlebarActions = new Set([
    'titlebar-more-actions', 'toggle-overview-panel', 'toggle-aux-sidebar',
    'toggle-vm-panel', 'toggle-maximize-pane', 'close-pane-button',
    'open-in-cider', 'toggle-bottom-terminal-panel', 'running-items-panel-toggle',
  ]);
  const input = 'textarea, input:not([type]), input[type="text"], input[type="search"], input[type="email"], input[type="url"]';
  const slot = (format, dynamic = false) => ({ format, dynamic });
  const statusSlot = slot(formats.status, true);
  const timeSlot = slot(formats.time, true);
  const summarySlot = slot(formats.fileSummary, true);
  const fileActionSlot = slot(formats.fileAction);
  const permissionTitleSlot = slot(formats.permissionTitle);
  const permissionButtonSlot = slot(formats.permissionButton, true);
  const artifactSlot = slot(formats.artifactAction);
  const composerSlot = slot(formats.composer, true);
  const shellOptions = { allowRelTime: true, allowBareRelTime: false, allowCoreWords: true, allowExtraLabels: true };
  const shellSlot = slot((text) => formats.shell(text, shellOptions));
  const shellAttrOptions = { allowRelTime: false, allowBareRelTime: false, allowCoreWords: true, allowExtraLabels: false };
  const shellAttr = (text) => formats.shell(text, shellAttrOptions);
  const placeholderSlot = slot(shellAttr, true);
  const confirmTitles = new Set(['Confirm Undo', 'Confirm Redo', '确认撤销', '确认重做']);

  const parentElement = (element) => element.parentElement;

  function up(element, levels, parentOf = parentElement) {
    for (let i = 0; element && i < levels; i++) element = parentOf(element);
    return element;
  }

  // 2.34 AutoScroll owns viewport > width wrapper > list > quotable roots.
  // Each turn owns its response and action fieldset four levels under that root.
  function ownsTurnBranch(branch, parentOf = parentElement) {
    const root = up(branch, 4, parentOf);
    const scroll = up(root, 3, parentOf);
    return root?.matches(turnRoot) &&
      scroll?.matches(viewport) &&
      parentOf(scroll)?.hasAttribute('data-autoscroll-overlay-host');
  }

  function responseFor(element) {
    const response = element.closest(responseBranch);
    return response && ownsTurnBranch(response) ? response : null;
  }

  function statusCandidate(button) {
    return button?.tagName === 'BUTTON' && statusIds.has(testId(button));
  }

  function ownsStatusHeader(button, parentOf, isFirstChild) {
    // The collapse component mounts the trigger before its optional body. With
    // trailing controls the trigger is the first child of a dedicated flex row.
    const row = parentOf(button);
    const trailing = row?.matches('div.flex.min-w-0.items-center');
    const header = trailing ? row : button;
    const collapse = parentOf(header);
    if (!collapse?.matches('div.relative') || !isFirstChild(header) ||
        (trailing && !isFirstChild(button))) return false;
    if (button.matches(stepContainer) || collapse.matches(statusInteriorMarker) ||
        (trailing && row.matches(statusInteriorMarker))) return false;
    const list = parentOf(collapse);
    if (!list?.matches(stepContainer)) return false;
    const parent = parentOf(list);
    const response = list.matches(responseBranch) ? list :
      parent?.matches(responseBranch) ? parent :
      list.hasAttribute('data-step-rows') && parent?.hasAttribute('data-step-list') ? parentOf(parent) : null;
    return response?.matches(responseBranch) && ownsTurnBranch(response, parentOf);
  }

  function statusButton(element) {
    const button = element.closest('button[data-testid][aria-expanded]');
    return statusCandidate(button) && ownsStatusHeader(button, parentElement,
      (node) => !node.previousElementSibling) ? button : null;
  }

  function fileHeader(element) {
    const header = element.closest('[data-testid="changed-files-card-header"]');
    if (!header || testId(header.parentElement) !== 'changed-files-card') return null;
    const cards = up(header, 2);
    const response = cards?.parentElement;
    return testId(cards) === 'turn-cards-container' &&
      response && testId(response) === 'agent-response' && response.hasAttribute('data-quotable') &&
      ownsTurnBranch(response) ? header : null;
  }

  function feedbackToolbar(element) {
    const bar = element.closest('[data-testid="cascade-system-message-toolbar"]');
    const fieldset = up(bar, 2);
    return fieldset?.tagName === 'FIELDSET' && ownsTurnBranch(fieldset) ? bar : null;
  }

  function feedbackButton(element) {
    if (!element.matches('button.agy-button-icon[data-tooltip-id][aria-label]')) return false;
    const bar = feedbackToolbar(element);
    return Boolean(bar && up(element, 3) === bar);
  }

  function permissionSlot(element) {
    const card = element.closest('[data-testid="inline-permission-card"][data-permission-surface="chat"]');
    const wrapper = card?.parentElement;
    const response = wrapper?.parentElement;
    if (!response || testId(wrapper) !== 'inline-permission-slot' || response !== responseFor(element)) return null;
    const button = element.closest('button[data-testid]');
    if (button && card.contains(button) && permissionButtons.has(testId(button))) return permissionButtonSlot;
    const titleGroup = card.firstElementChild?.lastElementChild?.lastElementChild;
    return element.parentElement === titleGroup && element.matches('span.text-compact.font-semibold')
      ? permissionTitleSlot : null;
  }

  function inChat(element) {
    return Boolean(element.closest(viewport + ', ' + view + ', ' + turnRoot + ', .chat-messages, .chat-scroll-pane, [role="log"]'));
  }

  function inComposer(element) {
    const surface = element.closest('.surface-composer');
    return Boolean(surface && testId(surface.parentElement) === 'agent-input-box' &&
      !surface.closest(viewport + ', ' + turnRoot));
  }

  function composerControl(element) {
    const footer = element.closest('.agy-composer-footer[data-agent-composer-root]');
    return Boolean(footer && inComposer(footer));
  }

  function composerPlaceholder(element) {
    // Lexical renders the placeholder as a sibling of the editable draft.
    return element.matches('p.pointer-events-none.select-none.text-ellipsis') &&
      element.previousElementSibling?.hasAttribute('data-lexical-editor') && inComposer(element);
  }

  function confirmSlot(element) {
    const dialog = element.closest('[role="dialog"].agy-dialog');
    const heading = dialog?.firstElementChild?.firstElementChild;
    if (!heading?.matches('h2.text-lg.font-medium') ||
        heading.firstChild?.nodeType !== 3 || !confirmTitles.has(heading.firstChild.data.trim())) return null;
    if (element === heading) return permissionTitleSlot;
    const body = dialog.children[1]?.firstElementChild;
    if (element === body?.firstElementChild && element.tagName === 'P') return permissionTitleSlot;
    const footer = body?.lastElementChild;
    const button = element.closest('button');
    if (footer?.matches('.items-center.justify-end.pt-3') && up(button, 2) === footer) return permissionButtonSlot;
    return null;
  }

  function shellOwner(element) {
    const toolbar = element.closest(shellToolbar);
    if (toolbar) {
      const action = element.closest('a, button');
      if (!action || !toolbar.contains(action)) return null;
      if (testId(toolbar) === 'pane-titlebar-toolbar') return titlebarActions.has(testId(action)) ? action : null;
      const customizationsLink = action.matches('a[data-tooltip-id]') && action.parentElement === toolbar &&
        action.pathname === '/customizations';
      return sidebarActions.has(testId(action)) || customizationsLink ? action : null;
    }
    const owner = element.closest(shell);
    if (owner) return owner;
    // The separate settings window mounts the same settings pane without a dialog.
    if (element.ownerDocument.location?.pathname === '/settings-standalone') {
      return element.closest('[data-split-root] .relative.flex-grow.min-h-0 > .overflow-auto > .grow.w-full');
    }
    return null;
  }

  function editable(element) {
    return element.isContentEditable || element.matches('textarea, input, [role="textbox"]');
  }

  function isProtected(element) {
    return Boolean(element.closest(protectedContent));
  }

  function textSlot(element) {
    if (isProtected(element) || editable(element)) return null;
    const step = statusButton(element);
    if (step) return statusSlot;
    const header = fileHeader(element);
    if (header) {
      const review = element.closest('button[data-testid="changed-files-card-review"]');
      if (review?.parentElement === header) return fileActionSlot;
      return element === header.firstElementChild?.firstElementChild ? summarySlot : null;
    }
    if (element.matches('span[data-screenshot-volatile][data-tooltip-id]')) {
      const bar = feedbackToolbar(element);
      if (bar && up(element, 2) === bar) return timeSlot;
    }
    const permission = permissionSlot(element);
    if (permission) return permission;
    if (composerPlaceholder(element)) return placeholderSlot;
    if (composerControl(element)) return composerSlot;
    if (inChat(element)) return null;
    if (element.closest('[data-testid="artifact-editor-header"]')) return element.closest('button') ? artifactSlot : null;
    if (element.closest('.artifact-sidebar')) return null;
    const confirmation = confirmSlot(element);
    if (confirmation) return confirmation;
    if (!shellOwner(element)) return null;
    return element.matches('[data-screenshot-volatile]') ? timeSlot : shellSlot;
  }

  function attrFormatter(element, name) {
    if (isProtected(element)) return null;
    if (name === 'placeholder') {
      if (!element.matches(input)) return null;
      if (inComposer(element)) return shellAttr;
      return !inChat(element) && !element.closest('.artifact-sidebar') && shellOwner(element) ? shellAttr : null;
    }
    if (editable(element)) return null;
    if (feedbackButton(element)) return formats.feedback;
    if (statusButton(element) === element) return formats.status;
    if (composerControl(element) && element.matches('button, [role="combobox"], [role="switch"]')) return formats.composer;
    if (inChat(element)) return null;
    if (element.matches('button') && element.closest('[data-testid="artifact-editor-header"]')) return formats.artifactAction;
    if (element.closest('.artifact-sidebar')) return null;
    return shellOwner(element) ? shellAttr : null;
  }

  return {
    textSlot, attrFormatter, isProtected, statusButton, statusCandidate, ownsStatusHeader,
    isProtectedRoot: (element) => element.matches(protectedContent),
  };
})();

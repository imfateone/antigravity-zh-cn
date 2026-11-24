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
    '#agy-monitor-footer-host', '#agy-monitor-popover-host', '[id^="agy-monitor-"]', '[data-agy-turn-host]',
    '[data-testid="gcp-project-combobox-list"]', '[data-testid="project-selector-item"]',
    '[data-testid="project-selector-github-repo-item"]',
    '[data-testid="overview-panel-host-header"]',
    '[data-testid^="overview-decorator-"]', '[data-testid^="overview-accumulated-section-"]',
    '[contenteditable]:not([contenteditable="false"])', '[data-lexical-editor]', '[role="textbox"]', artifact,
  ].join(', ');
  const pruneBlocked = [
    'script', 'style', 'pre', 'code', 'svg', 'math', 'iframe', 'object', 'embed', 'canvas',
    'noscript', 'template', 'option', '.monaco-editor', '.xterm', '.katex',
    'article', 'blockquote', '.prose', '[data-markdown]', '[data-markdown-root]',
    '[data-message-content]', '[data-testid="user-message"]', '[data-testid="user-input-step"]',
    '[class~="group/user-input-step"]', '[data-testid="inline-permission-error"]', '[data-diagnostic]',
    '[class*="thought-content"]', '[class*="thinking-content"]', '[class*="reasoning-content"]',
    '.bleed-contain',
    '#agy-monitor-footer-host', '#agy-monitor-popover-host', '[id^="agy-monitor-"]', '[data-agy-turn-host]',
    '[data-testid="gcp-project-combobox-list"]', '[data-testid="project-selector-item"]',
    '[data-testid="project-selector-github-repo-item"]',
    '[data-testid="overview-panel-host-header"]',
    '[data-testid^="overview-decorator-"]', '[data-testid^="overview-accumulated-section-"]',
    '[contenteditable]:not([contenteditable="false"])', '[data-lexical-editor]', '[role="textbox"]',
    '[data-artifact-content]', '[data-artifact-preview]', '.artifact-preview',
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
    '[data-testid="settings-button"]', '[data-testid="app-update-button"]', '[data-testid="manual-update-button"]',
    '[data-testid="title-menu-bar"]', '[data-testid="voice-picker"]', '[data-testid="voice-speed-panel"]',
    '[data-testid="orchestrator-picker-effort"]',
    '[data-select-popup].agy-overlay:not([data-testid="gcp-project-combobox-popup"])',
    '[data-testid="plugins-tabs"]', '[data-testid="plugins-section-header"]',
    '[data-testid="plugin-detail"]', '[data-testid="marketplace-filter-menu"]',
    '[data-testid="permissions-menu"]', '[data-testid="model-selector-panel"]',
    '[data-testid="mcp-config-modal"]', '[role="dialog"].settings-modal-container',
    '[data-testid="declared-permissions-modal"]', '[data-testid="plugin-source-caution-modal"]',
    '[data-testid="delete-mcp-modal"]', '[data-testid="delete-sidecar-modal"]', '[data-testid="add-mcp-button"]',
    '[data-testid="bottom-terminal-panel-title"]', '[data-testid="bottom-terminal-panel-new"]',
    '[data-testid="bottom-terminal-panel-empty"]', '[data-testid="bottom-terminal-panel-empty-new"]',
    '[data-testid="bottom-terminal-panel-close"]', '[data-testid="bottom-terminal-panel-menu-split"]',
    '[data-testid="bottom-terminal-panel-menu-kill"]', '[data-testid="bottom-terminal-panel-starting"]',
    '[data-testid="builtin-browser-back"]', '[data-testid="builtin-browser-forward"]',
    '[data-testid="builtin-browser-reload"]', '[data-testid="builtin-browser-placeholder"]',
    '[data-testid="builtin-browser-download-dir-change"]', '[data-testid="builtin-browser-download-dir-reset"]',
    '[data-testid="browser-error-retry-button"]', '[data-testid="browser-clear-data-button"]',
    '[data-testid="browser-clear-data-confirm"]', '[data-testid="clear-browser-history-button"]',
    '[data-testid="browser-site-data-manage-button"]', '[data-testid="webview-url-bar-open-external"]',
    '[data-testid="webview-url-bar-downloads"]', '[data-testid="preview-url-bar-open-new-tab"]',
    '[data-testid="file-explorer-refresh"]', '[data-testid="file-tree-filter-input"]',
    '[data-testid="file-tree-filter-clear"]', '[data-testid="file-tree-filter-empty"]',
    '[data-testid="file-tree-filter-error"]',
    '[data-testid="sidebar-toggle"]', '[data-testid="sidebar-search-button"]',
    '[data-testid="customize-sidebar-button"]', '[data-testid="customize-sidebar-modal"]',
    '[data-testid="filter-sort-button"]', '[data-testid="filter-submenu-trigger"]',
    '[data-testid="group-by-submenu-trigger"]', '[data-testid="display-submenu-trigger"]',
    '[data-testid="conversations-palette-filter-trigger"]', '[data-testid="palette-filter-archived"]',
    '[data-testid="palette-filter-scheduled"]', '[data-testid="palette-filter-unread"]',
    '[data-testid="palette-sort-last_updated"]', '[data-testid="palette-sort-last_user_prompt"]',
    '[data-testid="project-selector-search"]', '[data-testid="project-selector-create-project-trigger"]',
    '[data-testid="project-selector-new-workspace"]', '[data-testid="project-selector-connect-github"]',
    '[data-testid="project-selector-connect-ssh-host"]', '[data-testid="project-selector-configure-github-app"]',
    '[data-testid="toolbar-overflow-trigger"]', '[data-testid="overflow-menu"]',
    '[data-testid="automation-settings-save"]', '[data-testid="automation-settings-cancel"]',
    '[data-testid="schedule-editor-save"]', '[data-testid="running-confirm-stop"]',
    '[data-testid="running-row-stop"]', '[data-testid="running-selection-stop"]',
    '[data-testid="side-question-insert-to-main"]', '[data-testid="side-question-popout"]',
    '[data-testid="selection-quote-button"]', '[data-testid="selection-popup-quote-button"]',
    '[data-testid="selection-btw-button"]', '[data-testid="selection-comment-button"]',
  ].join(', ');
  const overviewRowSelector = [
    '[data-testid="overview-panel-row-review"]',
    '[data-testid="overview-panel-row-files"]',
    '[data-testid="overview-panel-row-terminal"]',
    '[data-testid="overview-panel-row-plugins"]',
  ].join(', ');
  const overviewExcludedSelector = [
    '[data-testid="overview-panel-host-header"]',
    '[data-testid^="overview-decorator-"]',
    '[data-testid^="overview-accumulated-section-"]',
    '[data-testid="overview-panel-row-review-detail"]',
    '[data-testid="overview-panel-row-review-diff-stats"]',
  ].join(', ');
  const overviewAuxSectionSelector = [
    '[data-testid="aux-pane-background-tasks-section"]',
    '[data-testid="aux-pane-terminals-section"]',
  ].join(', ');
  const artifactHeaderExclusion = [
    '[data-artifact-content]', '[data-artifact-preview]', '.artifact-preview',
    'pre', 'code', '.monaco-editor', '.xterm',
    '[id^="agy-monitor-"]', '[data-agy-turn-host]',
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
  const homeGreetingSlot = slot(formats.homeGreeting);
  const shellOptions = { allowRelTime: true, allowBareRelTime: false, allowCoreWords: true, allowExtraLabels: true };
  const shellSlot = slot((text) => formats.shell(text, shellOptions));
  const shellAttrOptions = { allowRelTime: false, allowBareRelTime: false, allowCoreWords: true, allowExtraLabels: false };
  const shellAttr = (text) => formats.shell(text, shellAttrOptions);
  const shellAttrSlot = slot(shellAttr, false);
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

  function homeGreeting(element) {
    const greeting = element.closest('[data-testid="home-greeting"]');
    return Boolean(
      greeting &&
      element.matches('h1.home-greeting-title') &&
      element.parentElement === greeting &&
      !greeting.closest(viewport + ', ' + turnRoot + ', .chat-messages, .chat-scroll-pane, [role="log"]')
    );
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

  function shouldPrune(element) {
    return Boolean(element.closest(pruneBlocked));
  }

  function artifactHeaderButton(element) {
    const hdr = element.closest('[data-testid="artifact-editor-header"]');
    const btn = element.closest('button');
    return Boolean(
      hdr && btn && hdr.contains(btn) &&
      !editable(element) &&
      !element.closest(artifactHeaderExclusion)
    );
  }

  function overviewSlot(element) {
    const auxSection = element.closest(overviewAuxSectionSelector);
    if (auxSection) {
      return element.closest('span.agy-hover-label') ? shellSlot : null;
    }
    const panel = element.closest('[data-testid="overview-panel"]');
    if (!panel || element.closest(overviewExcludedSelector)) return null;
    if (element.closest('[data-testid="overview-panel-customize-trigger"]')) return shellSlot;

    const row = element.closest(overviewRowSelector);
    if (row && panel.contains(row)) {
      const label = element.closest('span.agy-hover-label');
      return label && row.contains(label) ? shellSlot : null;
    }

    const hoverLabel = element.closest('span.agy-hover-label');
    if (hoverLabel && panel.contains(hoverLabel)) {
      const a6Header = hoverLabel.parentElement;
      if (a6Header?.parentElement?.parentElement === panel) return shellSlot;
      const section = a6Header?.parentElement;
      if (section && panel.contains(section) && section.matches('div.p-1') && !a6Header.previousElementSibling) {
        return shellSlot;
      }
    }

    const expandBtn = element.closest('button[type="button"][aria-expanded]');
    if (expandBtn && panel.contains(expandBtn) && expandBtn.parentElement?.matches('div.p-1') && expandBtn.previousElementSibling) {
      return shellSlot;
    }
    return null;
  }

  function escapeAttrSelector(value) {
    if (typeof CSS !== 'undefined' && typeof CSS.escape === 'function') {
      return CSS.escape(value);
    }
    return String(value).replace(/["\\\]\r\n]/g, '\\$&');
  }

  function verifiedTooltipSlot(element) {
    const tip = element.closest('[role="tooltip"][id]');
    const tipId = tip?.getAttribute('id');
    if (!tip || !tipId) return null;
    const doc = element.ownerDocument;
    if (!doc?.querySelector) return null;
    const trigger = doc.querySelector(`[data-tooltip-id="${escapeAttrSelector(tipId)}"]`);
    if (!trigger || isProtected(trigger)) return null;
    if (
      feedbackButton(trigger) ||
      statusButton(trigger) === trigger ||
      composerControl(trigger) ||
      shellOwner(trigger) ||
      overviewSlot(trigger)
    ) {
      return shellAttrSlot;
    }
    return null;
  }

  function textSlot(element) {
    if (artifactHeaderButton(element)) return artifactSlot;
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
    if (homeGreeting(element)) return homeGreetingSlot;
    if (inChat(element)) return null;
    const overview = overviewSlot(element);
    if (overview) return overview;
    const tooltip = verifiedTooltipSlot(element);
    if (tooltip) return tooltip;
    if (element.closest('[data-testid="artifact-editor-header"]') || element.closest('.artifact-sidebar')) return null;
    const confirmation = confirmSlot(element);
    if (confirmation) return confirmation;
    if (!shellOwner(element)) return null;
    return element.matches('[data-screenshot-volatile]') ? timeSlot : shellSlot;
  }

  function attrFormatter(element, name) {
    if (artifactHeaderButton(element) && name !== 'placeholder') return formats.artifactAction;
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
    if (overviewSlot(element)) return shellAttr;
    if (element.closest('.artifact-sidebar')) return null;
    return shellOwner(element) ? shellAttr : null;
  }

  return {
    textSlot, attrFormatter, isProtected, shouldPrune, shellOwner, overviewSlot,
    statusButton, statusCandidate, ownsStatusHeader,
    isProtectedRoot: (element) => element.matches(protectedContent),
  };
})();

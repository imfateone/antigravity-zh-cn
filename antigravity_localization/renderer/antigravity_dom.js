const dom = (() => {
  const testId = (node) => node?.getAttribute('data-testid');
  const view = '[data-testid="conversation-view"]';
  const viewport = '[data-testid="autoscroll-viewport"]';
  const turnRoot = '[data-quotable-root]';
  const responseBranch = '[data-testid="agent-response"][data-quotable]';
  const stepContainer = '[data-step-list], [data-step-rows]';
  const statusInteriorMarker = stepContainer + ', ' + responseBranch;

  const PROTECTED_TAGS = new Set([
    'SCRIPT', 'STYLE', 'PRE', 'CODE', 'SVG', 'MATH', 'IFRAME', 'OBJECT', 'EMBED', 'CANVAS',
    'NOSCRIPT', 'TEMPLATE', 'OPTION', 'ARTICLE', 'BLOCKQUOTE',
  ]);
  const HARD_PROTECTED_TESTIDS = new Set([
    'user-message', 'user-input-step', 'inline-permission-error',
    'gcp-project-combobox-list', 'project-selector-item', 'project-selector-github-repo-item',
    'overview-panel-host-header', 'overview-panel-row-review-detail', 'overview-panel-row-review-diff-stats',
  ]);

  const statusIds = new Set([
    'worked-for-collapsible', 'thinking-collapsible-trigger',
    'progress-updates-collapsible', 'tool-group-collapsible',
  ]);
  const permissionButtons = new Set([
    'inline-permission-allow', 'inline-permission-deny', 'inline-permission-add-note',
  ]);
  const sidebarActions = new Set(['new-conversation-button', 'automations-button', 'plugins-button']);
  const titlebarActions = new Set([
    'titlebar-more-actions', 'toggle-overview-panel', 'toggle-aux-sidebar',
    'toggle-vm-panel', 'toggle-maximize-pane', 'close-pane-button',
    'open-in-cider', 'toggle-bottom-terminal-panel', 'running-items-panel-toggle',
  ]);
  const SHELL_TESTIDS = new Set([
    // Settings, app bar, models & core UI controls
    'settings-sidebar', 'settings-app-version-card', 'settings-button',
    'app-update-button', 'manual-update-button', 'title-menu-bar',
    'voice-picker', 'voice-speed-panel', 'orchestrator-picker-effort',
    'plugins-tabs', 'plugins-section-header', 'plugin-detail',
    'marketplace-filter-menu', 'permissions-menu', 'model-selector-panel',
    'mcp-config-modal',
    // Fixed modal action buttons only (explicitly excluding business-value modal bodies)
    'declared-permissions-confirm', 'cancel-plugin-source-caution',
    'confirm-plugin-source-caution', 'review-plugin-source-caution',
    'confirm-delete-mcp', 'cancel-delete-mcp',
    'confirm-delete-skill', 'cancel-delete-skill', 'add-mcp-button',
    // Bottom terminal fixed chrome
    'bottom-terminal-panel-title', 'bottom-terminal-panel-new',
    'bottom-terminal-panel-empty', 'bottom-terminal-panel-empty-new',
    'bottom-terminal-panel-close', 'bottom-terminal-panel-menu-split',
    'bottom-terminal-panel-menu-kill', 'bottom-terminal-panel-starting',
    // Builtin browser fixed chrome
    'builtin-browser-back', 'builtin-browser-forward', 'builtin-browser-reload',
    'builtin-browser-placeholder', 'builtin-browser-download-dir-change',
    'builtin-browser-download-dir-reset', 'browser-error-retry-button',
    'browser-clear-data-button', 'browser-clear-data-confirm',
    'clear-browser-history-button', 'browser-site-data-manage-button',
    'webview-url-bar-open-external', 'webview-url-bar-downloads', 'preview-url-bar-open-new-tab',
    // File tree fixed chrome
    'file-explorer-refresh', 'file-tree-filter-input',
    'file-tree-filter-clear', 'file-tree-filter-empty', 'file-tree-filter-error',
    // Sidebar, palette & project selector fixed controls
    'sidebar-toggle', 'sidebar-search-button', 'customize-sidebar-button',
    'filter-sort-button', 'filter-submenu-trigger', 'group-by-submenu-trigger',
    'display-submenu-trigger', 'conversations-palette-filter-trigger',
    'palette-filter-archived', 'palette-filter-scheduled', 'palette-filter-unread',
    'palette-sort-last_updated', 'palette-sort-last_user_prompt',
    'project-selector-search', 'project-selector-create-project-trigger',
    'project-selector-new-workspace', 'project-selector-connect-github',
    'project-selector-connect-ssh-host', 'project-selector-configure-github-app',
    // Toolbar overflow, automation & selection fixed action buttons
    'toolbar-overflow-trigger', 'overflow-menu',
    'automation-settings-save', 'automation-settings-cancel', 'schedule-editor-save',
    'running-confirm-stop', 'running-selection-stop',
    'side-question-insert-to-main', 'side-question-popout',
    'selection-quote-button', 'selection-popup-quote-button',
    'selection-btw-button', 'selection-comment-button',
  ]);
  const OVERVIEW_ROW_TESTIDS = new Set([
    'overview-panel-row-review',
    'overview-panel-row-files',
    'overview-panel-row-terminal',
    'overview-panel-row-plugins',
  ]);
  const OVERVIEW_AUX_SECTION_TESTIDS = new Set([
    'aux-pane-background-tasks-section',
    'aux-pane-terminals-section',
  ]);

  const input = 'textarea, input:not([type]), input[type="text"], input[type="search"], input[type="email"], input[type="url"]';
  const slot = (format, dynamic = false, isTooltip = false) => ({ format, dynamic, isTooltip });
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
  const placeholderSlot = slot(shellAttr, true);
  const strictDictionaryOptions = { allowRelTime: false, allowBareRelTime: false, allowCoreWords: false, allowExtraLabels: false };
  const strictDictionarySlot = slot((text) => formats.shell(text, strictDictionaryOptions));
  const tooltipSlot = slot((text) => formats.shell(text, strictDictionaryOptions), false, true);
  const strictDictionaryFormat = (text) => formats.shell(text, strictDictionaryOptions);

  function formatOverviewExpand(text) {
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (
      trimmed === 'Show more' ||
      trimmed === 'Show less' ||
      trimmed === 'See all' ||
      trimmed === 'See less' ||
      /^Show\s+\d+\s+more$/i.test(trimmed) ||
      /^See\s+\d+\s+more$/i.test(trimmed) ||
      /^See all\s*\(.+?\)$/i.test(trimmed)
    ) {
      return formats.shell(text, strictDictionaryOptions);
    }
    return text;
  }
  const overviewExpandSlot = slot(formatOverviewExpand);
  const confirmTitles = new Set(['Confirm Undo', 'Confirm Redo', '确认撤销', '确认重做']);

  let tooltipRev = 1;
  const tooltipCache = new WeakMap();
  let portalBlocker = null;

  function bumpTooltipRev() {
    tooltipRev++;
  }

  function setPortalBlocker(fn) {
    portalBlocker = typeof fn === 'function' ? fn : null;
  }

  const parentElement = (element) => element.parentElement;

  function up(element, levels, parentOf = parentElement) {
    for (let i = 0; element && i < levels; i++) element = parentOf(element);
    return element;
  }

  function isHardProtectedNode(el, hasAttrs = el?.hasAttributes?.(), tid, role) {
    if (!el || el.nodeType !== 1) return false;
    if (PROTECTED_TAGS.has(el.tagName)) return true;
    if (!hasAttrs) return false;
    const id = el.id;
    if (id && id.startsWith('agy-monitor-')) return true;
    const resolvedTid = tid !== undefined ? tid : el.getAttribute('data-testid');
    if (
      resolvedTid &&
      (HARD_PROTECTED_TESTIDS.has(resolvedTid) ||
        resolvedTid.startsWith('overview-decorator-') ||
        resolvedTid.startsWith('overview-accumulated-section-'))
    ) {
      return true;
    }
    if (
      el.hasAttribute('data-markdown') ||
      el.hasAttribute('data-markdown-root') ||
      el.hasAttribute('data-message-content') ||
      el.hasAttribute('data-diagnostic') ||
      el.hasAttribute('data-agy-turn-host') ||
      el.hasAttribute('data-lexical-editor') ||
      el.hasAttribute('data-artifact-content') ||
      el.hasAttribute('data-artifact-preview')
    ) {
      return true;
    }
    const ce = el.getAttribute('contenteditable');
    if (ce !== null && ce !== 'false') return true;
    const resolvedRole = role !== undefined ? role : el.getAttribute('role');
    if (resolvedRole === 'textbox') return true;
    const cl = el.classList;
    if (
      cl.length &&
      (cl.contains('prose') ||
        cl.contains('monaco-editor') ||
        cl.contains('xterm') ||
        cl.contains('katex') ||
        cl.contains('bleed-contain') ||
        cl.contains('artifact-preview') ||
        cl.contains('group/user-input-step'))
    ) {
      return true;
    }
    const cls = typeof el.className === 'string' ? el.className : '';
    if (
      cls &&
      cls.includes('-content') &&
      (cls.includes('thought-content') ||
        cls.includes('thinking-content') ||
        cls.includes('reasoning-content'))
    ) {
      return true;
    }
    return false;
  }

  function isStandaloneSettingsBody(el) {
    if (el.ownerDocument.location?.pathname !== '/settings-standalone') return false;
    const p1 = el.parentElement;
    const p2 = p1?.parentElement;
    const root = p2?.parentElement;
    return Boolean(
      root &&
      el.classList.contains('grow') &&
      el.classList.contains('w-full') &&
      p1.classList.contains('overflow-auto') &&
      p2.classList.contains('relative') &&
      p2.classList.contains('flex-grow') &&
      p2.classList.contains('min-h-0') &&
      root.hasAttribute('data-split-root')
    );
  }

  function inspectAncestors(element) {
    const info = {
      hardProtected: false,
      artifactView: null,
      artifactBodyChild: false,
      artifactHeader: null,
      inArtifactSidebar: false,
      inChat: false,
      inChatBody: false,
      shellMatch: null,
      toolbarEl: null,
      toolbarAction: null,
      overviewPanel: null,
      overviewRow: null,
      overviewCustomizeTrigger: false,
      auxSection: null,
      hoverLabel: null,
      expandButton: null,
      tooltipEl: null,
      inShortcutNode: false,
      composerFooter: false,
      composerSurface: false,
      composerBox: null,
      agentResponse: null,
      changedFilesHeader: null,
      feedbackBar: null,
      permissionCard: null,
      dialogEl: null,
    };

    let prev = null;
    let nearestAction = null;
    for (let cur = element; cur && cur.nodeType === 1; prev = cur, cur = cur.parentElement) {
      const tag = cur.tagName;
      if (!info.hardProtected && PROTECTED_TAGS.has(tag)) {
        info.hardProtected = true;
      }
      if (tag === 'KBD') {
        info.inShortcutNode = true;
      }
      if (!nearestAction && (tag === 'A' || tag === 'BUTTON')) {
        nearestAction = cur;
      }
      const hasAttrs = cur.hasAttributes();
      if (!hasAttrs) continue;

      const cl = cur.classList;
      const tid = cur.getAttribute('data-testid');
      const role = cur.getAttribute('role');

      if (!info.hardProtected && isHardProtectedNode(cur, hasAttrs, tid, role)) {
        info.hardProtected = true;
      }

      if (!info.inShortcutNode && cur.hasAttribute('data-keybinding')) {
        info.inShortcutNode = true;
      }

      if (!info.hoverLabel && cl.contains('agy-hover-label')) {
        info.hoverLabel = cur;
      }

      if (
        !info.expandButton &&
        tag === 'BUTTON' &&
        cur.getAttribute('type') === 'button' &&
        cur.hasAttribute('aria-expanded')
      ) {
        info.expandButton = cur;
      }

      if (!info.inArtifactSidebar && cl.contains('artifact-sidebar')) {
        info.inArtifactSidebar = true;
      }

      const inBodyBoundary =
        tid === 'autoscroll-viewport' ||
        cur.hasAttribute('data-quotable-root') ||
        role === 'log' ||
        cl.contains('chat-messages') ||
        cl.contains('chat-scroll-pane');
      if (!info.inChatBody && inBodyBoundary) {
        info.inChatBody = true;
      }
      if (!info.inChat && (inBodyBoundary || tid === 'conversation-view')) {
        info.inChat = true;
      }

      if (!info.artifactHeader && tid === 'artifact-editor-header') {
        info.artifactHeader = cur;
      }

      if (tid === 'artifact-view') {
        if (!info.artifactView) info.artifactView = cur;
        if (prev && prev.getAttribute('data-testid') !== 'artifact-editor-header') {
          info.artifactBodyChild = true;
        }
      }

      if (!info.overviewRow && tid && OVERVIEW_ROW_TESTIDS.has(tid)) {
        info.overviewRow = cur;
      }
      if (!info.overviewCustomizeTrigger && tid === 'overview-panel-customize-trigger') {
        info.overviewCustomizeTrigger = true;
      }
      if (!info.auxSection && tid && OVERVIEW_AUX_SECTION_TESTIDS.has(tid)) {
        info.auxSection = cur;
      }
      if (!info.overviewPanel && tid === 'overview-panel') {
        info.overviewPanel = cur;
      }

      if (!info.tooltipEl && role === 'tooltip' && cur.hasAttribute('id')) {
        info.tooltipEl = cur;
      }

      if (!info.toolbarEl && (tid === 'pane-titlebar-toolbar' || tid === 'sidebar-navigation-items')) {
        info.toolbarEl = cur;
        info.toolbarAction = nearestAction;
      }

      if (
        !info.shellMatch &&
        ((tid && SHELL_TESTIDS.has(tid)) ||
          (role === 'dialog' && cl.contains('settings-modal-container')) ||
          (cur.hasAttribute('data-select-popup') && cl.contains('agy-overlay') && tid !== 'gcp-project-combobox-popup') ||
          isStandaloneSettingsBody(cur))
      ) {
        info.shellMatch = cur;
      }

      if (!info.composerFooter && cur.hasAttribute('data-agent-composer-root') && cl.contains('agy-composer-footer')) {
        info.composerFooter = true;
      }
      if (!info.composerSurface && cl.contains('surface-composer')) {
        info.composerSurface = true;
        info.composerBox = cur.parentElement;
      }
      if (!info.agentResponse && tid === 'agent-response' && cur.hasAttribute('data-quotable')) {
        info.agentResponse = cur;
      }
      if (!info.changedFilesHeader && tid === 'changed-files-card-header') {
        info.changedFilesHeader = cur;
      }
      if (!info.feedbackBar && tid === 'cascade-system-message-toolbar') {
        info.feedbackBar = cur;
      }
      if (
        !info.permissionCard &&
        tid === 'inline-permission-card' &&
        cur.getAttribute('data-permission-surface') === 'chat'
      ) {
        info.permissionCard = cur;
      }
      if (!info.dialogEl && role === 'dialog' && cl.contains('agy-dialog')) {
        info.dialogEl = cur;
      }
    }

    return info;
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

  function fileHeader(element, info) {
    const header = info.changedFilesHeader;
    if (!header || testId(header.parentElement) !== 'changed-files-card') return null;
    const cards = up(header, 2);
    const response = cards?.parentElement;
    return testId(cards) === 'turn-cards-container' &&
      response && testId(response) === 'agent-response' && response.hasAttribute('data-quotable') &&
      ownsTurnBranch(response) ? header : null;
  }

  function feedbackToolbar(info) {
    const bar = info.feedbackBar;
    if (!bar) return null;
    const fieldset = up(bar, 2);
    return fieldset?.tagName === 'FIELDSET' && ownsTurnBranch(fieldset) ? bar : null;
  }

  function feedbackButton(element, info = inspectAncestors(element)) {
    if (!element.matches('button.agy-button-icon[data-tooltip-id][aria-label]')) return false;
    const bar = feedbackToolbar(info);
    return Boolean(bar && up(element, 3) === bar);
  }

  function permissionSlot(element, info) {
    const card = info.permissionCard;
    if (!card) return null;
    const wrapper = card.parentElement;
    const response = wrapper?.parentElement;
    const validResponse = info.agentResponse && ownsTurnBranch(info.agentResponse) ? info.agentResponse : null;
    if (!response || testId(wrapper) !== 'inline-permission-slot' || response !== validResponse) return null;
    const button = element.closest('button[data-testid]');
    if (button && card.contains(button) && permissionButtons.has(testId(button))) return permissionButtonSlot;
    const titleGroup = card.firstElementChild?.lastElementChild?.lastElementChild;
    return element.parentElement === titleGroup && element.matches('span.text-compact.font-semibold')
      ? permissionTitleSlot : null;
  }

  function inComposer(info) {
    return Boolean(info.composerSurface && testId(info.composerBox) === 'agent-input-box' && !info.inChatBody);
  }

  function composerControl(element, info = inspectAncestors(element)) {
    return Boolean(info.composerFooter && inComposer(info));
  }

  function composerPlaceholder(element, info) {
    // Lexical renders the placeholder as a sibling of the editable draft.
    return element.matches('p.pointer-events-none.select-none.text-ellipsis') &&
      element.previousElementSibling?.hasAttribute('data-lexical-editor') && inComposer(info);
  }

  function homeGreeting(element, info) {
    const greeting = element.closest('[data-testid="home-greeting"]');
    return Boolean(
      greeting &&
      !info.inChatBody &&
      element.matches('h1.home-greeting-title') &&
      element.parentElement === greeting
    );
  }

  function confirmSlot(element, info) {
    const dialog = info.dialogEl;
    if (!dialog) return null;
    const heading = dialog.firstElementChild?.firstElementChild;
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

  function shellOwner(element, info = inspectAncestors(element)) {
    if (info.hardProtected) return null;
    if (info.toolbarEl) {
      const action = info.toolbarAction;
      if (!action || !info.toolbarEl.contains(action)) return null;
      if (testId(info.toolbarEl) === 'pane-titlebar-toolbar') {
        return titlebarActions.has(testId(action)) ? action : null;
      }
      const customizationsLink = action.tagName === 'A' &&
        action.hasAttribute('data-tooltip-id') &&
        action.parentElement === info.toolbarEl &&
        action.pathname === '/customizations';
      return sidebarActions.has(testId(action)) || customizationsLink ? action : null;
    }
    return info.shellMatch;
  }

  function editable(element) {
    return element.isContentEditable || element.matches('textarea, input, [role="textbox"]');
  }

  function isProtected(element) {
    const info = inspectAncestors(element);
    return info.hardProtected || Boolean(info.artifactView);
  }

  function shouldPrune(element) {
    const info = inspectAncestors(element);
    return info.hardProtected || info.artifactBodyChild;
  }

  function artifactHeaderButton(element, info) {
    if (!info.artifactHeader || editable(element)) return false;
    const btn = element.closest('button');
    if (!btn || !info.artifactHeader.contains(btn)) return false;
    return !info.artifactView || info.artifactHeader.parentElement === info.artifactView;
  }

  function overviewSlot(element, info = inspectAncestors(element)) {
    if (info.hardProtected) return null;
    if (info.auxSection) {
      return info.hoverLabel ? strictDictionarySlot : null;
    }
    const panel = info.overviewPanel;
    if (!panel) return null;
    if (info.overviewCustomizeTrigger) return strictDictionarySlot;

    const row = info.overviewRow;
    if (row && panel.contains(row)) {
      return info.hoverLabel && row.contains(info.hoverLabel) ? strictDictionarySlot : null;
    }

    const hoverLabel = info.hoverLabel;
    if (hoverLabel && panel.contains(hoverLabel)) {
      const a6Header = hoverLabel.parentElement;
      if (a6Header?.parentElement?.parentElement === panel) return strictDictionarySlot;
      const section = a6Header?.parentElement;
      if (
        section &&
        !a6Header.previousElementSibling &&
        section.classList.contains('p-1') &&
        section.parentElement?.parentElement === panel
      ) {
        return strictDictionarySlot;
      }
    }

    const expandBtn = info.expandButton;
    if (expandBtn && panel.contains(expandBtn)) {
      const section = expandBtn.parentElement;
      if (
        expandBtn.previousElementSibling &&
        section?.classList.contains('p-1') &&
        section.parentElement?.parentElement === panel
      ) {
        return overviewExpandSlot;
      }
    }
    return null;
  }

  function escapeAttrSelector(value) {
    if (typeof CSS !== 'undefined' && typeof CSS.escape === 'function') {
      return CSS.escape(value);
    }
    return String(value).replace(/["\\\]\r\n]/g, '\\$&');
  }

  function isTriggerAuthorized(trigger) {
    const tInfo = inspectAncestors(trigger);
    if (tInfo.hardProtected || tInfo.artifactView) return false;
    if (portalBlocker && portalBlocker(trigger)) return false;
    if (
      feedbackButton(trigger, tInfo) ||
      statusButton(trigger) === trigger ||
      composerControl(trigger, tInfo)
    ) {
      return true;
    }
    if (tInfo.inChat || tInfo.inArtifactSidebar) return false;
    return Boolean(shellOwner(trigger, tInfo) || overviewSlot(trigger, tInfo));
  }

  function verifiedTooltipSlot(element, info) {
    const tip = info.tooltipEl;
    if (!tip || info.inShortcutNode) return null;
    const tipId = tip.getAttribute('id');
    if (!tipId || /\s/.test(tipId)) return null;

    const cached = tooltipCache.get(tip);
    if (cached && cached.rev === tooltipRev) {
      return cached.allowed ? tooltipSlot : null;
    }

    const doc = element.ownerDocument;
    if (!doc?.querySelectorAll) return null;
    const triggers = doc.querySelectorAll(`[aria-describedby~="${escapeAttrSelector(tipId)}"]`);
    const allowed = triggers.length === 1 && isTriggerAuthorized(triggers[0]);
    tooltipCache.set(tip, { rev: tooltipRev, allowed });
    return allowed ? tooltipSlot : null;
  }

  function textSlot(element) {
    const info = inspectAncestors(element);
    if (info.hardProtected) return null;
    if (artifactHeaderButton(element, info)) return artifactSlot;
    if (info.artifactView || editable(element)) return null;

    const step = statusButton(element);
    if (step) return statusSlot;
    const header = fileHeader(element, info);
    if (header) {
      const review = element.closest('button[data-testid="changed-files-card-review"]');
      if (review?.parentElement === header) return fileActionSlot;
      return element === header.firstElementChild?.firstElementChild ? summarySlot : null;
    }
    if (element.matches('span[data-screenshot-volatile][data-tooltip-id]')) {
      const bar = feedbackToolbar(info);
      if (bar && up(element, 2) === bar) return timeSlot;
    }
    const permission = permissionSlot(element, info);
    if (permission) return permission;
    if (composerPlaceholder(element, info)) return placeholderSlot;
    if (composerControl(element, info)) return composerSlot;
    if (homeGreeting(element, info)) return homeGreetingSlot;
    if (info.inChat) return null;

    const overview = overviewSlot(element, info);
    if (overview) return overview;
    const tooltip = verifiedTooltipSlot(element, info);
    if (tooltip) return tooltip;

    if (info.artifactHeader || info.inArtifactSidebar) return null;
    const confirmation = confirmSlot(element, info);
    if (confirmation) return confirmation;
    if (!shellOwner(element, info)) return null;
    return element.matches('[data-screenshot-volatile]') ? timeSlot : shellSlot;
  }

  function attrFormatter(element, name) {
    const info = inspectAncestors(element);
    if (info.hardProtected) return null;
    if (artifactHeaderButton(element, info) && name !== 'placeholder') return formats.artifactAction;
    if (info.artifactView) return null;

    if (name === 'placeholder') {
      if (!element.matches(input)) return null;
      if (inComposer(info)) return shellAttr;
      return !info.inChat && !info.inArtifactSidebar && shellOwner(element, info) ? shellAttr : null;
    }
    if (editable(element)) return null;
    if (feedbackButton(element, info)) return formats.feedback;
    if (statusButton(element) === element) return formats.status;
    if (composerControl(element, info) && element.matches('button, [role="combobox"], [role="switch"]')) return formats.composer;
    if (info.inChat) return null;
    const overview = overviewSlot(element, info);
    if (overview) return strictDictionaryFormat;
    if (info.inArtifactSidebar) return null;
    return shellOwner(element, info) ? shellAttr : null;
  }

  return {
    textSlot,
    attrFormatter,
    isProtected,
    shouldPrune,
    shellOwner,
    overviewSlot,
    bumpTooltipRev,
    setPortalBlocker,
    statusButton,
    statusCandidate,
    ownsStatusHeader,
    isProtectedRoot: (element) =>
      isHardProtectedNode(element) || element?.getAttribute?.('data-testid') === 'artifact-view',
  };
})();

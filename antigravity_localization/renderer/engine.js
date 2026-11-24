(() => {
  const fields = ['placeholder', 'title', 'aria-label', 'data-tooltip', 'data-title'];
  const boundaryAttrs = [
    'data-agy-turn-host', 'data-testid', 'data-lexical-editor',
    'data-markdown', 'data-markdown-root', 'data-message-content',
    'data-artifact-content', 'data-artifact-preview', 'data-diagnostic',
    'data-quotable-root', 'data-select-popup',
  ];
  const boundaryAttrSet = new Set(boundaryAttrs);

  const isStandaloneSettings = window.location?.pathname === '/settings-standalone';
  const ROUTING_CLASSES = new Set([
    'prose', 'monaco-editor', 'xterm', 'katex', 'bleed-contain',
    'artifact-preview', 'group/user-input-step',
    'settings-modal-container', 'agy-overlay', 'agy-dialog',
    'agy-hover-label', 'home-greeting-title', 'surface-composer',
    'agy-composer-footer', 'agy-button-icon', 'artifact-sidebar',
    'chat-messages', 'chat-scroll-pane', 'p-1',
    ...(isStandaloneSettings ? ['grow', 'w-full', 'overflow-auto', 'relative', 'flex-grow', 'min-h-0'] : []),
  ]);
  const ROUTING_CLASS_HINT_RE = isStandaloneSettings
    ? /\b(?:prose|monaco-editor|xterm|katex|bleed-contain|artifact-(?:preview|sidebar)|settings-modal-container|agy-(?:overlay|dialog|hover-label|composer-footer|button-icon)|home-greeting-title|surface-composer|chat-(?:messages|scroll-pane)|p-1|grow|w-full|overflow-auto|relative|flex-grow|min-h-0)\b|group\/user-input-step|(?:thought|thinking|reasoning)-content/
    : /\b(?:prose|monaco-editor|xterm|katex|bleed-contain|artifact-(?:preview|sidebar)|settings-modal-container|agy-(?:overlay|dialog|hover-label|composer-footer|button-icon)|home-greeting-title|surface-composer|chat-(?:messages|scroll-pane)|p-1)\b|group\/user-input-step|(?:thought|thinking|reasoning)-content/;

  function routingClassSignature(cls) {
    if (!cls || typeof cls !== 'string' || !ROUTING_CLASS_HINT_RE.test(cls)) return '';
    const parts = cls.split(/\s+/);
    const hits = [];
    for (let i = 0; i < parts.length; i++) {
      const tok = parts[i];
      if (!tok) continue;
      if (
        ROUTING_CLASSES.has(tok) ||
        (tok.includes('-content') &&
          (tok.includes('thought-content') ||
            tok.includes('thinking-content') ||
            tok.includes('reasoning-content')))
      ) {
        hits.push(tok);
      }
    }
    return hits.length ? hits.sort().join(' ') : '';
  }

  const textSlots = new WeakMap();
  const attrSlots = new WeakMap();
  const ancestorIndex = new WeakMap();
  const mounts = new Set();
  const updatedTexts = new Set();
  const updatedAttrs = new Map();
  const revokedSubtrees = new Set();
  const openTooltips = new Set();
  const openMenus = new Set();
  const portals = createPortalRegistry(connected, index, revoke);
  dom.setPortalBlocker?.(portals.blocks);
  let cleanup = null;
  let walk = null;
  let scheduled = false;

  function connected(node) {
    return node?.isConnected && node.ownerDocument === document && node.getRootNode() === document;
  }

  function index(node, reconcile) {
    let memberships = new Set();
    function refresh() {
      const next = new Set();
      const element = node.nodeType === 1 ? node : node.parentElement;
      for (let parent = element; parent; parent = parent.parentElement) {
        let entries = ancestorIndex.get(parent);
        if (!entries) ancestorIndex.set(parent, entries = new Set());
        entries.add(reconcile);
        next.add(entries);
      }
      for (const entries of memberships) {
        if (!next.has(entries)) entries.delete(reconcile);
      }
      memberships = next;
    }
    refresh();
    return {
      refresh,
      forget() {
        for (const entries of memberships) entries.delete(reconcile);
      },
    };
  }

  function revoke(element) {
    if (ancestorIndex.get(element)?.size) revokedSubtrees.add(element);
  }

  function textSlot(text) {
    const element = text.parentElement;
    return connected(text) && element && !portals.blocks(element) ? dom.textSlot(element) : null;
  }

  function releaseText(text, state) {
    textSlots.delete(text);
    state.link.forget();
    // A native write from the application can assign the same characters.
    const externallyUpdated = state.observer.takeRecords().length > 0;
    state.observer.disconnect();
    const last = state.translation;
    if (!externallyUpdated && last && text.ownerDocument === document && text.data === last.output) {
      text.data = last.source;
    }
  }

  function reconcileText(text, state) {
    const slot = textSlot(text);
    if (slot === state.slot) {
      state.link.refresh();
    } else {
      releaseText(text, state);
      if (slot) updatedTexts.add(text);
    }
  }

  function observeText(text, slot) {
    const existing = textSlots.get(text);
    if (existing) return existing;
    const state = {
      slot,
      translation: null,
      link: null,
      observer: new MutationObserver(() => {
        state.translation = null;
        if (textSlot(text) === slot) updatedTexts.add(text);
        else reconcileText(text, state);
        schedule();
      }),
    };
    state.link = index(text, () => reconcileText(text, state));
    state.observer.observe(text, { characterData: true });
    textSlots.set(text, state);
    return state;
  }

  function translateText(text) {
    const slot = textSlot(text);
    const old = textSlots.get(text);
    if (old && old.slot !== slot) releaseText(text, old);
    if (!slot) return;
    if (slot.isTooltip) {
      const tip = text.parentElement?.closest?.('[role="tooltip"][id]');
      if (tip) openTooltips.add(tip);
    }
    if (slot.isMenu) {
      const menu = text.parentElement?.closest?.('[role="menu"][id]');
      if (menu) openMenus.add(menu);
    }
    const source = text.data;
    const output = slot.format(source);
    if (output === source) {
      if (slot.dynamic) observeText(text, slot);
      return;
    }
    const state = observeText(text, slot);
    state.observer.takeRecords();
    state.translation = null;
    text.data = output;
    state.observer.takeRecords();
    state.translation = { source, output };
  }

  function attrFormatter(element, name) {
    return connected(element) && !portals.blocks(element) ? dom.attrFormatter(element, name) : null;
  }

  function invalidateAttrs(state, records, ownName) {
    for (const record of records) {
      if (record.attributeName === ownName) {
        ownName = null;
      } else {
        state.translations.delete(record.attributeName);
      }
    }
  }

  function dropEmptyAttrState(element, state) {
    if (state.translations.size) return;
    state.observer.disconnect();
    state.link.forget();
    attrSlots.delete(element);
  }

  function reconcileAttrs(element, state) {
    invalidateAttrs(state, state.observer.takeRecords());
    for (const [name, last] of state.translations) {
      const format = attrFormatter(element, name);
      if (format === last.format) continue;
      state.translations.delete(name);
      if (element.ownerDocument === document && element.getAttribute(name) === last.output) {
        element.setAttribute(name, last.source);
        invalidateAttrs(state, state.observer.takeRecords());
      }
      if (format) queueAttr(element, name);
    }
    if (state.translations.size) state.link.refresh();
    else dropEmptyAttrState(element, state);
  }

  function observeAttrs(element) {
    const state = { translations: new Map(), observer: null, link: null };
    state.observer = new MutationObserver((records) => {
      invalidateAttrs(state, records);
      dropEmptyAttrState(element, state);
    });
    state.observer.observe(element, { attributes: true, attributeFilter: fields });
    state.link = index(element, () => reconcileAttrs(element, state));
    attrSlots.set(element, state);
    return state;
  }

  function translateAttr(element, name) {
    const source = element.getAttribute(name);
    if (!source) return;
    const format = attrFormatter(element, name);
    if (!format) return;
    const output = format(source);
    if (output === source) return;
    // Track the element itself until cleanup, including intervening detached
    // mutations after the body observer stops seeing the removed subtree.
    const state = attrSlots.get(element) ?? observeAttrs(element);
    invalidateAttrs(state, state.observer.takeRecords());
    try {
      element.setAttribute(name, output);
      state.translations.set(name, { source, output, format });
      invalidateAttrs(state, state.observer.takeRecords(), name);
    } finally {
      dropEmptyAttrState(element, state);
    }
  }

  function canInspect(node) {
    return node.nodeType === 1 || node.nodeType === 3;
  }

  function prune(node) {
    if (!canInspect(node)) return true;
    const element = node.nodeType === 1 ? node : node.parentElement;
    if (node.nodeType === 1 && node.id) portals.indexPanel(node);
    const blocked = dom.shouldPrune ? dom.shouldPrune(element) : dom.isProtected(element);
    return !element || blocked || portals.blocks(element);
  }

  function queueAttr(element, attr) {
    let attrs = updatedAttrs.get(element);
    if (!attrs) updatedAttrs.set(element, attrs = new Set());
    attrs.add(attr);
  }

  function inspectNode(node) {
    if (node.nodeType === 3) {
      updatedTexts.add(node);
      return;
    }
    if (!connected(node)) return;
    if (node.hasAttribute('aria-controls')) portals.syncTrigger(node);
    for (const attr of fields) {
      if (node.hasAttribute(attr)) queueAttr(node, attr);
    }
  }

  function take(set) {
    const value = set.values().next().value;
    set.delete(value);
    return value;
  }

  function hasWork() {
    return cleanup || revokedSubtrees.size || walk || mounts.size ||
      portals.hasPending() || updatedTexts.size || updatedAttrs.size;
  }

  function flush() {
    scheduled = false;
    const deadline = performance.now() + 4;
    do {
      try {
        if (cleanup || revokedSubtrees.size) {
          if (!cleanup) {
            cleanup = ancestorIndex.get(take(revokedSubtrees)).values();
          }
          const next = cleanup.next();
          if (next.done) cleanup = null;
          else next.value();
        } else if (walk || mounts.size) {
          // Discover every pending trigger before submitting display writes.
          if (!walk) walk = createMountWalk(take(mounts), prune);
          const next = walk.next();
          if (next.done) walk = null;
          else if (next.value) inspectNode(next.value);
        } else if (portals.hasPending()) {
          portals.settleStep();
        } else if (updatedAttrs.size) {
          const [element, attrs] = updatedAttrs.entries().next().value;
          const attr = take(attrs);
          if (!attrs.size) updatedAttrs.delete(element);
          translateAttr(element, attr);
        } else if (updatedTexts.size) {
          translateText(take(updatedTexts));
        }
      } catch (_) {
        // A stale renderer node cannot stop the rest of the queue.
      }
    } while (hasWork() && performance.now() < deadline);
    if (hasWork()) schedule();
  }

  function schedule() {
    if (scheduled || !hasWork()) return;
    scheduled = true;
    requestAnimationFrame(flush);
  }

  function reconcileRemoval(node, parent, budget) {
    if (node.parentNode === parent && connected(node)) return;
    if (node.nodeType === 3) {
      const state = textSlots.get(node);
      if (state && budget.remaining) {
        budget.remaining--;
        reconcileText(node, state);
      } else if (state) {
        updatedTexts.add(node);
      }
      return;
    }
    if (node.nodeType !== 1) return;
    const entries = ancestorIndex.get(node);
    if (!entries?.size) return;
    // A narrow subtree can be unobserved before its pending text notifications
    // are delivered. Keep a shared cap for bulk removal in the same delivery.
    if (entries.size > budget.remaining) {
      revoke(node);
      return;
    }
    budget.remaining -= entries.size;
    for (const reconcile of entries) {
      try { reconcile(); } catch (_) {}
    }
  }

  function syncTooltipsForAttr(oldValue, newValue) {
    for (const raw of [oldValue, newValue]) {
      if (!raw || typeof raw !== 'string') continue;
      for (const id of raw.split(/\s+/)) {
        if (!id) continue;
        const tip = document.getElementById(id);
        if (!tip || tip.getAttribute('role') !== 'tooltip') continue;
        if (ancestorIndex.get(tip)?.size) revoke(tip);
        const prunable = dom.shouldPrune ? dom.shouldPrune(tip) : dom.isProtected(tip);
        if (!prunable && connected(tip)) mounts.add(tip);
      }
    }
  }

  function refreshOpenTooltips() {
    if (!openTooltips.size) return;
    for (const tip of openTooltips) {
      if (!connected(tip) || !ancestorIndex.get(tip)?.size) {
        openTooltips.delete(tip);
      } else {
        revoke(tip);
      }
    }
  }

  function syncMenusForAttr(oldValue, newValue) {
    for (const raw of [oldValue, newValue]) {
      if (!raw || typeof raw !== 'string') continue;
      for (const id of raw.split(/\s+/)) {
        if (!id) continue;
        const menu = document.getElementById(id);
        if (!menu || menu.getAttribute('role') !== 'menu') continue;
        if (ancestorIndex.get(menu)?.size) revoke(menu);
        const prunable = dom.shouldPrune ? dom.shouldPrune(menu) : dom.isProtected(menu);
        if (!prunable && connected(menu)) mounts.add(menu);
      }
    }
  }

  function refreshOpenMenus() {
    if (!openMenus.size) return;
    for (const menu of openMenus) {
      if (!connected(menu) || !ancestorIndex.get(menu)?.size) {
        openMenus.delete(menu);
      } else {
        revoke(menu);
      }
    }
  }

  function queueEligibleMount(element) {
    const prunable = dom.shouldPrune ? dom.shouldPrune(element) : dom.isProtected(element);
    if (prunable || !connected(element)) return;
    const role = element.getAttribute('role');
    if (
      role === 'menu' ||
      role === 'dialog' ||
      (dom.shellOwner && dom.shellOwner(element)) ||
      (dom.overviewSlot && dom.overviewSlot(element)) ||
      dom.textSlot(element)
    ) {
      mounts.add(element);
    }
  }

  function observeAttrChange(element, name, oldValue) {
    if (name === 'aria-controls' || name === 'aria-expanded') {
      if (element.hasAttribute('aria-controls') || portals.hasTrigger(element)) portals.syncTrigger(element);
      if (name === 'aria-controls') {
        dom.bumpTooltipRev?.();
        syncMenusForAttr(oldValue, element.getAttribute('aria-controls'));
        refreshOpenMenus();
      }
    } else if (name === 'aria-describedby') {
      dom.bumpTooltipRev?.();
      syncTooltipsForAttr(oldValue, element.getAttribute('aria-describedby'));
      refreshOpenTooltips();
    } else if (name === 'aria-labelledby') {
      dom.bumpTooltipRev?.();
      if (element.getAttribute('role') === 'menu') {
        if (ancestorIndex.get(element)?.size) revoke(element);
        const prunable = dom.shouldPrune ? dom.shouldPrune(element) : dom.isProtected(element);
        if (!prunable && connected(element)) mounts.add(element);
      }
      refreshOpenMenus();
    } else if (name === 'id') {
      dom.bumpTooltipRev?.();
      portals.indexPanel(element);
      if (connected(element)) portals.inspectPanel(element);
      if (ancestorIndex.get(element)?.size && dom.isProtected(element)) revoke(element);
      const prunable = dom.shouldPrune ? dom.shouldPrune(element) : dom.isProtected(element);
      const role = element.getAttribute('role');
      if (!prunable && connected(element) && (role === 'tooltip' || role === 'menu')) mounts.add(element);
      refreshOpenTooltips();
      refreshOpenMenus();
    } else if (name === 'contenteditable') {
      if (dom.isProtected(element)) revoke(element);
      else mounts.add(element);
    } else if (name === 'class') {
      const nextSig = routingClassSignature(element.getAttribute('class'));
      const prevSig = routingClassSignature(oldValue);
      if (nextSig === prevSig) return;
      dom.bumpTooltipRev?.();
      if (ancestorIndex.get(element)?.size) revoke(element);
      queueEligibleMount(element);
      refreshOpenTooltips();
      refreshOpenMenus();
    } else if (name === 'role' || boundaryAttrSet.has(name)) {
      const nextVal = element.getAttribute(name);
      if (oldValue === nextVal) return;
      dom.bumpTooltipRev?.();
      const isBoundary = boundaryAttrSet.has(name);
      if (
        ancestorIndex.get(element)?.size &&
        (dom.isProtected(element) || nextVal === 'log' || isBoundary)
      ) {
        revoke(element);
      }
      queueEligibleMount(element);
      refreshOpenTooltips();
      refreshOpenMenus();
    } else {
      queueAttr(element, name);
    }
  }

  const bodyObserver = new MutationObserver((records) => {
    portals.noteMutations(records);
    const budget = { remaining: 64 };
    let touchedChildList = false;
    let shouldCheckOpenTooltips = false;
    let shouldCheckOpenMenus = false;
    for (const record of records) {
      try {
        if (record.type === 'childList') {
          touchedChildList = true;
          walk?.childrenChanged(record);
          for (const node of record.removedNodes) {
            if (node.nodeType === 1) {
              if (!shouldCheckOpenTooltips && openTooltips.size &&
                  (node.hasAttribute('aria-describedby') || node.firstElementChild)) {
                shouldCheckOpenTooltips = true;
              }
              if (!shouldCheckOpenMenus && openMenus.size &&
                  (node.hasAttribute('aria-controls') || node.hasAttribute('aria-labelledby') || node.firstElementChild)) {
                shouldCheckOpenMenus = true;
              }
            }
            try { reconcileRemoval(node, record.target, budget); } catch (_) {}
          }
          for (const node of record.addedNodes) {
            if (node.nodeType === 1) {
              if (!shouldCheckOpenTooltips && openTooltips.size &&
                  node.getAttribute('role') !== 'tooltip' &&
                  (node.hasAttribute('aria-describedby') || node.firstElementChild)) {
                shouldCheckOpenTooltips = true;
              }
              if (!shouldCheckOpenMenus && openMenus.size &&
                  node.getAttribute('role') !== 'menu' &&
                  (node.hasAttribute('aria-controls') || node.hasAttribute('aria-labelledby') || node.firstElementChild)) {
                shouldCheckOpenMenus = true;
              }
            }
            if (canInspect(node) && connected(node)) mounts.add(node);
          }
        } else {
          observeAttrChange(record.target, record.attributeName, record.oldValue);
        }
      } catch (_) {}
    }
    if (touchedChildList) {
      dom.bumpTooltipRev?.();
      if (shouldCheckOpenTooltips) refreshOpenTooltips();
      if (shouldCheckOpenMenus) refreshOpenMenus();
    }
    schedule();
  });

  function start() {
    if (!document.body || window.top !== window) return;
    bodyObserver.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeOldValue: true,
      attributeFilter: [...fields, 'aria-controls', 'aria-expanded', 'aria-describedby', 'aria-labelledby', 'id', 'contenteditable', 'class', 'role', ...boundaryAttrs],
    });
    mounts.add(document.body);
    schedule();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();

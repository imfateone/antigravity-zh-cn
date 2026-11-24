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
    'chat-messages', 'chat-scroll-pane',
    ...(isStandaloneSettings ? ['grow', 'w-full', 'overflow-auto', 'relative', 'flex-grow', 'min-h-0'] : []),
  ]);
  const ROUTING_CLASS_HINT_RE = isStandaloneSettings
    ? /\b(?:prose|monaco-editor|xterm|katex|bleed-contain|artifact-(?:preview|sidebar)|settings-modal-container|agy-(?:overlay|dialog|hover-label|composer-footer|button-icon)|home-greeting-title|surface-composer|chat-(?:messages|scroll-pane)|grow|w-full|overflow-auto|relative|flex-grow|min-h-0)\b|group\/user-input-step|(?:thought|thinking|reasoning)-content/
    : /\b(?:prose|monaco-editor|xterm|katex|bleed-contain|artifact-(?:preview|sidebar)|settings-modal-container|agy-(?:overlay|dialog|hover-label|composer-footer|button-icon)|home-greeting-title|surface-composer|chat-(?:messages|scroll-pane))\b|group\/user-input-step|(?:thought|thinking|reasoning)-content/;

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
  const trackedPortals = new Map();
  const portalsByTrigger = new Map();
  const portalsById = new Map();
  const dirtyPortals = new Set();
  const portals = createPortalRegistry(connected, index, revoke);
  dom.setPortalBlocker?.(portals.blocks);
  let cleanup = null;
  let walk = null;
  let scheduled = false;

  function connected(node) {
    return node?.isConnected && node.ownerDocument === document && node.getRootNode() === document;
  }

  function index(node, reconcile) {
    let chain = [];
    let memberships = null;
    function refresh() {
      const element = node.nodeType === 1 ? node : node.parentElement;
      if (chain.length) {
        let idx = 0;
        let same = true;
        for (let parent = element; parent; parent = parent.parentElement) {
          const entries = ancestorIndex.get(parent);
          if (!entries || chain[idx++] !== entries) {
            same = false;
            break;
          }
        }
        if (same && idx === chain.length) return;
      }
      const nextChain = [];
      const next = new Set();
      for (let parent = element; parent; parent = parent.parentElement) {
        let entries = ancestorIndex.get(parent);
        if (!entries) ancestorIndex.set(parent, entries = new Set());
        entries.add(reconcile);
        nextChain.push(entries);
        next.add(entries);
      }
      if (memberships) {
        for (const entries of memberships) {
          if (!next.has(entries)) entries.delete(reconcile);
        }
      }
      chain = nextChain;
      memberships = next;
    }
    refresh();
    return {
      refresh,
      forget() {
        if (memberships) {
          for (const entries of memberships) entries.delete(reconcile);
        }
        chain.length = 0;
        memberships = null;
      },
    };
  }

  function revoke(element) {
    if (ancestorIndex.get(element)?.size) revokedSubtrees.add(element);
  }

  function textSlot(text) {
    const element = text.parentElement;
    return connected(text) && element && !portals.blocks(element) ? dom.textSlot(element, text) : null;
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
    if (state.slot.isTooltip || state.slot.isMenu) {
      const portal = text.parentElement?.closest?.(state.slot.isMenu ? '[role="menu"][id]' : '[role="tooltip"][id]');
      if (portal && (!connected(portal) || !ancestorIndex.get(portal)?.size)) {
        untrackPortal(portal);
      }
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
      if (tip) trackPortal(tip, 'tooltip');
    }
    if (slot.isMenu) {
      const menu = text.parentElement?.closest?.('[role="menu"][id]');
      if (menu) trackPortal(menu, 'menu');
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

  function escapeSelectorValue(value) {
    if (typeof CSS !== 'undefined' && typeof CSS.escape === 'function') {
      return CSS.escape(value);
    }
    return String(value).replace(/["\\\]\r\n]/g, '\\$&');
  }

  function addIndexEntry(map, key, val) {
    let entries = map.get(key);
    if (!entries) map.set(key, entries = new Set());
    entries.add(val);
  }

  function deleteIndexEntry(map, key, val) {
    const entries = map.get(key);
    if (!entries) return;
    entries.delete(val);
    if (!entries.size) map.delete(key);
  }

  function untrackPortal(portal) {
    const info = trackedPortals.get(portal);
    if (!info) return;
    trackedPortals.delete(portal);
    if (info.trigger) deleteIndexEntry(portalsByTrigger, info.trigger, portal);
    if (info.portalId) deleteIndexEntry(portalsById, info.portalId, portal);
    if (info.triggerId) deleteIndexEntry(portalsById, info.triggerId, portal);
    dirtyPortals.delete(portal);
    dom.invalidatePortal?.(portal);
  }

  function trackPortal(portal, kind) {
    if (!portal) return;
    const portalId = portal.getAttribute('id') || '';
    const trigger = dom.getPortalOwner?.(portal) || null;
    const triggerId = trigger?.getAttribute?.('id') || '';
    const prev = trackedPortals.get(portal);
    if (
      prev &&
      prev.kind === kind &&
      prev.portalId === portalId &&
      prev.trigger === trigger &&
      prev.triggerId === triggerId
    ) {
      return;
    }
    if (prev) untrackPortal(portal);
    trackedPortals.set(portal, { kind, portalId, trigger, triggerId });
    if (trigger) addIndexEntry(portalsByTrigger, trigger, portal);
    if (portalId) addIndexEntry(portalsById, portalId, portal);
    if (triggerId) addIndexEntry(portalsById, triggerId, portal);
  }

  function markPortalDirty(portal) {
    if (portal) dirtyPortals.add(portal);
  }

  function markPortalsForIds(rawAttr) {
    if (!portalsById.size || !rawAttr || typeof rawAttr !== 'string') return;
    for (const id of rawAttr.split(/\s+/)) {
      if (!id) continue;
      const set = portalsById.get(id);
      if (set) {
        for (const portal of set) dirtyPortals.add(portal);
      }
    }
  }

  function markTriggerAndDescendantPortalsDirty(element) {
    if (!portalsByTrigger.size || !element) return;
    for (const [trigger, set] of portalsByTrigger) {
      if (trigger === element || !connected(trigger) || (element.nodeType === 1 && element.contains(trigger))) {
        for (const portal of set) dirtyPortals.add(portal);
      }
    }
  }

  function markSubtreePortalsForAddedNode(node) {
    if (!trackedPortals.size || node.nodeType !== 1) return;
    const nid = node.getAttribute('id');
    if (nid) markPortalsForIds(nid);
    const desc = node.getAttribute('aria-describedby');
    if (desc) markPortalsForIds(desc);
    const ctrls = node.getAttribute('aria-controls');
    if (ctrls) markPortalsForIds(ctrls);
    if (!node.firstElementChild || !portalsById.size) return;
    for (const [id, set] of portalsById) {
      const esc = escapeSelectorValue(id);
      if (node.querySelector(`[id="${esc}"], [aria-controls~="${esc}"], [aria-describedby~="${esc}"]`)) {
        for (const portal of set) dirtyPortals.add(portal);
      }
    }
  }

  function markPortalsForRemovedNode(node) {
    if (!trackedPortals.size) return;
    for (const [portal, info] of trackedPortals) {
      if (
        portal === node ||
        !connected(portal) ||
        (node.nodeType === 1 && node.contains(portal)) ||
        (info.trigger && (info.trigger === node || !connected(info.trigger) || (node.nodeType === 1 && node.contains(info.trigger))))
      ) {
        dirtyPortals.add(portal);
      }
    }
  }

  function flushDirtyPortals() {
    if (!dirtyPortals.size) return;
    for (const portal of dirtyPortals) {
      dom.invalidatePortal?.(portal);
      if (ancestorIndex.get(portal)?.size) revoke(portal);
      if (!connected(portal)) {
        untrackPortal(portal);
        continue;
      }
      const prunable = dom.shouldPrune ? dom.shouldPrune(portal) : dom.isProtected(portal);
      if (!prunable) mounts.add(portal);
    }
    dirtyPortals.clear();
  }

  function syncTooltipsForAttr(oldValue, newValue) {
    for (const raw of [oldValue, newValue]) {
      if (!raw || typeof raw !== 'string') continue;
      for (const id of raw.split(/\s+/)) {
        if (!id) continue;
        const tip = document.getElementById(id);
        if (!tip || tip.getAttribute('role') !== 'tooltip') continue;
        dom.invalidatePortal?.(tip);
        if (ancestorIndex.get(tip)?.size) revoke(tip);
        const prunable = dom.shouldPrune ? dom.shouldPrune(tip) : dom.isProtected(tip);
        if (!prunable && connected(tip)) mounts.add(tip);
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
        dom.invalidatePortal?.(menu);
        if (ancestorIndex.get(menu)?.size) revoke(menu);
        const prunable = dom.shouldPrune ? dom.shouldPrune(menu) : dom.isProtected(menu);
        if (!prunable && connected(menu)) mounts.add(menu);
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
        const nextVal = element.getAttribute('aria-controls');
        markPortalsForIds(oldValue);
        markPortalsForIds(nextVal);
        markTriggerAndDescendantPortalsDirty(element);
        syncMenusForAttr(oldValue, nextVal);
      }
    } else if (name === 'aria-describedby') {
      const nextVal = element.getAttribute('aria-describedby');
      markPortalsForIds(oldValue);
      markPortalsForIds(nextVal);
      markTriggerAndDescendantPortalsDirty(element);
      syncTooltipsForAttr(oldValue, nextVal);
    } else if (name === 'aria-labelledby') {
      if (element.getAttribute('role') === 'menu') {
        markPortalDirty(element);
        dom.invalidatePortal?.(element);
        if (ancestorIndex.get(element)?.size) revoke(element);
        const prunable = dom.shouldPrune ? dom.shouldPrune(element) : dom.isProtected(element);
        if (!prunable && connected(element)) mounts.add(element);
      }
    } else if (name === 'aria-haspopup') {
      markTriggerAndDescendantPortalsDirty(element);
      if (element.hasAttribute('aria-controls')) {
        syncMenusForAttr(null, element.getAttribute('aria-controls'));
      }
    } else if (name === 'id') {
      const newId = element.getAttribute('id');
      markPortalsForIds(oldValue);
      markPortalsForIds(newId);
      if (trackedPortals.has(element)) markPortalDirty(element);
      markTriggerAndDescendantPortalsDirty(element);
      portals.indexPanel(element);
      if (connected(element)) portals.inspectPanel(element);
      if (ancestorIndex.get(element)?.size && dom.isProtected(element)) revoke(element);
      const prunable = dom.shouldPrune ? dom.shouldPrune(element) : dom.isProtected(element);
      const role = element.getAttribute('role');
      if (role === 'tooltip' || role === 'menu') {
        dom.invalidatePortal?.(element);
        if (!prunable && connected(element)) mounts.add(element);
      }
    } else if (name === 'contenteditable') {
      markTriggerAndDescendantPortalsDirty(element);
      if (element.hasAttribute('aria-controls')) syncMenusForAttr(null, element.getAttribute('aria-controls'));
      if (element.hasAttribute('aria-describedby')) syncTooltipsForAttr(null, element.getAttribute('aria-describedby'));
      if (dom.isProtected(element) || element.isContentEditable) revoke(element);
      else mounts.add(element);
    } else if (name === 'class') {
      const nextSig = routingClassSignature(element.getAttribute('class'));
      const prevSig = routingClassSignature(oldValue);
      const isOverviewP1 =
        element.parentElement?.parentElement?.getAttribute?.('data-testid') === 'overview-panel' &&
        (element.classList.contains('p-1') || /\bp-1\b/.test(oldValue || ''));
      if (nextSig === prevSig && !isOverviewP1) return;
      markTriggerAndDescendantPortalsDirty(element);
      if (ancestorIndex.get(element)?.size) revoke(element);
      queueEligibleMount(element);
    } else if (name === 'role' || boundaryAttrSet.has(name)) {
      const nextVal = element.getAttribute(name);
      if (oldValue === nextVal) return;
      markTriggerAndDescendantPortalsDirty(element);
      const isBoundary = boundaryAttrSet.has(name);
      if (
        ancestorIndex.get(element)?.size &&
        (dom.isProtected(element) || nextVal === 'log' || isBoundary)
      ) {
        revoke(element);
      }
      queueEligibleMount(element);
    } else {
      if (name === 'aria-label') {
        if (portalsByTrigger.has(element)) markTriggerAndDescendantPortalsDirty(element);
        if (element.hasAttribute('aria-controls')) {
          syncMenusForAttr(null, element.getAttribute('aria-controls'));
        }
      }
      queueAttr(element, name);
    }
  }

  const bodyObserver = new MutationObserver((records) => {
    portals.noteMutations(records);
    const budget = { remaining: 64 };
    let lastTarget = null;
    let lastTargetPruned = false;
    for (const record of records) {
      try {
        if (record.type === 'childList') {
          if (record.target !== lastTarget) {
            lastTarget = record.target;
            lastTargetPruned = record.target?.nodeType === 1 &&
              Boolean(dom.shouldPrune ? dom.shouldPrune(record.target) : dom.isProtected(record.target));
          }
          const targetPruned = lastTargetPruned;
          if (!targetPruned) walk?.childrenChanged(record);
          for (const node of record.removedNodes) {
            markPortalsForRemovedNode(node);
            if (!targetPruned ||
                (node.nodeType === 1 && ancestorIndex.get(node)?.size) ||
                (node.nodeType === 3 && textSlots.has(node))) {
              try { reconcileRemoval(node, record.target, budget); } catch (_) {}
            }
          }
          for (const node of record.addedNodes) {
            markSubtreePortalsForAddedNode(node);
            if (!targetPruned && canInspect(node) && connected(node)) mounts.add(node);
          }
        } else {
          observeAttrChange(record.target, record.attributeName, record.oldValue);
        }
      } catch (_) {}
    }
    flushDirtyPortals();
    schedule();
  });

  function start() {
    if (!document.body || window.top !== window) return;
    bodyObserver.observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeOldValue: true,
      attributeFilter: [...fields, 'aria-controls', 'aria-expanded', 'aria-describedby', 'aria-labelledby', 'aria-haspopup', 'id', 'contenteditable', 'class', 'role', ...boundaryAttrs],
    });
    mounts.add(document.body);
    schedule();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
  else start();
})();

function createPortalRegistry(connected, index, onProtect) {
  const triggers = new WeakMap();
  const ownersById = new Map();
  const panelsById = new Map();
  const indexedPanels = new WeakMap();
  const protectedPanels = new WeakSet();
  let journal = null;
  let settlement = null;
  let revision = 0;

  function addToIndex(index, name, node) {
    let entries = index.get(name);
    if (!entries) index.set(name, entries = new Set());
    entries.add(node);
  }

  function removeFromIndex(index, name, node) {
    const entries = index.get(name);
    entries.delete(node);
    if (!entries.size) index.delete(name);
  }

  function pendingWork() {
    return { buttons: new Set(), removedRoots: new Set(), panelIds: new Set() };
  }

  function beginRecord() {
    journal ??= {
      start: revision - 1,
      changes: new WeakMap(),
      oldIds: new Map(),
      windows: new Map(),
      pending: pendingWork(),
    };
  }

  function rememberPanel(id, node, pending = journal.pending) {
    addToIndex(journal.oldIds, id, node);
    pending.panelIds.add(id);
  }

  function remember(node, field, previous) {
    let fields = journal.changes.get(node);
    if (!fields) journal.changes.set(node, fields = new Map());
    let records = fields.get(field);
    if (!records) fields.set(field, records = []);
    records.push({ revision, previous });
  }

  function noteMutations(records) {
    let lastTarget = null;
    let lastTargetPruned = false;
    for (const record of records) {
      revision++;
      if (record.type === 'childList') {
        if (record.target !== lastTarget) {
          lastTarget = record.target;
          lastTargetPruned = record.target?.nodeType === 1 &&
            Boolean(dom.shouldPrune ? dom.shouldPrune(record.target) : dom.isProtected?.(record.target));
        }
        if (lastTargetPruned) {
          let needsTracking = false;
          for (const node of record.removedNodes) {
            if (node.nodeType === 1 && (triggers.has(node) || indexedPanels.has(node) || (node.id && panelsById.has(node.id)))) {
              needsTracking = true;
              break;
            }
          }
          if (!needsTracking) {
            for (const node of record.addedNodes) {
              if (node.nodeType === 1 && (triggers.has(node) || indexedPanels.has(node) || (node.id && panelsById.has(node.id)))) {
                needsTracking = true;
                break;
              }
            }
          }
          if (!needsTracking) continue;
        }
        beginRecord();
        let previous = record.previousSibling;
        for (const node of record.removedNodes) {
          if (node.nodeType === 1) {
            remember(node, 'parent', record.target);
            journal.pending.removedRoots.add(node);
          }
          remember(node, 'previous', previous);
          previous = node;
        }
        for (const node of record.addedNodes) {
          if (node.nodeType === 1) remember(node, 'parent', null);
          remember(node, 'previous', null);
        }
        // The following sibling used to follow the last removed node.
        if (record.nextSibling) remember(record.nextSibling, 'previous', previous);
      } else if (record.attributeName === 'id') {
        beginRecord();
        remember(record.target, 'id', record.oldValue);
        if (record.oldValue) rememberPanel(record.oldValue, record.target);
      } else if ((record.attributeName === 'aria-controls' || record.attributeName === 'aria-expanded') &&
                 dom.statusCandidate(record.target)) {
        beginRecord();
        remember(record.target, record.attributeName, record.oldValue);
        journal.pending.buttons.add(record.target);
      }
    }
  }

  function protect(panel) {
    if (protectedPanels.has(panel)) return;
    protectedPanels.add(panel);
    onProtect(panel);
  }

  function indexPanel(node) {
    const id = connected(node) ? node.id : '';
    const old = indexedPanels.get(node);
    if (id && old?.id === id) return old;
    if (old) {
      indexedPanels.delete(node);
      removeFromIndex(panelsById, old.id, node);
      old.link.forget();
      if (journal) rememberPanel(old.id, node);
    }
    if (!id) return;
    const state = { id, link: null };
    state.link = index(node, () => {
      if (indexPanel(node) === state) state.link.refresh();
    });
    indexedPanels.set(node, state);
    addToIndex(panelsById, id, node);
    if (journal?.windows.has(id)) journal.pending.panelIds.add(id);
    return state;
  }

  function forget(button, state) {
    if (!state) return;
    triggers.delete(button);
    state.link.forget();
    for (const id of state.ids) removeFromIndex(ownersById, id, button);
    journal?.pending.buttons.add(button);
  }

  function validTrigger(button) {
    if (!connected(button) || dom.statusButton(button) !== button || dom.isProtected(button)) return false;
    for (let node = button; node; node = node.parentElement) {
      if (protectedPanels.has(node)) return false;
    }
    return true;
  }

  function controlIds(controls) {
    return new Set(controls.trim().split(/\s+/).filter(Boolean));
  }

  function syncTrigger(button) {
    const old = triggers.get(button);
    const controls = button.getAttribute('aria-controls')?.trim();
    if (!controls || !validTrigger(button)) {
      forget(button, old);
      return;
    }
    if (old?.controls === controls) return old;
    forget(button, old);
    const state = { controls, ids: controlIds(controls), link: null };
    state.link = index(button, () => {
      if (syncTrigger(button) === state) state.link.refresh();
    });
    triggers.set(button, state);
    for (const id of state.ids) {
      addToIndex(ownersById, id, button);
      const panel = document.getElementById(id);
      if (connected(panel)) protect(panel);
    }
    return state;
  }

  function inspectPanel(node) {
    if (protectedPanels.has(node)) return true;
    const owners = node.id && ownersById.get(node.id);
    if (!owners) return false;
    for (const trigger of owners) {
      if (trigger.getAttribute('aria-controls')?.trim() === triggers.get(trigger)?.controls && validTrigger(trigger)) {
        protect(node);
        return true;
      }
    }
    return false;
  }

  function blocks(element) {
    for (let node = element; node; node = node.parentElement) {
      if (inspectPanel(node)) return true;
    }
    return false;
  }

  function snapshot(at) {
    let start = journal.start;
    function value(node, field, current) {
      const changes = journal.changes.get(node)?.get(field);
      let i = (changes?.length ?? 0) - 1;
      while (i >= 0 && changes[i].revision > at) current = changes[i--].previous;
      if (i >= 0) start = Math.max(start, changes[i].revision);
      return current;
    }
    function parent(node) {
      const ancestor = value(node, 'parent', node.parentNode);
      return ancestor?.nodeType === 1 ? ancestor : null;
    }
    function inBody(startNode, reject) {
      const visited = new Set();
      for (let node = startNode; node && !visited.has(node); node = parent(node)) {
        if (reject?.(node)) return false;
        if (node === document.body) return true;
        visited.add(node);
      }
      return false;
    }
    function firstElement(node) {
      const visited = new Set();
      let sibling = value(node, 'previous', node.previousSibling);
      while (sibling && !visited.has(sibling)) {
        if (sibling.nodeType === 1) return false;
        visited.add(sibling);
        sibling = value(sibling, 'previous', sibling.previousSibling);
      }
      return !sibling;
    }
    return {
      parent, inBody, firstElement,
      attr: (node, name) => value(node, name, node.getAttribute(name)),
      get start() { return start; },
    };
  }

  function* collectRemovedNodes(pending) {
    const seen = new WeakSet();
    for (const root of pending.removedRoots) {
      // This is a budgeted pass over removed subtrees only, including DOM that
      // was removed before the normal mount cursor first reached it.
      const iterator = document.createNodeIterator(root, NodeFilter.SHOW_ELEMENT);
      for (let node = iterator.nextNode(); node; node = iterator.nextNode()) {
        if (!seen.has(node)) {
          seen.add(node);
          if (dom.statusCandidate(node) && (node.hasAttribute('aria-controls') ||
              journal.changes.get(node)?.has('aria-controls'))) pending.buttons.add(node);
          if (node.id) rememberPanel(node.id, node, pending);
        }
        yield;
      }
    }
  }

  function recordWindow(id, start, end, pending) {
    let windows = journal.windows.get(id);
    if (!windows) journal.windows.set(id, windows = []);
    const last = windows[windows.length - 1];
    if (last && start <= last.end && last.start <= end) {
      last.start = Math.min(start, last.start);
      last.end = Math.max(end, last.end);
    } else {
      windows.push({ start, end });
    }
    pending.panelIds.add(id);
  }

  function* occupiedId(panel, id, { start, end }) {
    for (let at = end; at >= start;) {
      const view = snapshot(at);
      if (view.attr(panel, 'id') === id && view.inBody(panel)) return true;
      at = view.start - 1;
      yield;
    }
    return false;
  }

  function* checkPanels(id) {
    const windows = journal.windows.get(id);
    if (!windows) return;
    const candidates = new Set(panelsById.get(id));
    for (const node of journal.oldIds.get(id) ?? []) candidates.add(node);
    const current = document.getElementById(id);
    if (current) candidates.add(current);
    for (const panel of candidates) {
      if (!protectedPanels.has(panel)) {
        for (const range of windows) {
          if (yield* occupiedId(panel, id, range)) {
            protect(panel);
            break;
          }
        }
      }
      yield;
    }
  }

  function* restoreOwnership(pending, through) {
    yield* collectRemovedNodes(pending);
    // A panel can lose its ID while the trigger itself stays unchanged.
    for (const id of pending.panelIds) {
      for (const button of ownersById.get(id) ?? []) {
        pending.buttons.add(button);
        yield;
      }
      yield;
    }
    for (const button of pending.buttons) {
      for (let at = through; at >= journal.start;) {
        const view = snapshot(at);
        const controls = view.attr(button, 'aria-controls');
        const ownsPanel = controls && view.attr(button, 'aria-expanded') !== null &&
          view.inBody(button, (node) => protectedPanels.has(node) || dom.isProtectedRoot(node)) &&
          dom.ownsStatusHeader(button, view.parent, view.firstElement);
        if (ownsPanel) {
          // Match concrete elements for the interval the control actually held
          // this ID. A later element recycling the same string stays eligible.
          for (const id of controlIds(controls)) recordWindow(id, view.start, at, pending);
        }
        at = view.start - 1;
        yield;
      }
    }
    for (const id of pending.panelIds) {
      yield* checkPanels(id);
      yield;
    }
  }

  function hasPendingWork({ removedRoots, buttons, panelIds }) {
    return removedRoots.size || buttons.size || panelIds.size;
  }

  function settleStep() {
    if (!settlement && hasPendingWork(journal.pending)) {
      // Finish this pass even if another delivery arrives between frames.
      // New records are added to the journal for the next pass.
      const pending = journal.pending;
      journal.pending = pendingWork();
      settlement = restoreOwnership(pending, revision);
    }
    if (settlement && !settlement.next().done) return;
    settlement = null;
    if (!hasPendingWork(journal.pending)) journal = null;
  }

  return {
    noteMutations, syncTrigger, indexPanel, inspectPanel, blocks, settleStep,
    hasPending: () => journal !== null,
    hasTrigger: (node) => triggers.has(node),
  };
}

function createMountWalk(root, shouldPrune) {
  const visited = new WeakSet();
  const parents = new WeakMap();
  const stack = [];

  function visit(node) {
    if (visited.has(node)) return null;
    visited.add(node);
    if (shouldPrune(node)) return null;
    if (node.firstChild) {
      const frame = { parent: node, next: node.firstChild };
      parents.set(node, frame);
      stack.push(frame);
    }
    return node;
  }

  function* traverse() {
    const alive = () => root.isConnected && root.ownerDocument === document;
    if (!alive()) return;
    yield visit(root);
    while (stack.length && alive()) {
      const frame = stack[stack.length - 1];
      if (!frame.next || !root.contains(frame.parent)) {
        parents.delete(frame.parent);
        stack.pop();
        yield null;
        continue;
      }
      // The cursor is anchored to a parent, so dropping the last visited node
      // across frames cannot discard its siblings or any ancestor's siblings.
      const node = frame.next.parentNode === frame.parent ? frame.next : frame.parent.firstChild;
      frame.next = node?.nextSibling;
      yield node ? visit(node) : null;
    }
  }

  const iterator = traverse();
  return {
    next: () => iterator.next(),
    childrenChanged(record) {
      const frame = parents.get(record.target);
      if (!frame?.next) return;
      for (const removed of record.removedNodes) {
        if (removed === frame.next) {
          frame.next = record.nextSibling;
          return;
        }
      }
    },
  };
}

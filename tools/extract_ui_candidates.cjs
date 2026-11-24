"use strict";

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const TK_EOF = 0;
const TK_ID = 1;
const TK_STR = 2;
const TK_NUM = 3;
const TK_PUNC = 4;
const TK_OTHER = 5;

const REGEX_PREFIX_KEYWORDS = new Set([
  "return",
  "case",
  "throw",
  "typeof",
  "void",
  "delete",
  "in",
  "of",
  "instanceof",
  "new",
  "await",
  "yield",
  "else",
  "do",
]);

const REGEX_PREFIX_PUNC = new Set([
  "(",
  "[",
  "{",
  ",",
  ";",
  ":",
  "?",
  "=",
  "!",
  "&",
  "|",
  "^",
  "~",
  "+",
  "-",
  "*",
  "**",
  "%",
  "<",
  ">",
  "<<",
  ">>",
  ">>>",
  "&&",
  "||",
  "??",
  "=>",
  "==",
  "===",
  "!=",
  "!==",
  "<=",
  ">=",
  "+=",
  "-=",
  "*=",
  "/=",
  "%=",
  "**=",
  "&&=",
  "||=",
  "??=",
  "<<=",
  ">>=",
  ">>>=",
]);

const COMPARE_OPS = new Set(["==", "===", "!=", "!=="]);
const TESTID_KEYS = new Set(["data-testid", "dataTestId", "testId"]);
const DISPLAY_ATTR_KEYS = new Set([
  "aria-label",
  "title",
  "placeholder",
  "data-tooltip",
  "data-title",
]);
const COMPONENT_TEXT_KEYS = new Set([
  "label",
  "tooltip",
  "description",
  "heading",
  "subtitle",
  "emptyMessage",
  "emptyText",
  "confirmLabel",
  "cancelLabel",
]);

const SKIP_SINGLE_WORDS = new Set([
  "http",
  "https",
  "true",
  "false",
  "null",
  "undefined",
  "NaN",
  "Infinity",
  "Object",
  "Array",
  "String",
  "Number",
  "Boolean",
  "Function",
  "Promise",
  "Symbol",
  "Map",
  "Set",
  "Error",
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
  "HEAD",
  "OPTIONS",
  "UTF-8",
  "utf-8",
  "JSON",
]);

const TAILWIND_PREFIX_RE =
  /^(flex|grid|items-|justify-|gap-|space-[xy]-|text-|bg-|border-|px-|py-|pt-|pb-|pl-|pr-|mx-|my-|mt-|mb-|ml-|mr-|p-\d|m-\d|w-|h-|min-|max-|overflow-|rounded|hover:|focus:|active:|disabled:|dark:|group-|peer-|cursor-|select-|pointer-events-|transition|duration-|shadow|ring-|font-|leading-|tracking-|whitespace-|truncate|line-clamp-|z-|inset-|top-|right-|bottom-|left-|col-|row-)/;

function isIdentStart(code) {
  return (
    (code >= 65 && code <= 90) ||
    (code >= 97 && code <= 122) ||
    code === 95 ||
    code === 36
  );
}

function isIdentPart(code) {
  return isIdentStart(code) || (code >= 48 && code <= 57);
}

function decodeStringLiteral(src, startQuotePos) {
  const quote = src.charCodeAt(startQuotePos);
  const len = src.length;
  let i = startQuotePos + 1;
  let chunkStart = i;
  let out = "";

  while (i < len) {
    const ch = src.charCodeAt(i);
    if (ch === quote) {
      return {
        value: out.length === 0 ? src.slice(chunkStart, i) : out + src.slice(chunkStart, i),
        nextPos: i + 1,
      };
    }
    if (ch === 92) {
      out += src.slice(chunkStart, i);
      i++;
      if (i >= len) break;
      const esc = src.charCodeAt(i);
      if (esc === 110) out += "\n";
      else if (esc === 114) out += "\r";
      else if (esc === 116) out += "\t";
      else if (esc === 98) out += "\b";
      else if (esc === 102) out += "\f";
      else if (esc === 118) out += "\v";
      else if (esc === 48 && !(src.charCodeAt(i + 1) >= 48 && src.charCodeAt(i + 1) <= 55)) {
        out += "\0";
      } else if (esc === 120 && i + 2 < len) {
        const hex = src.slice(i + 1, i + 3);
        if (/^[0-9a-fA-F]{2}$/.test(hex)) {
          out += String.fromCharCode(parseInt(hex, 16));
          i += 2;
        } else {
          out += "x";
        }
      } else if (esc === 117) {
        if (src.charCodeAt(i + 1) === 123) {
          const closeBrace = src.indexOf("}", i + 2);
          if (closeBrace !== -1) {
            const hex = src.slice(i + 2, closeBrace);
            if (/^[0-9a-fA-F]+$/.test(hex)) {
              const cp = parseInt(hex, 16);
              if (cp <= 0x10ffff) {
                out += String.fromCodePoint(cp);
              }
              i = closeBrace;
            }
          }
        } else if (i + 4 < len) {
          const hex = src.slice(i + 1, i + 5);
          if (/^[0-9a-fA-F]{4}$/.test(hex)) {
            out += String.fromCharCode(parseInt(hex, 16));
            i += 4;
          } else {
            out += "u";
          }
        }
      } else if (esc === 13) {
        if (src.charCodeAt(i + 1) === 10) i++;
      } else if (esc === 10 || esc === 0x2028 || esc === 0x2029) {
        // line continuation
      } else {
        out += src[i];
      }
      i++;
      chunkStart = i;
      continue;
    }
    if (ch === 10 || ch === 13) {
      break;
    }
    i++;
  }
  return { value: out + src.slice(chunkStart, i), nextPos: Math.min(i + 1, len) };
}

class JsLexer {
  constructor(src) {
    this.src = src;
    this.len = src.length;
    this.pos = 0;
    this.regexAllowed = true;
    this.parenKeywordStack = [];
    this.pendingControlHeader = false;
    this.templateStack = [];
    this.lookahead = null;
  }

  _skipRegex() {
    const src = this.src;
    const len = this.len;
    let i = this.pos + 1;
    let inClass = false;
    while (i < len) {
      const ch = src.charCodeAt(i);
      if (ch === 92) {
        i += 2;
        continue;
      }
      if (ch === 91) {
        inClass = true;
      } else if (ch === 93 && inClass) {
        inClass = false;
      } else if (ch === 47 && !inClass) {
        i++;
        while (i < len && isIdentPart(src.charCodeAt(i))) i++;
        this.pos = i;
        return;
      } else if (ch === 10 || ch === 13) {
        break;
      }
      i++;
    }
    this.pos = Math.min(i, len);
  }

  _scanTemplateBody(startPos) {
    const src = this.src;
    const len = this.len;
    let i = startPos;
    while (i < len) {
      const ch = src.charCodeAt(i);
      if (ch === 92) {
        i += 2;
        continue;
      }
      if (ch === 36 && src.charCodeAt(i + 1) === 123) {
        this.templateStack.push({ braceDepth: 1 });
        this.pos = i + 2;
        this.regexAllowed = true;
        return { type: TK_PUNC, value: "${" };
      }
      if (ch === 96) {
        this.pos = i + 1;
        this.regexAllowed = false;
        return { type: TK_OTHER, value: "`" };
      }
      i++;
    }
    this.pos = len;
    this.regexAllowed = false;
    return { type: TK_EOF, value: "" };
  }

  _readMultiPunc() {
    const src = this.src;
    const pos = this.pos;
    const c1 = src[pos];
    const c2 = src.slice(pos, pos + 2);
    const c3 = src.slice(pos, pos + 3);
    const c4 = src.slice(pos, pos + 4);

    if (c4 === ">>>=") return c4;
    if (
      c3 === "===" ||
      c3 === "!==" ||
      c3 === "..." ||
      c3 === ">>>" ||
      c3 === "**=" ||
      c3 === "&&=" ||
      c3 === "||=" ||
      c3 === "??=" ||
      c3 === "<<=" ||
      c3 === ">>="
    ) {
      return c3;
    }
    if (c2 === "?." && !(src.charCodeAt(pos + 2) >= 48 && src.charCodeAt(pos + 2) <= 57)) {
      return c2;
    }
    if (
      c2 === "&&" ||
      c2 === "||" ||
      c2 === "??" ||
      c2 === "=>" ||
      c2 === "==" ||
      c2 === "!=" ||
      c2 === "<=" ||
      c2 === ">=" ||
      c2 === "++" ||
      c2 === "--" ||
      c2 === "**" ||
      c2 === "<<" ||
      c2 === ">>" ||
      c2 === "+=" ||
      c2 === "-=" ||
      c2 === "*=" ||
      c2 === "/=" ||
      c2 === "%="
    ) {
      return c2;
    }
    return c1;
  }

  _readNext() {
    const src = this.src;
    const len = this.len;

    while (this.pos < len) {
      const ch = src.charCodeAt(this.pos);

      if (ch === 32 || ch === 9 || ch === 10 || ch === 13 || ch === 12 || ch === 11 || ch === 0xa0) {
        this.pos++;
        continue;
      }

      if (ch === 47) {
        const nextCh = src.charCodeAt(this.pos + 1);
        if (nextCh === 47) {
          this.pos += 2;
          while (this.pos < len) {
            const c = src.charCodeAt(this.pos);
            this.pos++;
            if (c === 10 || c === 13) break;
          }
          continue;
        }
        if (nextCh === 42) {
          const endIdx = src.indexOf("*/", this.pos + 2);
          this.pos = endIdx === -1 ? len : endIdx + 2;
          continue;
        }
        if (this.regexAllowed) {
          this._skipRegex();
          this.regexAllowed = false;
          this.pendingControlHeader = false;
          return { type: TK_OTHER, value: "/re/" };
        }
      }

      if (ch === 34 || ch === 39) {
        const { value, nextPos } = decodeStringLiteral(src, this.pos);
        this.pos = nextPos;
        this.regexAllowed = false;
        this.pendingControlHeader = false;
        return { type: TK_STR, value };
      }

      if (ch === 96) {
        this.pendingControlHeader = false;
        return this._scanTemplateBody(this.pos + 1);
      }

      if (isIdentStart(ch)) {
        const start = this.pos;
        this.pos++;
        while (this.pos < len && isIdentPart(src.charCodeAt(this.pos))) {
          this.pos++;
        }
        const word = src.slice(start, this.pos);
        this.pendingControlHeader = word === "if" || word === "while" || word === "for" || word === "with";
        this.regexAllowed = REGEX_PREFIX_KEYWORDS.has(word);
        return { type: TK_ID, value: word };
      }

      if (
        (ch >= 48 && ch <= 57) ||
        (ch === 46 && src.charCodeAt(this.pos + 1) >= 48 && src.charCodeAt(this.pos + 1) <= 57)
      ) {
        const start = this.pos;
        this.pos++;
        while (this.pos < len) {
          const c = src.charCodeAt(this.pos);
          if (isIdentPart(c) || c === 46) {
            this.pos++;
          } else if ((c === 43 || c === 45) && (src.charCodeAt(this.pos - 1) === 101 || src.charCodeAt(this.pos - 1) === 69)) {
            this.pos++;
          } else {
            break;
          }
        }
        this.regexAllowed = false;
        this.pendingControlHeader = false;
        return { type: TK_NUM, value: src.slice(start, this.pos) };
      }

      const punc = this._readMultiPunc();
      this.pos += punc.length;

      if (punc === "(") {
        this.parenKeywordStack.push(this.pendingControlHeader);
        this.pendingControlHeader = false;
      } else if (punc === ")") {
        const wasCtrl = this.parenKeywordStack.length > 0 ? this.parenKeywordStack.pop() : false;
        this.pendingControlHeader = false;
        this.regexAllowed = Boolean(wasCtrl);
        return { type: TK_PUNC, value: punc };
      } else {
        this.pendingControlHeader = false;
      }

      if (this.templateStack.length > 0) {
        const top = this.templateStack[this.templateStack.length - 1];
        if (punc === "{") {
          top.braceDepth++;
        } else if (punc === "}") {
          top.braceDepth--;
          if (top.braceDepth === 0) {
            this.templateStack.pop();
            return this._scanTemplateBody(this.pos);
          }
        }
      }

      this.regexAllowed = punc === "}" || REGEX_PREFIX_PUNC.has(punc);
      return { type: TK_PUNC, value: punc };
    }

    return { type: TK_EOF, value: "" };
  }

  peek() {
    if (this.lookahead === null) {
      this.lookahead = this._readNext();
    }
    return this.lookahead;
  }

  next() {
    if (this.lookahead !== null) {
      const tok = this.lookahead;
      this.lookahead = null;
      return tok;
    }
    return this._readNext();
  }
}

function isUiCandidate(raw) {
  if (typeof raw !== "string") return false;
  const text = raw.replace(/\u00a0/g, " ").trim();
  if (text.length < 2 || text.length > 180) return false;
  if (!/[A-Za-z]/.test(text)) return false;
  if (SKIP_SINGLE_WORDS.has(text)) return false;
  if (/^(\/|\.\/|\.\.\/|#|@|--|data:|blob:|mailto:|file:\/\/|https?:\/\/|vscode:|antigravity:)/i.test(text)) {
    return false;
  }
  if (text.includes("://") || text.includes("\\")) return false;
  if (/^M[\d.\s,LlHhVvCcSsQqTtAaZz-]+$/.test(text)) return false;
  if (/^(application|text|image|audio|video|font)\/[a-z0-9.+-]+$/i.test(text)) return false;
  if (/^#[0-9a-fA-F]{3,8}$/.test(text)) return false;

  if (!/\s/.test(text)) {
    if (/^[a-z0-9._:/-]+$/.test(text)) return false;
    if (/^[a-z]+[A-Z]/.test(text)) return false;
    if (/^[A-Z][a-z]+([A-Z][a-z]+){2,}$/.test(text)) return false;
    if (/[_{}\[\]<>]/.test(text)) return false;
    if (/^[A-Z0-9_]+$/.test(text) && text.length > 4) return false;
    if (/^\d+(px|rem|em|vh|vw|ms|s|%)$/i.test(text)) return false;
    return /^[A-Z]/.test(text);
  }

  const tokens = text.split(/\s+/);
  if (tokens.length >= 2) {
    const cssLikeCount = tokens.filter(
      (t) => TAILWIND_PREFIX_RE.test(t) || (/^[a-z0-9!.:/\[\]-]+$/.test(t) && /[-:\[\]/]/.test(t))
    ).length;
    if (cssLikeCount >= 2 && cssLikeCount >= tokens.length - 1) return false;
  }
  if (/^[\s{}\[\]()<>:;,.+=/*|\\`"'~^%$&!@#?-]*$/.test(text)) return false;
  return true;
}

function loadLocalizationEngine(rendererDir) {
  const ctx = vm.createContext({
    Map,
    Set,
    Object,
    Array,
    String,
    Number,
    RegExp,
    JSON,
    Intl,
    Math,
  });
  for (const name of ["catalog.js", "formatters.js"]) {
    const code = fs.readFileSync(path.join(rendererDir, name), "utf8");
    vm.runInContext(code, ctx);
  }
  vm.runInContext("this.__exported = { catalog, formats };", ctx);
  return ctx.__exported;
}

function classifyCandidate(text, engine) {
  const { catalog, formats } = engine;
  if (catalog.dictionaryMap.has(text) || catalog.dictionaryMap.has(text.trim())) {
    return "matched_exact";
  }
  const fns = [
    (s) =>
      formats.shell(s, {
        allowRelTime: true,
        allowBareRelTime: false,
        allowCoreWords: true,
        allowExtraLabels: true,
      }),
    (s) => formats.status(s),
    (s) => formats.composer(s),
    (s) => formats.permissionTitle(s),
    (s) => formats.permissionButton(s),
    (s) => formats.artifactAction(s),
    (s) => formats.fileAction(s),
    (s) => formats.homeGreeting(s),
    (s) => formats.feedback(s),
  ];
  for (const fn of fns) {
    try {
      const out = fn(text);
      if (typeof out === "string" && out !== text) {
        return "matched_formatter";
      }
    } catch (_) {
      // Ignore formatter edge errors
    }
  }
  return "unmatched";
}

function extractCandidates(bundleSource, rendererDir) {
  const engine = loadLocalizationEngine(rendererDir);
  const testids = new Map();
  const candidates = new Map();

  function recordTestId(id, kind, role) {
    if (!id || typeof id !== "string") return;
    let entry = testids.get(id);
    if (!entry) {
      entry = { count: 0, kinds: new Set(), roles: new Set() };
      testids.set(id, entry);
    }
    entry.count++;
    if (kind) entry.kinds.add(kind);
    if (role && typeof role === "string") entry.roles.add(role);
  }

  function recordCandidate(rawText, field, contextTestId) {
    if (!isUiCandidate(rawText)) return;
    const text = rawText.replace(/\u00a0/g, " ").trim();
    let entry = candidates.get(text);
    if (!entry) {
      entry = {
        text,
        count: 0,
        fields: new Set(),
        contexts: new Map(),
      };
      candidates.set(text, entry);
    }
    entry.count++;
    entry.fields.add(field);
    const ctxKey = contextTestId || "<root>";
    entry.contexts.set(ctxKey, (entry.contexts.get(ctxKey) || 0) + 1);
  }

  const lexer = new JsLexer(bundleSource);

  function parseObjectLiteral(enclosingTestId, captureDisplayProps) {
    lexer.next(); // consume '{'
    let depth = 1;
    let ownTestId = null;
    let roleVal = null;
    const foundTestIds = [];
    const bufferedProps = [];

    let expectingKey = true;
    let currentKey = null;
    let expectValueForKey = false;
    let prev2 = null;
    let prev1 = null;

    while (depth > 0) {
      const tok = lexer.peek();
      if (tok.type === TK_EOF) break;

      if (depth === 1) {
        if (tok.type === TK_PUNC && tok.value === "}") {
          lexer.next();
          depth--;
          break;
        }
        if (tok.type === TK_PUNC && tok.value === ",") {
          lexer.next();
          expectingKey = true;
          currentKey = null;
          expectValueForKey = false;
          prev2 = prev1;
          prev1 = tok;
          continue;
        }
        if (expectingKey) {
          lexer.next();
          if (tok.type === TK_ID || tok.type === TK_STR) {
            currentKey = tok.value;
            if (lexer.peek().type === TK_PUNC && lexer.peek().value === ":") {
              const colon = lexer.next();
              expectingKey = false;
              expectValueForKey = true;
              prev2 = tok;
              prev1 = colon;
              continue;
            }
          }
          expectingKey = false;
          expectValueForKey = false;
          prev2 = prev1;
          prev1 = tok;
          continue;
        }
        if (expectValueForKey) {
          expectValueForKey = false;
          if (tok.type === TK_STR) {
            const valTok = lexer.next();
            const after = lexer.peek();
            if (after.type === TK_PUNC && (after.value === "," || after.value === "}")) {
              if (TESTID_KEYS.has(currentKey)) {
                foundTestIds.push({
                  id: valTok.value,
                  kind: currentKey === "data-testid" ? "dom" : "component",
                });
                if (!ownTestId) ownTestId = valTok.value;
              } else if (currentKey === "role") {
                roleVal = valTok.value;
              } else if (captureDisplayProps) {
                if (DISPLAY_ATTR_KEYS.has(currentKey)) {
                  bufferedProps.push({ text: valTok.value, field: `attr:${currentKey}` });
                } else if (COMPONENT_TEXT_KEYS.has(currentKey)) {
                  bufferedProps.push({ text: valTok.value, field: `prop:${currentKey}` });
                }
              }
            }
            prev2 = prev1;
            prev1 = valTok;
            continue;
          }
        }
      }

      if (tok.type === TK_PUNC && tok.value === "{") {
        parseObjectLiteral(ownTestId || enclosingTestId, false);
        prev2 = { type: TK_PUNC, value: "}" };
        prev1 = prev2;
        continue;
      }

      if (
        tok.type === TK_PUNC &&
        tok.value === "(" &&
        prev1 &&
        prev1.type === TK_ID &&
        prev1.value === "createElement" &&
        prev2 &&
        prev2.type === TK_PUNC &&
        prev2.value === "."
      ) {
        parseCreateElementCall(ownTestId || enclosingTestId);
        prev2 = { type: TK_PUNC, value: ")" };
        prev1 = prev2;
        continue;
      }

      lexer.next();
      if (tok.type === TK_PUNC) {
        if (tok.value === "(" || tok.value === "[") depth++;
        else if (tok.value === ")" || tok.value === "]") depth = Math.max(1, depth - 1);
      }
      prev2 = prev1;
      prev1 = tok;
    }

    const effectiveCtx = ownTestId || enclosingTestId;
    for (const item of foundTestIds) {
      recordTestId(item.id, item.kind, roleVal);
    }
    for (const item of bufferedProps) {
      recordCandidate(item.text, item.field, effectiveCtx);
    }
    return effectiveCtx;
  }

  function parseCreateElementCall(enclosingTestId) {
    lexer.next(); // consume '('
    let argIndex = 0;
    let callDepth = 0;
    let atArgStart = true;
    let activeTestId = enclosingTestId;
    let prev2 = null;
    let prev1 = { type: TK_PUNC, value: "(" };

    while (true) {
      const tok = lexer.peek();
      if (tok.type === TK_EOF) break;

      if (callDepth === 0) {
        if (tok.type === TK_PUNC && tok.value === ")") {
          lexer.next();
          break;
        }
        if (tok.type === TK_PUNC && tok.value === ",") {
          lexer.next();
          argIndex++;
          atArgStart = true;
          prev2 = prev1;
          prev1 = tok;
          continue;
        }
      }

      if (tok.type === TK_PUNC && tok.value === "{") {
        const captureProps = argIndex === 1 && callDepth === 0;
        const nextCtx = parseObjectLiteral(activeTestId, captureProps);
        if (captureProps && nextCtx) {
          activeTestId = nextCtx;
        }
        atArgStart = false;
        prev2 = { type: TK_PUNC, value: "}" };
        prev1 = prev2;
        continue;
      }

      if (
        tok.type === TK_PUNC &&
        tok.value === "(" &&
        prev1 &&
        prev1.type === TK_ID &&
        prev1.value === "createElement" &&
        prev2 &&
        prev2.type === TK_PUNC &&
        prev2.value === "."
      ) {
        parseCreateElementCall(activeTestId);
        atArgStart = false;
        prev2 = { type: TK_PUNC, value: ")" };
        prev1 = prev2;
        continue;
      }

      lexer.next();
      atArgStart = false;

      if (argIndex >= 2 && callDepth === 0 && tok.type === TK_STR) {
        const nextTok = lexer.peek();
        const prevIsCompare =
          (prev1 && prev1.type === TK_PUNC && COMPARE_OPS.has(prev1.value)) ||
          (prev1 && prev1.type === TK_ID && prev1.value === "case");
        const nextIsCompareOrTernaryTest =
          nextTok.type === TK_PUNC &&
          (COMPARE_OPS.has(nextTok.value) || nextTok.value === "?" || nextTok.value === ".");
        if (!prevIsCompare && !nextIsCompareOrTernaryTest) {
          recordCandidate(tok.value, "text", activeTestId);
        }
      }

      if (tok.type === TK_PUNC) {
        if (tok.value === "(") {
          callDepth++;
        } else if (tok.value === ")") {
          callDepth = Math.max(0, callDepth - 1);
        }
      }
      prev2 = prev1;
      prev1 = tok;
    }
  }

  let prev2 = null;
  let prev1 = null;
  while (true) {
    const tok = lexer.peek();
    if (tok.type === TK_EOF) break;
    if (tok.type === TK_PUNC && tok.value === "{") {
      parseObjectLiteral(null, false);
      prev2 = { type: TK_PUNC, value: "}" };
      prev1 = prev2;
      continue;
    }
    if (
      tok.type === TK_PUNC &&
      tok.value === "(" &&
      prev1 &&
      prev1.type === TK_ID &&
      prev1.value === "createElement" &&
      prev2 &&
      prev2.type === TK_PUNC &&
      prev2.value === "."
    ) {
      parseCreateElementCall(null);
      prev2 = { type: TK_PUNC, value: ")" };
      prev1 = prev2;
      continue;
    }
    lexer.next();
    prev2 = prev1;
    prev1 = tok;
  }

  let matchedExactCount = 0;
  let matchedFormatterCount = 0;
  let unmatchedCount = 0;
  const unmatchedItems = [];
  const matchedItems = [];

  for (const entry of candidates.values()) {
    const status = classifyCandidate(entry.text, engine);
    const serialized = {
      text: entry.text,
      count: entry.count,
      fields: Array.from(entry.fields).sort(),
      contexts: Object.fromEntries(
        Array.from(entry.contexts.entries()).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      ),
    };
    if (status === "matched_exact") {
      matchedExactCount++;
      matchedItems.push({ ...serialized, status });
    } else if (status === "matched_formatter") {
      matchedFormatterCount++;
      matchedItems.push({ ...serialized, status });
    } else {
      unmatchedCount++;
      unmatchedItems.push(serialized);
    }
  }

  unmatchedItems.sort((a, b) => b.count - a.count || a.text.localeCompare(b.text));
  matchedItems.sort((a, b) => b.count - a.count || a.text.localeCompare(b.text));

  let domUnique = 0;
  let componentUnique = 0;
  const testidMap = {};
  for (const [id, info] of Array.from(testids.entries()).sort((a, b) => a[0].localeCompare(b[0]))) {
    const kinds = Array.from(info.kinds).sort();
    if (kinds.includes("dom")) domUnique++;
    if (kinds.includes("component")) componentUnique++;
    testidMap[id] = {
      count: info.count,
      kinds,
      roles: Array.from(info.roles).sort(),
    };
  }

  return {
    catalog_stats: {
      dictionary: engine.catalog.dictionaryMap.size,
      core_words: engine.catalog.coreWordsMap.size,
      extra_labels: engine.catalog.extraLabelsMap.size,
    },
    testid_stats: {
      total_unique: testids.size,
      dom_unique: domUnique,
      component_unique: componentUnique,
    },
    testids: testidMap,
    candidates: {
      total_unique: candidates.size,
      matched_exact: matchedExactCount,
      matched_formatter: matchedFormatterCount,
      unmatched_count: unmatchedCount,
      items: unmatchedItems,
      matched_items: matchedItems,
    },
  };
}

if (require.main === module) {
  const bundlePath = process.argv[2];
  const rendererDir = process.argv[3];
  if (!bundlePath || !rendererDir) {
    console.error("Usage: node extract_ui_candidates.cjs <bundleJsPath> <rendererDir>");
    process.exit(2);
  }
  const src = fs.readFileSync(bundlePath, "utf8");
  const result = extractCandidates(src, rendererDir);
  process.stdout.write(JSON.stringify(result));
}

module.exports = {
  JsLexer,
  extractCandidates,
  isUiCandidate,
};

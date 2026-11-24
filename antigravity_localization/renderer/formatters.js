const formats = (() => {
  const { dictionaryMap, coreWordsMap, extraLabelsMap } = catalog;

  const CHAT_ACTION_BUTTON_MAP = new Map([
    ["Review", "审阅"],
    ["Accept", "接受"],
    ["Accept all", "全部接受"],
    ["Accept All", "全部接受"],
    ["Reject", "拒绝"],
    ["Reject all", "全部拒绝"],
    ["Reject All", "全部拒绝"],
    ["Discard", "放弃"],
    ["Keep", "保留"],
    ["Apply", "应用"],
    ["View diff", "查看差异"],
    ["Open diff", "打开差异"],
    ["Show diff", "显示差异"],
    ["Hide diff", "隐藏差异"],
    ["Expand", "展开"],
    ["Collapse", "折叠"],
    ["Show more", "展开更多"],
    ["Show less", "收起"],
    ["Open", "打开"],
    ["Open file", "打开文件"],
    ["View", "查看"],
    ["Download", "下载"],
    ["Copy", "复制"],
    ["Copied", "已复制"],
    ["Copied!", "已复制！"],
    ["Copy code", "复制代码"],
    ["Copy message", "复制消息"],
    ["Copy response", "复制回复"],
    ["Good response", "好的回答"],
    ["Bad response", "差的回答"],
    ["Thumbs up", "点赞"],
    ["Thumbs down", "点踩"],
    ["Allow", "允许"],
    ["Deny", "拒绝"],
    ["Run", "运行"],
    ["Always allow", "始终允许"],
    ["Allow once", "仅本次允许"],
    ["Yes, allow this time", "是，仅本次允许"],
    ["Yes, and always allow in this conversation", "是，在本次对话中始终允许"],
    ["Yes, and always allow when not in a project", "是，在未分组项目中始终允许"],
    ["Yes, and always allow", "是，始终允许"],
    ["Skip", "跳过"],
    ["Cancel", "取消"],
    ["Confirm", "确认"],
    ["Continue", "继续"],
    ["Proceed", "继续"],
    ["Retry", "重试"],
    ["Try again", "重试"],
    ["Regenerate", "重新生成"],
    ["Stop", "停止"],
    ["Undo", "撤销"],
    ["Redo", "重做"],
    ["Dismiss", "忽略"],
    ["Close", "关闭"],
    ["Submit", "提交"],
    ["Approve", "批准"],
    ["Decline", "拒绝"],
    ["Ask", "询问"],
    ["View details", "查看详情"],
    ["Hide details", "隐藏详情"],
    ["Edit", "编辑"],
    ["Delete", "删除"],
    ["Save", "保存"],
    ["Send", "发送"],
    ["Attach", "添加附件"]
  ]);

  const CHAT_STATUS_EXACT_MAP = new Map([
    ["Waiting for user input", "等待用户输入"],
    ["Running command", "运行命令"],
    ["Ran command", "已运行命令"],
    ["Reading file", "读取文件"],
    ["Read file", "已读取文件"],
    ["Searching...", "搜索中..."],
    ["Searching", "搜索中"],
    ["Generating...", "生成中..."],
    ["Generating", "生成中"],
    ["Planning...", "规划中..."],
    ["Reviewing...", "审阅中..."],
    ["Thinking...", "思考中..."],
    ["Thinking", "思考中"],
    ["Thought Process", "思考过程"],
    ["Working...", "运行中..."],
    ["Working", "运行中"]
  ]);

  // Strict exact-only allowlist for verified inline permission/confirmation dialogs inside chat panes
  const INLINE_PERMISSION_TITLES = new Map([
    ["Confirm Undo", "确认撤销"],
    ["Confirm Redo", "确认重做"],
    ["This undo action will not make any code changes.", "此撤销操作不会对代码做出任何更改。"],
    ["This redo action will not make any code changes.", "此重做操作不会对代码做出任何更改。"],
    ["Allow write access to this path?", "允许写入此路径吗？"],
    ["Allow read access to this path?", "允许读取此路径吗？"],
    ["Allow command execution?", "允许执行此命令吗？"],
    ["Confirming this undo action will make the following changes:", "确认此撤销操作将做出以下更改："],
    ["Confirming this undo action will make the following changes", "确认此撤销操作将做出以下更改："],
    ["Confirming this undo action will not make any code changes.", "确认此撤销操作不会做出任何代码更改。"],
    ["Confirming this undo action will not make any code changes", "确认此撤销操作不会做出任何代码更改。"],
    ["Confirming this redo action will make the following changes:", "确认此重做操作将做出以下更改："],
    ["Confirming this redo action will make the following changes", "确认此重做操作将做出以下更改："],
    ["Confirming this redo action will not make any code changes.", "确认此重做操作不会做出任何代码更改。"],
    ["Confirming this redo action will not make any code changes", "确认此重做操作不会做出任何代码更改。"],
    ["Undo changes up to this point", "撤销更改至此处"],
    ["Redo changes up to this point", "重做更改至此处"]
  ]);

  const INLINE_PERMISSION_BUTTON_MAP = new Map([
    ["Yes, allow this time", "是，仅本次允许"],
    ["Yes, and always allow in this conversation", "是，在本次对话中始终允许"],
    ["Yes, and always allow when not in a project", "是，在未分组项目中始终允许"],
    ["Yes, and always allow", "是，始终允许"],
    ["No (tell the agent what to do instead)", "否 (告诉智能体改做什么)"],
    ["Allow", "允许"],
    ["Allow once", "仅本次允许"],
    ["Always allow", "始终允许"],
    ["Deny", "拒绝"],
    ["Run", "运行"],
    ["Skip", "跳过"],
    ["Cancel", "取消"],
    ["Confirm", "确认"],
    ["Approve", "批准"],
    ["Decline", "拒绝"],
    ["Undo", "撤销"],
    ["Redo", "重做"],
    ["Continue", "继续"],
    ["Proceed", "继续"]
  ]);

  // Action labels for the application-owned file summary card.
  const SUMMARY_ACTION_MAP = new Map([
    ["Review", "审阅"],
    ["Accept", "接受"],
    ["Accept all", "全部接受"],
    ["Accept All", "全部接受"],
    ["Reject", "拒绝"],
    ["Reject all", "全部拒绝"],
    ["Reject All", "全部拒绝"],
    ["View diff", "查看差异"],
    ["Open diff", "打开差异"]
  ]);

  // Display attributes for the application-owned turn feedback toolbar.
  const FEEDBACK_ATTR_MAP = new Map([
    ["Copy", "复制"],
    ["Copied", "已复制"],
    ["Copied!", "已复制！"],
    ["Copy code", "复制代码"],
    ["Copy message", "复制消息"],
    ["Copy response", "复制回复"],
    ["Good response", "好的回答"],
    ["Bad response", "差的回答"],
    ["Thumbs up", "点赞"],
    ["Thumbs down", "点踩"]
  ]);

  // Outer artifact panel toolbar native <button> labels (NEVER inside [data-artifact-content] or div[role="button"])
  const ARTIFACT_TOOLBAR_BUTTON_MAP = new Map([
    ["Close", "关闭"],
    ["Copy", "复制"],
    ["Copied", "已复制"],
    ["Copied!", "已复制！"],
    ["Review", "审阅"],
    ["Download", "下载"],
    ["Accept", "接受"],
    ["Reject", "拒绝"],
    ["Expand", "展开"],
    ["Collapse", "折叠"],
    ["Open", "打开"],
    ["Save", "保存"],
    ["Edit", "编辑"]
  ]);

  // Safe string replacement that never interprets $&, $1, $$ in dynamic values
  function replaceTrimmed(text, replacement) {
    const trimmed = text.trim();
    if (!trimmed) return text;
    const idx = text.indexOf(trimmed);
    if (idx === -1) return replacement;
    return text.slice(0, idx) + replacement + text.slice(idx + trimmed.length);
  }

  // Strictly parse numeric duration segments only (e.g. "22s", "1m 12s", "850ms", "1.5h")
  function formatStrictDuration(raw) {
    if (!raw || typeof raw !== 'string') return null;
    const tokens = raw.match(/\d+(?:\.\d+)?\s*(?:ms|h|m|s)/gi);
    if (!tokens || tokens.length === 0) return null;
    if (raw.replace(/\d+(?:\.\d+)?\s*(?:ms|h|m|s)/gi, '').trim() !== '') return null;
    return tokens.map((tok) => {
      const m = tok.match(/^(\d+(?:\.\d+)?)\s*(ms|h|m|s)$/i);
      if (!m) return tok;
      const unit = m[2].toLowerCase();
      const zhUnit = unit === 'ms' ? '毫秒' : unit === 'h' ? '小时' : unit === 'm' ? '分' : '秒';
      return m[1] + zhUnit;
    }).join(' ');
  }

  function formatResetDuration(raw) {
    if (!raw || typeof raw !== 'string') return null;
    const tokens = raw.match(/\d+\s*(?:days?|d|hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)\b/gi);
    if (!tokens || tokens.length === 0) return null;
    const leftover = raw.replace(/\d+\s*(?:days?|d|hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)\b/gi, '').replace(/[\s,and]+/gi, '');
    if (leftover !== '') return null;
    return tokens.map((tok) => {
      const m = tok.match(/^(\d+)\s*([a-z]+)$/i);
      if (!m) return tok;
      const u = m[2].toLowerCase();
      if (u.startsWith('d')) return m[1] + '天';
      if (u.startsWith('h')) return m[1] + '小时';
      if (u.startsWith('m')) return m[1] + '分钟';
      return m[1] + '秒';
    }).join(' ');
  }

  function translateRelativeTime(text, allowBareLowercase) {
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (!trimmed) return text;
    if (trimmed === 'Just now') return replaceTrimmed(text, '刚刚');
    if (trimmed === 'Yesterday') return replaceTrimmed(text, '昨天');
    let m;
    if ((m = trimmed.match(/^(\d+)\s*s\s+ago$/i))) return replaceTrimmed(text, m[1] + '秒前');
    if ((m = trimmed.match(/^(\d+)\s*m\s+ago$/i))) return replaceTrimmed(text, m[1] + '分钟前');
    if ((m = trimmed.match(/^(\d+)\s*h\s+ago$/i))) return replaceTrimmed(text, m[1] + '小时前');
    if ((m = trimmed.match(/^(\d+)\s*d\s+ago$/i))) return replaceTrimmed(text, m[1] + '天前');
    if (allowBareLowercase) {
      // Strict lowercase without whitespace so 2D/3D/1M/2H/5S are never corrupted
      if ((m = trimmed.match(/^(\d+)s$/))) return replaceTrimmed(text, m[1] + '秒前');
      if ((m = trimmed.match(/^(\d+)m$/))) return replaceTrimmed(text, m[1] + '分钟前');
      if ((m = trimmed.match(/^(\d+)h$/))) return replaceTrimmed(text, m[1] + '小时前');
      if ((m = trimmed.match(/^(\d+)d$/))) return replaceTrimmed(text, m[1] + '天前');
    }
    return text;
  }

  function translateChatStatusText(text) {
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (!trimmed) return text;
    if (CHAT_STATUS_EXACT_MAP.has(trimmed)) {
      return replaceTrimmed(text, CHAT_STATUS_EXACT_MAP.get(trimmed));
    }
    let m;
    if ((m = trimmed.match(/^Worked for\s+(.+?)(?:\s*(>))?$/i))) {
      const dur = formatStrictDuration(m[1]);
      if (dur) return replaceTrimmed(text, '运行耗时 ' + dur + (m[2] ? ' >' : ''));
    }
    if ((m = trimmed.match(/^Thought for\s+(.+?)(?:\s*(>))?$/i))) {
      const dur = formatStrictDuration(m[1]);
      if (dur) return replaceTrimmed(text, '思考耗时 ' + dur + (m[2] ? ' >' : ''));
    }
    if ((m = trimmed.match(/^Working(\.{0,3})$/))) {
      return replaceTrimmed(text, '运行中' + m[1]);
    }
    if ((m = trimmed.match(/^Thinking(\.{0,3})$/))) {
      return replaceTrimmed(text, '思考中' + m[1]);
    }
    if ((m = trimmed.match(/^Explored\s+(\d+)\s+files?(?:\s*(>))?$/i))) {
      return replaceTrimmed(text, '已浏览 ' + m[1] + ' 个文件' + (m[2] ? ' >' : ''));
    }
    if (/^Editing\s+\S/.test(trimmed)) {
      return replaceTrimmed(text, '正在编辑' + trimmed.slice('Editing'.length));
    }
    if (/^(?:Exploring file|running command|editing file)(?:,\s*(?:Exploring file|running command|editing file))*$/i.test(trimmed)) {
      const parts = trimmed.split(/,\s*/).map((part) => {
        const lower = part.toLowerCase();
        if (lower === 'exploring file') return '浏览文件';
        if (lower === 'running command') return '运行命令';
        if (lower === 'editing file') return '编辑文件';
        return part;
      });
      return replaceTrimmed(text, parts.join('、'));
    }
    return text;
  }

  function translateFileSummaryText(text) {
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (!trimmed) return text;
    let m;
    if ((m = trimmed.match(/^(\d+)\s+files?\s+changed(?:\s+(\+\d+)\s+(-\d+))?(?:\s*(>))?$/i))) {
      let out = m[1] + ' 个文件已修改';
      if (m[2] && m[3]) out += ' ' + m[2] + ' ' + m[3];
      if (m[4]) out += ' >';
      return replaceTrimmed(text, out);
    }
    if ((m = trimmed.match(/^Files?\s+Changed\s*(\d+)$/i))) {
      return replaceTrimmed(text, '已修改文件 ' + m[1]);
    }
    return text;
  }

  function translateInlineDialogTitle(text) {
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (!trimmed) return text;
    if (INLINE_PERMISSION_TITLES.has(trimmed)) {
      return replaceTrimmed(text, INLINE_PERMISSION_TITLES.get(trimmed));
    }
    return text;
  }

  function translateInlineDialogButton(text) {
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (!trimmed) return text;
    if (INLINE_PERMISSION_BUTTON_MAP.has(trimmed)) {
      return replaceTrimmed(text, INLINE_PERMISSION_BUTTON_MAP.get(trimmed));
    }
    return text;
  }

  const MODAL_TITLE_MAP = new Map([
    ['Delete MCP Server', '删除 MCP 服务器'],
    ['Delete Skill', '删除技能'],
    ['Delete Task', '删除任务'],
    ['Customize Sidebar', '自定义侧边栏'],
    ['Review skill before installing', '安装前审阅技能'],
    ['Review plugin before installing', '安装前审阅插件'],
  ]);

  function translateModalTitle(text) {
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (!trimmed) return text;
    if (MODAL_TITLE_MAP.has(trimmed)) {
      return replaceTrimmed(text, MODAL_TITLE_MAP.get(trimmed));
    }
    let m;
    if ((m = trimmed.match(/^Set up (.+)$/))) {
      return replaceTrimmed(text, '配置 ' + m[1]);
    }
    if ((m = trimmed.match(/^Review permissions for (.+)$/))) {
      return replaceTrimmed(text, '审阅 ' + m[1] + ' 的权限');
    }
    if ((m = trimmed.match(/^Install folder "(.+)" is already in use$/))) {
      return replaceTrimmed(text, '安装目录“' + m[1] + '”已被占用');
    }
    return text;
  }

  const MODAL_BODY_MAP = new Map([
    ['Are you sure you want to delete', '确定要删除'],
    ['? This will remove it from your MCP configuration.', ' 吗？此操作会将其从 MCP 配置中移除。'],
    ['? This action cannot be undone.', ' 吗？此操作无法撤销。'],
    ['? This removes it from your config directory.', ' 吗？此操作会将其从配置目录中移除。'],
    ['Replacing removes the currently installed plugin and installs the new one in its place.', '替换将移除当前已安装的插件，并在原位置安装新插件。'],
    ['needs a few details from you before it can run.', '在运行前需要您补充以下信息。'],
    ['Please fill out all required argument values before continuing.', '继续前请填写所有必填参数值。'],
    ['Failed to update permissions. Please try again.', '更新权限失败，请重试。'],
    ['This extension has no declared permissions requiring user input.', '此扩展没有需要用户输入的声明权限。'],
    ['Please fill out all required values to continue.', '请填写所有必填项以继续。'],
    ['Resolving permissions...', '正在解析权限...'],
    ['Agents created by', '由'],
    ['run in a dedicated', '创建的智能体将在独立的'],
    ['with its own permissions, which you can change anytime in the', '中运行，拥有独立权限，您可以随时在'],
    ['settings page.', '设置页面中更改。'],
    ['Workspaces', '工作区'],
    ['Folders these agents can access.', '这些智能体可访问的文件夹。'],
    ['Access grants', '访问授权'],
    ['Commands and files these agents can use.', '这些智能体可使用的命令和文件。'],
    ['No folder selected', '未选择文件夹'],
  ]);

  function translateModalBody(text) {
    if (!text || typeof text !== 'string') return text;
    if (text === 'Delete ') return '删除 ';
    const trimmed = text.trim();
    if (!trimmed) return text;
    if (MODAL_BODY_MAP.has(trimmed)) {
      return replaceTrimmed(text, MODAL_BODY_MAP.get(trimmed));
    }
    let m;
    if ((m = trimmed.match(/^On top of those defaults,\s*(.+)\s+requests the access below\.$/))) {
      return replaceTrimmed(text, '在默认权限之外，' + m[1] + ' 还请求以下访问权限。');
    }
    if ((m = trimmed.match(/^This (plugin|skill)'s source is in (.+), which can have looser review standards than standard Google code\. Review its contents before installing\.$/))) {
      return replaceTrimmed(
        text,
        '此' + (m[1] === 'skill' ? '技能' : '插件') + '的源码位于 ' + m[2] + '，审核标准可能较标准 Google 代码更为宽松。安装前请先审阅其内容。'
      );
    }
    return text;
  }

  function translateComposerText(text) {
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (!trimmed) return text;
    if (CHAT_ACTION_BUTTON_MAP.has(trimmed)) {
      return replaceTrimmed(text, CHAT_ACTION_BUTTON_MAP.get(trimmed));
    }
    if (trimmed !== 'Just now' && trimmed !== 'Yesterday' && dictionaryMap.has(trimmed)) {
      return replaceTrimmed(text, dictionaryMap.get(trimmed));
    }
    let m;
    if ((m = trimmed.match(/^(\d+)\s*attachments?$/i))) {
      return replaceTrimmed(text, m[1] + ' 个附件');
    }
    if ((m = trimmed.match(/^Start\s+Best-of-(\d+)$/i))) {
      return replaceTrimmed(text, '启动 ' + m[1] + ' 方案优选');
    }
    return text;
  }

  function translateAppShellText(text, opts) {
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (!trimmed) return text;
    const allowRelTime = !opts || opts.allowRelTime !== false;
    const allowBareRelTime = !opts || opts.allowBareRelTime !== false;
    const allowCoreWords = !opts || opts.allowCoreWords !== false;
    const allowExtraLabels = !opts || opts.allowExtraLabels !== false;

    if (trimmed !== 'Just now' && trimmed !== 'Yesterday' && dictionaryMap.has(trimmed)) {
      return replaceTrimmed(text, dictionaryMap.get(trimmed));
    }

    let m;
    if ((m = trimmed.match(/^Your Plan:\s*(.+)$/))) {
      return replaceTrimmed(text, '当前计划：' + m[1]);
    }
    if (trimmed === 'Gemini 4 Argon is now available on paid Pro plans.' ||
        trimmed === 'Gemini 4 Argon is now available on paid Pro plans') {
      return replaceTrimmed(text, 'Gemini 4 Argon 现已面向付费 Pro 计划订阅用户开放。');
    }
    if (trimmed === 'Choose whether to be notified when the agent needs your attention.' ||
        trimmed === 'Choose whether to be notified when the agent needs your attention') {
      return replaceTrimmed(text, '选择当智能体需要您的关注或完成任务时是否接收通知。');
    }
    if ((m = trimmed.match(/^Setting up WSL:\s*(.+)$/))) {
      return replaceTrimmed(text, '正在配置 WSL: ' + m[1]);
    }
    if ((m = trimmed.match(/^Turn\s*(\d+)(?:\s*of\s*(\d+))?$/i))) {
      return replaceTrimmed(text, m[2] ? ('第 ' + m[1] + ' / ' + m[2] + ' 轮') : ('第 ' + m[1] + ' 轮'));
    }
    if ((m = trimmed.match(/^Jump to turn\s*(\d+)$/i))) {
      return replaceTrimmed(text, '跳转至第 ' + m[1] + ' 轮');
    }
    if ((m = trimmed.match(/^Chapter\s*(\d+)$/i))) {
      return replaceTrimmed(text, '第 ' + m[1] + ' 章');
    }
    if ((m = trimmed.match(/^(\d+)\s*turns?$/i))) {
      return replaceTrimmed(text, m[1] + ' 轮对话');
    }
    if ((m = trimmed.match(/^Page\s*(\d+)\s*of\s*(\d+)$/i))) {
      return replaceTrimmed(text, '第 ' + m[1] + ' 页，共 ' + m[2] + ' 页');
    }
    if ((m = trimmed.match(/^(\d+)\s*attachments?$/i))) {
      return replaceTrimmed(text, m[1] + ' 个附件');
    }
    if ((m = trimmed.match(/^(\d+(?:\.\d+)?)%\s+of the customization budget is available\.?$/))) {
      return replaceTrimmed(text, '自定义项预算可用额度为 ' + m[1] + '%。');
    }
    if (/^%\s*of the customization budget is available\.?$/.test(trimmed)) {
      return replaceTrimmed(text, '% 的自定义项预算可用额度。');
    }
    if (/^of the customization budget is available\.?$/.test(trimmed)) {
      return replaceTrimmed(text, '的自定义项预算可用额度。');
    }
    if ((m = trimmed.match(/^Show\s+(\d+)\s+breakdowns?$/))) {
      return replaceTrimmed(text, '显示 ' + m[1] + ' 项明细');
    }
    if ((m = trimmed.match(/^(\d+)\s+agents?\s+running$/i))) {
      return replaceTrimmed(text, m[1] + ' 个智能体运行中');
    }
    if (/^No\s+agents?\s+running$/i.test(trimmed)) {
      return replaceTrimmed(text, '暂无运行中的智能体');
    }
    if ((m = trimmed.match(/^Start\s+Best-of-(\d+)$/i))) {
      return replaceTrimmed(text, '启动 ' + m[1] + ' 方案优选');
    }
    if ((m = trimmed.match(/^Artifacts?\s*(\d+)$/i))) {
      return replaceTrimmed(text, '产物 ' + m[1]);
    }
    if (/^No\s+artifacts?\s+generated\.?$/i.test(trimmed)) {
      return replaceTrimmed(text, '未生成任何产物');
    }
    if (/^No\s+projects?\s+found\.?$/i.test(trimmed)) {
      return replaceTrimmed(text, '暂无项目');
    }
    if (/^No\s+Project$/i.test(trimmed)) {
      return replaceTrimmed(text, '无项目');
    }
    if (trimmed === 'Type') return replaceTrimmed(text, '输入');
    if (trimmed === 'and select') return replaceTrimmed(text, '并选择');
    if (trimmed === 'to have the agent generate a plan.' || trimmed === 'to have the agent generate a plan') {
      return replaceTrimmed(text, '即可让智能体生成计划。');
    }
    if (trimmed === 'Visit') return replaceTrimmed(text, '访问');
    if (trimmed === 'Legal Help') return replaceTrimmed(text, '法律帮助');
    if (trimmed === 'to ask for content changes for legal reasons.' || trimmed === 'to ask for content changes for legal reasons') {
      return replaceTrimmed(text, '以出于法律原因请求更改内容。');
    }
    if ((m = trimmed.match(/^Learn more about\s+(.+)$/))) {
      const target = dictionaryMap.has(m[1]) ? dictionaryMap.get(m[1]) : m[1];
      return replaceTrimmed(text, '了解更多关于 ' + target + ' 的信息');
    }
    if ((m = trimmed.match(/^You have used some of your weekly limit, it will fully refresh in\s+(.+)\.$/))) {
      const timeStr = formatResetDuration(m[1]);
      if (timeStr) return replaceTrimmed(text, '您已使用部分每周限额，它将在 ' + timeStr + ' 后完全重置。');
    }
    if ((m = trimmed.match(/^You have used some of your 5-hour limit, it will fully refresh in\s+(.+)\.$/))) {
      const timeStr = formatResetDuration(m[1]);
      if (timeStr) return replaceTrimmed(text, '您已使用部分五小时限额，它将在 ' + timeStr + ' 后完全重置。');
    }
    if ((m = trimmed.match(/^Resets?\s+in\s+(.+)$/i))) {
      const timeStr = formatResetDuration(m[1]);
      if (timeStr) return replaceTrimmed(text, '将在 ' + timeStr + ' 后重置');
    }
    if ((m = trimmed.match(/^Uploads?\s*(\d+)$/i))) return replaceTrimmed(text, '已上传文件 ' + m[1]);
    if ((m = trimmed.match(/^See all\s*\((.+?)\)$/i))) return replaceTrimmed(text, '查看全部 (' + m[1] + ')');
    if ((m = trimmed.match(/^Background Tasks?\s*(\d+)$/i))) return replaceTrimmed(text, '后台任务 ' + m[1]);
    if ((m = trimmed.match(/^Background Tasks?\s*\((\d+)\)$/i))) return replaceTrimmed(text, '后台任务 (' + m[1] + ')');
    if ((m = trimmed.match(/^Terminals?\s*(\d+)$/i))) return replaceTrimmed(text, '终端 ' + m[1]);
    if ((m = trimmed.match(/^Terminals?\s*\((\d+)\)$/i))) return replaceTrimmed(text, '终端 (' + m[1] + ')');
    if (/^No\s+subagents?(?:\s*running)?\.?$/i.test(trimmed)) return replaceTrimmed(text, '暂无子智能体');
    if ((m = trimmed.match(/^Available AI Credits:\s*([\d,]+)$/))) {
      return replaceTrimmed(text, '可用 AI 积分: ' + m[1]);
    }
    if ((m = trimmed.match(/^Send feedback as\s+(.+)$/))) {
      return replaceTrimmed(text, '以 ' + m[1] + ' 的身份发送反馈');
    }
    if ((m = trimmed.match(/^(\+?\d+)\s+more\s+lines$/))) {
      return replaceTrimmed(text, '更多 ' + m[1] + ' 行');
    }
    if ((m = trimmed.match(/^See\s+(\d+)\s+more$/i))) return replaceTrimmed(text, '查看更多 ' + m[1] + ' 项');
    if ((m = trimmed.match(/^Show\s+(\d+)\s+more$/i))) return replaceTrimmed(text, '展开其余 ' + m[1] + ' 项');
    if ((m = trimmed.match(/^Last\s+(\d+)\s+days?$/i))) return replaceTrimmed(text, '最近 ' + m[1] + ' 天');
    if ((m = trimmed.match(/^Last\s+(\d+)\s+hours?$/i))) return replaceTrimmed(text, '最近 ' + m[1] + ' 小时');
    if ((m = trimmed.match(/^Last\s+(\d+)\s+months?$/i))) return replaceTrimmed(text, '最近 ' + m[1] + ' 个月');
    if ((m = trimmed.match(/^Version\s+([\d\.]+(?:-\w+)?)$/))) {
      return replaceTrimmed(text, '版本 v' + m[1]);
    }
    if ((m = trimmed.match(/^Start using\s+(.+?),\s*our best\s+(.+?)\s+model\.?$/i))) {
      return replaceTrimmed(text, '开始使用 ' + m[1] + '，我们最强大的 ' + m[2] + ' 模型。');
    }
    if (trimmed === 'Configure the browser subagent.' || trimmed === 'Configure the browser subagent') {
      return replaceTrimmed(text, '配置浏览器子智能体。');
    }
    if (trimmed === 'The browser subagent can be invoked by typing /browser in the conversation input box.') {
      return replaceTrimmed(text, '您可以在对话输入框中输入 /browser 来调用浏览器子智能体。');
    }
    if (trimmed === "You currently don't have any MCP Servers installed.") {
      return replaceTrimmed(text, '您目前尚未安装任何 MCP 服务器。');
    }
    if (trimmed === 'Add an MCP server above or add a custom one via the MCP Config.') {
      return replaceTrimmed(text, '请在上方添加 MCP 服务器，或通过 MCP 配置添加自定义服务器。');
    }
    if ((m = trimmed.match(/^Sort and filter conversations \((\d+) active\)$/))) {
      return replaceTrimmed(text, '排序和筛选对话（已启用 ' + m[1] + ' 项）');
    }
    if ((m = trimmed.match(/^Add \((\d+)\)$/))) {
      return replaceTrimmed(text, '添加 (' + m[1] + ')');
    }
    if ((m = trimmed.match(/^Show\s+(\d+)\s+more\s+subagents?$/i))) {
      return replaceTrimmed(text, '展开其余 ' + m[1] + ' 个子智能体');
    }
    if ((m = trimmed.match(/^(Group By|Idle Conversations):\s*(.+)$/))) {
      const keyZh = dictionaryMap.get(m[1]) ?? m[1];
      const valZh = dictionaryMap.get(m[2]) ?? m[2];
      return replaceTrimmed(text, keyZh + '：' + valZh);
    }
    if ((m = trimmed.match(/^(Commands|Unsandboxed commands|Read files|Write files|Read URLs|Browser actions|Browser downloads|MCP tools|Admin escalation|Custom|Other),\s*(\d+)\s+grants?$/))) {
      const lblZh = dictionaryMap.get(m[1]) ?? m[1];
      return replaceTrimmed(text, lblZh + '，' + m[2] + ' 项授权');
    }

    if (allowRelTime) {
      const relRes = translateRelativeTime(text, allowBareRelTime);
      if (relRes !== text) return relRes;
    }

    if (allowExtraLabels) {
      const label = trimmed.endsWith('.') ? trimmed.slice(0, -1) : trimmed;
      const translated = extraLabelsMap.get(trimmed) ?? extraLabelsMap.get(label);
      if (translated !== undefined) return replaceTrimmed(text, translated);
    }

    // Short Word Exact Replacement (strictly gated to interactive UI controls / labels)
    if (allowCoreWords) {
      const wordsCount = trimmed.split(/\s+/).length;
      if (wordsCount <= 3) {
        const lowerText = trimmed.toLowerCase();
        if (coreWordsMap.has(lowerText)) {
          return replaceTrimmed(text, coreWordsMap.get(lowerText));
        }
      }
    }

    return text;
  }

  function translateHomeGreeting(text) {
    if (!text || typeof text !== 'string') return text;
    const trimmed = text.trim();
    if (!trimmed) return text;
    if (trimmed === 'Hey there, what should we build today?') {
      return replaceTrimmed(text, '你好，今天我们要构建什么？');
    }
    if (trimmed === 'Welcome back. Where should we pick up?') {
      return replaceTrimmed(text, '欢迎回来，我们从哪里继续？');
    }
    if (trimmed === "Good to see you. What's next?") {
      return replaceTrimmed(text, '很高兴见到你，接下来做什么？');
    }
    let m;
    if ((m = trimmed.match(/^Hey\s+(.+?),\s*what should we build today\?$/))) {
      return replaceTrimmed(text, '你好，' + m[1] + '。今天我们要构建什么？');
    }
    if ((m = trimmed.match(/^Welcome back,\s+(.+?)\.\s*Where should we pick up\?$/))) {
      return replaceTrimmed(text, '欢迎回来，' + m[1] + '。我们从哪里继续？');
    }
    if ((m = trimmed.match(/^Good to see you,\s+(.+?)\.\s*What's next\?$/))) {
      return replaceTrimmed(text, '很高兴见到你，' + m[1] + '。接下来做什么？');
    }
    return text;
  }

  function exactLabel(map, text) {
    const value = map.get(text.trim());
    return value === undefined ? text : replaceTrimmed(text, value);
  }

  return {
    shell: translateAppShellText,
    homeGreeting: translateHomeGreeting,
    composer: translateComposerText,
    status: translateChatStatusText,
    time: (text) => translateRelativeTime(text, true),
    fileSummary: translateFileSummaryText,
    fileAction: (text) => exactLabel(SUMMARY_ACTION_MAP, text),
    feedback: (text) => exactLabel(FEEDBACK_ATTR_MAP, text),
    artifactAction: (text) => exactLabel(ARTIFACT_TOOLBAR_BUTTON_MAP, text),
    permissionTitle: translateInlineDialogTitle,
    permissionButton: translateInlineDialogButton,
    modalTitle: translateModalTitle,
    modalBody: translateModalBody
  };
})();

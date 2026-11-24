const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const sources = ['catalog.js', 'formatters.js'].map(
  name => fs.readFileSync(path.join(process.argv[2], name), 'utf8')
);
const formats = vm.runInNewContext(sources.join('\n') + '\nformats');

for (const value of ['__proto__', 'hasOwnProperty', 'constructor', '2D', '3D', '1M', '5S']) {
  assert.equal(formats.shell(value), value);
}
for (const value of [
  'It requires Node 20 to be installed.',
  'See our server response: custom trace.',
  'Patch note: No projects found in the log.',
  'Manage your notification preferences only in this workspace…',
  'Gemini 4 Argon is now available in preview with custom quota details.',
  'Using the Google Antigravity Python SDK to b',
  'Worked for 22s',
  '2 files changed +99 -23 >',
]) {
  assert.equal(formats.shell(value), value);
}
assert.equal(formats.shell('Settings'), '设置');
assert.equal(formats.shell('Play a sound when your action is needed or the agent finishes.'),
  '当需要您操作或智能体完成任务时播放提示音。');
assert.equal(formats.status('Thought for a while testing'), 'Thought for a while testing');
assert.equal(formats.status('Thought for 1m 5s >'), '思考耗时 1分 5秒 >');
assert.equal(formats.status('Editing foo$&bar.py +3 -1'), '正在编辑 foo$&bar.py +3 -1');
assert.equal(formats.status('Editing config.py'), '正在编辑 config.py');
assert.equal(formats.status('Explored 2 files'), '已浏览 2 个文件');
assert.equal(formats.fileSummary('2 files changed +99 -23 >'), '2 个文件已修改 +99 -23 >');
assert.equal(formats.time('2m'), '2分钟前');

// Home greeting templates (named, unnamed, special characters like $&, and non-greeting guards)
assert.equal(formats.homeGreeting('Hey there, what should we build today?'), '你好，今天我们要构建什么？');
assert.equal(formats.homeGreeting('Welcome back. Where should we pick up?'), '欢迎回来，我们从哪里继续？');
assert.equal(formats.homeGreeting("Good to see you. What's next?"), '很高兴见到你，接下来做什么？');
assert.equal(formats.homeGreeting('Hey Orabone, what should we build today?'), '你好，Orabone。今天我们要构建什么？');
assert.equal(formats.homeGreeting('Welcome back, Orabone. Where should we pick up?'), '欢迎回来，Orabone。我们从哪里继续？');
assert.equal(formats.homeGreeting("Welcome back, foo$&bar. Where should we pick up?"), '欢迎回来，foo$&bar。我们从哪里继续？');
assert.equal(formats.homeGreeting("Good to see you, Orabone. What's next?"), '很高兴见到你，Orabone。接下来做什么？');
assert.equal(formats.homeGreeting('Welcome back, Orabone.'), 'Welcome back, Orabone.');
assert.equal(formats.homeGreeting('Settings'), 'Settings');

// Plan & v2.34 settings / shortcuts / voice / browser / account labels
assert.equal(formats.shell('Your Plan: Google AI Ultra'), '当前计划：Google AI Ultra');
assert.equal(formats.shell('Your Plan: Google AI Pro'), '当前计划：Google AI Pro');
assert.equal(formats.shell('By using this app, you agree to its'), '使用本应用即表示您同意其');
assert.equal(formats.shell('  By using this app, you agree to its '), '  使用本应用即表示您同意其 ');
assert.equal(formats.shell('Knowledge Work'), '知识工作');
assert.equal(formats.shell('Software Engineering'), '软件工程');
assert.equal(formats.shell('Voice mode'), '语音模式');
assert.equal(formats.shell('Not set'), '未设置');
assert.equal(formats.shell('System default'), '系统默认');
assert.equal(formats.shell('Change…'), '更改…');
assert.equal(formats.shell('Extra High'), '超高');
assert.equal(formats.shell('Orchestrator Settings'), '编排器设置');
assert.equal(formats.shell('Browsing History'), '浏览历史');
assert.equal(formats.shell('Go Back'), '后退');
assert.equal(formats.shell('Terminal: Select All'), '终端：全选');
assert.equal(formats.shell('Show All'), '显示全部');
assert.equal(formats.shell('This computer'), '本机（本地对话）');
assert.equal(formats.shell('Queued messages'), '排队消息');
assert.equal(formats.shell('Search shortcuts...'), '搜索快捷键...');
assert.equal(formats.shell('Remote Agents Data'), '远程智能体数据');
assert.equal(formats.shell('Background Tasks (7)'), '后台任务 (7)');
assert.equal(formats.shell('Terminals (2)'), '终端 (2)');
assert.equal(formats.shell('Show 3 more'), '展开其余 3 项');
assert.equal(formats.shell('Show more'), '展开更多');
assert.equal(formats.shell('Show less'), '收起');
assert.equal(formats.shell('Reload'), '重新加载');
assert.equal(formats.shell('Customize Sections'), '自定义分区');

// Add Context, Palette, Customize Sidebar, Grant Templates & Modal Title/Body Safety
assert.equal(formats.shell('Only Automations'), '仅看自动化');
assert.equal(formats.shell('Sort and filter conversations (3 active)'), '排序和筛选对话（已启用 3 项）');
assert.equal(formats.shell('Add (3)'), '添加 (3)');
assert.equal(formats.shell('Show 2 more subagents'), '展开其余 2 个子智能体');
assert.equal(formats.shell('Show 1 more subagent'), '展开其余 1 个子智能体');
assert.equal(formats.shell('Group By: Workspace'), '分组方式：工作区');
assert.equal(formats.shell('Idle Conversations: Show 5'), '空闲对话：显示 5 项');
assert.equal(formats.shell('Commands, 2 grants'), '命令，2 项授权');

assert.equal(formats.modalTitle('Delete MCP Server'), '删除 MCP 服务器');
assert.equal(formats.modalTitle('Delete Skill'), '删除技能');
assert.equal(formats.modalTitle('Delete Task'), '删除任务');
assert.equal(formats.modalTitle('Customize Sidebar'), '自定义侧边栏');
assert.equal(formats.modalTitle('Review skill before installing'), '安装前审阅技能');
assert.equal(formats.modalTitle('Review plugin before installing'), '安装前审阅插件');
assert.equal(formats.modalTitle('Set up Settings'), '配置 Settings');
assert.equal(formats.modalTitle('Review permissions for Files'), '审阅 Files 的权限');
assert.equal(formats.modalTitle('Install folder "Settings" is already in use'), '安装目录“Settings”已被占用');
assert.equal(formats.modalTitle('Settings'), 'Settings');

assert.equal(formats.modalBody('Are you sure you want to delete '), '确定要删除 ');
assert.equal(formats.modalBody('? This will remove it from your MCP configuration.'), ' 吗？此操作会将其从 MCP 配置中移除。');
assert.equal(formats.modalBody('Delete '), '删除 ');
assert.equal(formats.modalBody('Delete'), 'Delete');
assert.equal(formats.modalBody('Settings'), 'Settings');
assert.equal(formats.modalBody('false'), 'false');
assert.equal(formats.modalBody('Open'), 'Open');
assert.equal(formats.modalBody('workspace'), 'workspace');
assert.equal(
  formats.modalBody("This plugin's source is in foo and bar, which can have looser review standards than standard Google code. Review its contents before installing."),
  '此插件的源码位于 foo and bar，审核标准可能较标准 Google 代码更为宽松。安装前请先审阅其内容。'
);
assert.equal(
  formats.modalBody(' On top of those defaults, Settings requests the access below.'),
  ' 在默认权限之外，Settings 还请求以下访问权限。'
);

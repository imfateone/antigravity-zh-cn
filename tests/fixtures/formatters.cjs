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

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

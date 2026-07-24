const fs = require('fs');
const path = require('path');
const vueCompiler = require('@vue/compiler-sfc');

const dir = 'C:/Users/Administrator/AppData/Roaming/reasonix/global-workspace/huopan/frontend/src/views';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.vue'));

for (const file of files) {
  const source = fs.readFileSync(path.join(dir, file), 'utf8');
  try {
    vueCompiler.parse(source, { filename: file });
  } catch (e) {
    console.log(`ERROR in ${file}:`, e.message.substring(0, 200));
  }
}
console.log('done');

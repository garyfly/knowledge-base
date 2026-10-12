// md-stats.mjs —— 递归统计目录下 .md 文件的数量、字符数、字节数，并列出 Top 10
// 用法：
//   node md-stats.mjs              # 统计当前目录
//   node md-stats.mjs "01 Notes"   # 统计指定目录（相对或绝对路径都行）
//   node md-stats.mjs --json       # 输出 JSON，方便别的程序接着用

import { readdir, readFile } from 'node:fs/promises'
import { join, resolve, relative } from 'node:path'

// ---------------------------------------------------------------- 配置区
const SKIP_DIR_NAMES = new Set(['.obsidian', 'node_modules']) // 额外要跳过的目录名
/** 判断某个目录名是否要跳过：显式列出的，或以 . 开头的隐藏目录 */
const shouldSkipDir = (name) => SKIP_DIR_NAMES.has(name) || name.startsWith('.')

const isMarkdown = (name) => name.toLowerCase().endsWith('.md') // .md / .MD 都算

/**
 * 字符数怎么数：
 *   'codepoint' —— 按 Unicode 码点，中文/emoji 各算 1 个（推荐，符合"字数"直觉）
 *   'utf16'     —— 按 JS 字符串的 UTF-16 长度，emoji 等会算 2 个
 */
const CHAR_METRIC = 'codepoint'

// ---------------------------------------------------------------- 第一步：递归收集所有 .md 的路径
/**
 * @param {string} dir 要遍历的目录（绝对路径）
 * @param {string[]} out 收集结果（累积用，递归时一直传同一个数组）
 * @returns {Promise<string[]>} 所有 .md 文件的绝对路径
 */
async function collectMarkdownFiles(dir, out = []) {
  let entries
  try {
    // withFileTypes: true 让每一项自带 isFile()/isDirectory()，省一次 stat
    entries = await readdir(dir, { withFileTypes: true })
  } catch (err) {
    // 单个目录读不动（权限、被占用、中途被删）不该让整次遍历崩掉
    console.warn(`  [跳过] 无法读取 ${dir}（${err.code}）`)
    return out
  }

  for (const entry of entries) {
    const fullPath = join(dir, entry.name)

    // 跳过符号链接：软链接指回上层目录会造成无限递归
    if (entry.isSymbolicLink()) continue

    if (entry.isDirectory()) {
      if (shouldSkipDir(entry.name)) continue
      await collectMarkdownFiles(fullPath, out) // 进入下一层
    } else if (entry.isFile() && isMarkdown(entry.name)) {
      out.push(fullPath)
    }
  }
  return out
}

// ---------------------------------------------------------------- 第二步：逐个文件读出来算体积
/**
 * 读一个文件，返回它的字符数与字节数
 * @param {string} absPath
 */
async function measureFile(absPath) {
  const buffer = await readFile(absPath) // 拿到 Buffer，字节数不用再猜
  const bytes = buffer.byteLength // 真实字节数（UTF-8 编码后）

  // Buffer → 字符串时必须显式给 'utf8'，否则中文会乱码
  let text = buffer.toString('utf8')
  if (text.charCodeAt(0) === 0xfeff) text = text.slice(1) // 去掉 BOM
  text = text.replace(/\r\n/g, '\n') // 统一换行，避免 Windows 的 \r 虚增字符数

  const chars = CHAR_METRIC === 'utf16' ? text.length : [...text].length

  return { path: absPath, chars, bytes }
}

// ---------------------------------------------------------------- 第三步：汇总 + Top10
function summarize(root, rows) {
  const files = rows.length
  const totalChars = rows.reduce((sum, r) => sum + r.chars, 0)
  const totalBytes = rows.reduce((sum, r) => sum + r.bytes, 0)

  // 想改成"按字节数排 Top10"，把 chars 换成 bytes 即可
  const top10 = [...rows]
    .sort((a, b) => b.chars - a.chars || a.path.localeCompare(b.path, 'zh'))
    .slice(0, 10)
    .map((r) => ({ ...r, path: relative(root, r.path) || r.path }))

  return {
    root,
    files,
    totalChars,
    totalBytes,
    avgChars: files ? Math.round(totalChars / files) : 0,
    top10,
  }
}

// ---------------------------------------------------------------- 输出
const n = (x) => x.toLocaleString('zh-CN')

function printReport(s) {
  console.log(`\n目录：${s.root}`)
  console.log('─'.repeat(64))
  console.log(`  .md 文件数 ： ${n(s.files)}`)
  console.log(`  总字符数   ： ${n(s.totalChars)}`)
  console.log(`  总字节数   ： ${n(s.totalBytes)}  (${(s.totalBytes / 1024).toFixed(1)} KB)`)
  console.log(`  平均字符数 ： ${n(s.avgChars)} / 文件`)

  console.log(`\nTop 10（按字符数）：`)
  if (!s.top10.length) {
    console.log('  （没有找到 .md 文件）')
    return
  }
  const width = Math.max(...s.top10.map((r) => n(r.chars).length))
  s.top10.forEach((r, i) => {
    const size = n(r.chars).padStart(width)
    console.log(`  ${String(i + 1).padStart(2)}. ${size} 字  ${r.path}`)
  })
  console.log()
}

// ---------------------------------------------------------------- 主流程
async function main() {
  const args = process.argv.slice(2)
  const asJson = args.includes('--json')
  const target = args.find((a) => !a.startsWith('--'))

  // resolve 把相对路径变成绝对路径，同时消掉 .. 和多余的斜杠
  const root = resolve(target ?? process.cwd())

  const paths = await collectMarkdownFiles(root) // 1. 找出所有文件
  const rows = await Promise.all(paths.map(measureFile)) // 2. 并发读取并度量
  const summary = summarize(root, rows) // 3. 汇总

  if (asJson) {
    console.log(JSON.stringify(summary, null, 2))
  } else {
    printReport(summary)
  }
}

main().catch((err) => {
  console.error('统计失败：', err)
  process.exitCode = 1
})

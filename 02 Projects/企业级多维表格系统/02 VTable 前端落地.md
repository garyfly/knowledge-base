# 02 VTable 前端落地（渲染层怎么用、数据层只能自己写）

> 版本基准：`@visactor/vtable` **1.26.8**（2026-09-11 发布，MIT）。事实核查见 [`_research/企业级多维表格系统/01-vtable-事实核查.md`](../../_research/企业级多维表格系统/01-vtable-事实核查.md)。
>
> 结论先行：
> 1. **VTable 是 Canvas 渲染引擎，不是数据网格框架**。它没有服务端行模型、没有分页数据协议、没有服务端排序筛选，筛选 UI / 导出 / 撤销重做都在插件包里。所以「用 VTable 搭多维表格」的真实工作量在**你自己写的数据层**。
> 2. **一页一策**：后端分页 + `setRecords(当前页)` + 自建分页器，是最稳的路线；只有"只读大表、要连续滚动"时才用 `CachedDataSource` 行级懒加载，并接受内部排序/自动列宽失效。
> 3. **前端只做三件事**：把元数据翻译成列定义、把用户操作翻译成 API 调用、把冲突和失败翻译回界面。业务规则一律在后端。

---

## 1. 先认清边界：VTable 提供什么 / 不提供什么

| 能力 | VTable 1.26.8 | 你要自己补 |
|---|---|---|
| 百万行渲染、虚拟滚动 | ✅ 核心能力（Canvas，官方称百万级数据秒级渲染） | 数据从哪来 |
| 列定义、表头分组、冻结、合并单元格、主题、tooltip、右键菜单 | ✅ | 菜单里的业务动作 |
| 单元格编辑器 | ✅ 4 个内置（Input / TextArea / DateInput / List）+ `IEditor` 自定义 | 各字段类型的编辑器（选项、成员、附件、关联） |
| 自定义单元格渲染 | ✅ `customLayout`（推荐）/ `customRender` | 各类型的渲染函数 |
| 排序 | ⚠️ 有图标和事件，但**在前端对 records 排序** | 后端排序 + 只把排序状态透传 |
| 筛选 | ⚠️ 核心不内置 UI，靠 `vtable-plugins` 的 `FilterPlugin`（前端按值/按条件） | 服务端筛选面板、筛选 DSL、视图持久化 |
| 分页 | ⚠️ 内置 `pagination` 只是**对内存里 records 的切片** | 服务端分页协议、游标、总数策略 |
| 导入导出 | ⚠️ 插件 `TableExportPlugin`（默认只导当前页） | 大数据量走服务端导出 |
| 复制粘贴 / 撤销重做 | ⚠️ `keyboardOptions` + `HistoryPlugin`（插件） | 与后端操作的幂等对齐 |
| 无障碍 / 移动端 | ❓ 官方文档未覆盖 | 自行评估（企业内桌面场景通常可接受） |

一句话：**VTable 负责"画得好、画得快"，你负责"数据对、状态稳"。**

---

## 2. 包的选择（1.26.8）

```bash
npm i @visactor/vtable@1.26.8 @visactor/react-vtable@1.26.8 \
      @visactor/vtable-editors@1.26.8 @visactor/vtable-plugins@1.26.8
# 需要甘特视图时再加
npm i @visactor/vtable-gantt@1.26.8
```

| 包 | 用途 | 备注 |
|---|---|---|
| `@visactor/vtable` | 核心（ListTable / PivotTable / PivotChart） | 解包体积约 26.7 MB，**必须按需加载**（`ListTableSimple` + 注册用到的东西） |
| `@visactor/react-vtable` | React 封装（peer: react 18 / 19） | React 19 要配对应 `react-reconciler`（18 → 0.29.x，19 → 0.33.x） |
| `@visactor/vtable-editors` | 编辑器 | 核心包已依赖，仍建议显式装同版本 |
| `@visactor/vtable-plugins` | `FilterPlugin` / `TableExportPlugin` / `HistoryPlugin` | 依赖 exceljs + file-saver，体积不小，按视图懒加载 |
| `@visactor/vtable-gantt` | 甘特视图 | 只在甘特视图路由里 import |
| ~~`@visactor/vtable-export`~~ | 已废弃 | 用插件版 `TableExportPlugin` |

---

## 3. 前端分层：把 VTable 关在"渲染层"里

```
┌────────────────────────────────────────────────────┐
│ 视图壳（React）                                     │
│  工具栏 / 筛选面板 / 分组面板 / 字段配置 / 行详情抽屉  │
├────────────────────────────────────────────────────┤
│ DataSheetTable 组件（薄）                           │
│  columns = f(元数据)  records = f(数据层)            │
├────────────────────────────────────────────────────┤
│ 数据层（自己写，最容易写烂的地方）                     │
│  RecordStore：页缓存 / 游标 / 筛选排序状态 / 乐观更新  │
│  EditQueue：待提交的单元格编辑、合并、失败回滚         │
│  RealtimeClient：WebSocket 增量 + 冲突提示            │
├────────────────────────────────────────────────────┤
│ API Client（fetch 封装，统一错误码/重试/取消）         │
└────────────────────────────────────────────────────┘
              ↓ REST + WebSocket
          Java 后端（见 README 架构）
```

关键设计：**`RecordStore` 是唯一数据源**。VTable 只拿到"当前窗口的记录数组"，永远不回读 `tableInstance.records` 当业务数据（它只是视图副本）。

```ts
// 数据层的核心接口，先定形再写实现
interface RecordStore {
  load(params: { viewId: string; cursor?: string; limit: number }): Promise<Page>;
  applyLocalEdit(recordId: string, fieldId: string, value: unknown): void;
  commit(edit: PendingEdit): Promise<'ok' | 'conflict' | 'forbidden'>;
  subscribe(cb: (change: Changeset) => void): () => void;
}

type Page = { records: RecordDto[]; nextCursor?: string; totalHint?: number };
type PendingEdit = { opId: string; recordId: string; fieldId: string; value: unknown; baseVersion: number };
```

---

## 4. 元数据 → 列定义：映射表

VTable 的列配置字段（1.26.8 确认存在）：`field` / `title` / `width` / `headerType` / `cellType` / `fieldFormat` / `style` / `sort` / `showSort` / `customLayout` / `customRender` / `editor` / `aggregation` / `columns`（嵌套即表头分组）/ `hide` / `tree` / `mergeCell`（仅 text）等。

> 注意两个常见误解：**ListTable 没有列级 `format` 字段**，用 `fieldFormat`；**冻结不是列级配置**，是全局 `frozenColCount` / `frozenRowCount`。

| 字段类型 | `cellType` / 渲染 | 编辑器 | 说明 |
|---|---|---|---|
| 文本、多行文本 | `'text'` | `InputEditor` / `TextAreaEditor` | 默认只显示 200 字符（`maxCharactersNumber`），长文本配 tooltip |
| 数字 / 货币 / 百分比 | `'text'` + `fieldFormat` | `InputEditor` + `validateValue` | 显示格式化，存储保留原值 |
| 日期 / 日期时间 | `'text'` + `fieldFormat` | `DateInputEditor` | 时区统一后端算，前端只负责显示 |
| 复选框 | `'checkbox'` | 内置 | 事件 `checkbox_state_change` |
| 单选 | `customLayout`（彩色标签） | 自研 `SelectEditor`（`ListEditor` 只够静态值） | 选项颜色来自字段 `property.options` |
| 多选 | `customLayout`（多个 `VTag`） | 自研多选弹层 | 注意编辑器弹层的 `isEditorElement` |
| 成员 | `customLayout`（头像组） | 自研成员选择器 | 头像走 CDN，懒加载 |
| 附件 | `customLayout`（缩略图 + 计数） | 点击打开上传抽屉 | 不放在单元格里编辑 |
| 关联 / 查找 / 汇总 | `customLayout`（芯片 / 只读文本） | 关联用选择器，查找/汇总只读 | 只读列设 `editor: undefined` |
| 进度条 / 评分 / 迷你图 | `'progressbar'` / `'text'`+`customLayout` / `'sparkline'` | 只读 | 内置能力，别自己画 |
| 公式 | `'text'` + 只读样式 + tooltip 展示表达式 | 只读 | 后端算出结果，前端只显示 |

```ts
// 元数据 → VTable 列的翻译器（节选）
function toVTableColumn(field: FieldDto, ctx: RenderCtx) {
  const base = { field: field.id, title: field.name, width: ctx.widthOf(field.id) ?? 140 };
  switch (field.type) {
    case 'text':    return { ...base, cellType: 'text' as const };
    case 'number':  return { ...base, cellType: 'text' as const,
                            fieldFormat: (r: RecordDto) => formatNumber(r[field.id], field.property) };
    case 'checkbox':return { ...base, cellType: 'checkbox' as const };
    case 'select':  return { ...base, customLayout: (args) => renderTagCell(args, field) };
    case 'user':    return { ...base, customLayout: (args) => renderUserCell(args, field) };
    case 'formula': return { ...base, cellType: 'text' as const, disableSelect: false,
                            style: { bgColor: 'var(--readonly-bg)' } };
    default:        return base;
  }
}
```

**列顺序、隐藏、宽度、冻结**来自视图配置（服务端存），**行高**可以放用户本地偏好 —— 决策依据：多人共享的视图需要一致外观，个人阅读习惯不该污染团队视图。

---

## 5. 数据加载：分页、游标、窗口

### 5.1 推荐方案：后端分页 + `setRecords`

```ts
const PAGE = 200; // 一页 200 行 × 30 列 ≈ 6000 个单元格，Canvas 渲染毫秒级

async function loadFirstPage(store: RecordStore, table: VTable.ListTable) {
  const page = await store.load({ viewId, limit: PAGE });
  table.setRecords(page.records.map(toVTableRecord)); // 只给当前页
}
```

- 翻页/滚动加载 → 请求下一页 → `setRecords` 整体替换。
- 这样"当前页"是唯一渲染数据集，**编辑、排序、筛选都只在页内可见**属于预期行为（和 Airtable 的"页"概念一致）。
- 想要固定行高 + 无缝滚动，可以用"当前页 + 预取下一页"的方式拼成 400 行，滚动到 80% 时提前换页。

### 5.2 不推荐直接开内置 `pagination`

`pagination: { totalCount, perPageCount, currentPage }` 是对**内存里 records** 的切片，服务端只给一页时切片逻辑和页脚页码会互相打架（官方无示例）。自己画分页条 / 自己管游标更省心。

### 5.3 什么时候用 `CachedDataSource`

只读大表（比如"全公司 200 万条日志"）且需要连续滚动时：

```ts
const ds = new VTable.data.CachedDataSource({
  length: total,
  get: (index) => fetchBatch(Math.floor(index / 100) * 100, 100).then(list => list[index % 100])
});
(table as any).dataSource = ds;  // 是实例属性，不是 option.records
```

代价（官方明示）：内部排序失效、`width:'auto'` / `widthMode:'autoWidth'` 失效（要遍历全列）、双击列边界自动调宽会拉全量数据、表头右键汇总会扫全选区。**可编辑的协作表不要用这条路线** —— 编辑 + 懒加载 + 冲突处理会互相打脸。

---

## 6. 编辑链路：乐观更新 + 版本号 + 冲突回退

```
用户双击单元格
  → VTable 唤起 editor（onStart）
  → 用户确认 → editor.getValue()
  → VTable 先改自己的 records，触发 'change_cell_value' 事件
  → 我们：拿到 { col, row, rawValue, currentValue, changedValue }
      1. 生成 opId（uuid）、读本地 baseVersion
      2. 立即本地更新 RecordStore（乐观）
      3. 入 EditQueue，PATCH /records/{id}/cells/{fieldId}
      4. 成功：用服务端返回的 version 覆盖本地
      5. 409 冲突：拉最新值，弹"该单元格已被 XX 修改"，选择保留我的/用最新
      6. 403 无权限：回滚 + toast
      7. 网络失败：指数退避重试 3 次，仍失败进"待同步"队列并提示
```

事件与 API（1.26.8 真实名字）：
- 事件：`table.on('change_cell_value', ({ col, row, rawValue, currentValue, changedValue }) => ...)`；批量：`change_cell_values`。
- 编程改值：`table.changeCellValue(col, row, value, workOnEditableCell?, triggerEvent?)`。

```ts
table.on('change_cell_value', async (args) => {
  const fieldId = columns[args.col].field as string;
  const recordId = recordIdAt(args.row);           // 自己维护 row → recordId 映射
  const opId = crypto.randomUUID();
  store.applyLocalEdit(recordId, fieldId, args.currentValue);
  const result = await store.commit({ opId, recordId, fieldId, value: args.currentValue,
                                      baseVersion: store.versionOf(recordId) });
  if (result === 'conflict') table.setCellValue(args.col, args.row, store.latestValue(recordId, fieldId));
  if (result === 'forbidden') table.setCellValue(args.col, args.row, args.rawValue);
});
```

> `setCellValue` 的准确签名以 `.d.ts` 为准（1.26.8 有 `changeCellValue`；若无 `setCellValue` 就用 `changeCellValue`）。

### 自定义编辑器（`IEditor`）

```ts
class SelectEditor implements VTable.editors.IEditor {
  onStart(ctx: { container: HTMLElement; referencePosition: { rect: any; style?: any };
                 value: unknown; endEdit: () => void; col: number; row: number }) { /* 挂载下拉 */ }
  onEnd() { /* 卸载，避免内存泄漏 */ }
  getValue() { return this.selected; }
  isEditorElement(target: HTMLElement) { return this.popupEl.contains(target); } // 关键：弹层在 body 下
  validateValue(newValue: unknown) { return this.required ? !!newValue : true; }
}
VTable.register.editor('select-editor', new SelectEditor());
// 列上：{ editor: 'select-editor' }
```

三个官方提醒的坑：① 内置编辑器是原生 input 封装，输入法/弹层场景容易提前退出编辑，`isEditorElement` 必须判断 portal 元素；② `validateValue` 返回 `false` / `ValidateEnum.invalidateExit` 阻止提交，支持 Promise 做异步校验；③ `editCellTrigger` 可改 `'click' | 'api' | 'keydown'`。

---

## 7. 自定义单元格：`customLayout` 是主力

```tsx
// React 版：列内放自定义组件，标 role="custom-layout"；props 由 react-vtable 注入
// { table, row, col, value, dataValue, rect } —— 具体字段名以 1.26.8 类型声明为准
function StatusTag(props: { value: unknown }) {
  const opt = optionOf('f_status', props.value);            // 选项 id → 名称/颜色
  return <Tag role="custom-layout" text={opt.name} style={{ fill: opt.color }} />;
}

<ListTable option={option}>
  <ListColumn field="f_status" title="状态" width={120} />
</ListTable>
```

> 组件必须通过 `columns` 里的 `customLayout`（或 react-vtable 的列内嵌写法）真正挂到列上；上例只示意结构，真实写法见官方 React 自定义单元格文档。

约束（官方文档）：
- React 组件里只能返回 react-vtable 的图元（`Group/Text/Image/Tag/...`）。**要嵌真实 DOM（比如原生日期选择器、富文本）走 `CustomComponent` 容器 + `attribute.react = { pointerEvents, container, anchorType, element }`**。
- `customLayout` 每次滚动/重绘都会调用，**函数里不要做网络请求、不要新建大对象**；重活提前算好放闭包。
- 表头自定义用 `role="header-custom-layout"`。

性能经验（待实测验证）：
- 单屏可见单元格约 20×30=600 个；每个自定义单元格建 5 个图元 ≈ 3000 图元，仍在 Canvas 承受范围内，但**别在 `customLayout` 里创建 DOM**。
- 头像、附件缩略图用 `<img>` 图元 + 浏览器缓存，避免每次重绘重新解码。

---

## 8. 排序 / 筛选 / 视图状态：前端只做"传话筒"

VTable 的 `sort: true` 会在**前端**对 `records` 重排。我们的 records 只是当前页，前端排序的结果是错的。处理方式二选一：

**方案 A（推荐）**：列上不设 `sort`，自己画表头排序菜单 → 改视图 `sorts` → 重新请求第 1 页。
**方案 B**：保留 `sort: true`，监听 `SORT_CLICK` → 立刻请求后端 → 用后端结果 `setRecords` 覆盖（前端那一下排序只是过渡态，可接受）。

筛选同理：`FilterPlugin` 是对已加载数据的**前端筛选**，只能做"页内临时过滤"。企业级多维表格的筛选是视图属性（服务端执行），必须自建筛选面板，把条件序列化成 DSL 交给后端（DSL 定义见 `01 数据模型与存储引擎.md` §6.1）。

视图状态（列宽/隐藏/冻结/行高/排序/筛选）保存策略：

| 状态 | 存哪 | 为什么 |
|---|---|---|
| 筛选、排序、分组、隐藏字段、列顺序 | 视图（服务端 `view.config`） | 团队看到同一个视图就该看到同样的内容 |
| 列宽、行高、冻结列数 | 视图 + 用户覆盖 | 默认跟随视图，个人调整存本地（localStorage）覆盖 |
| 当前滚动位置、展开行 | 本地内存 | 刷新即丢，别浪费存储 |

保存节流：列宽拖拽结束（`resize` 相关事件 / `mouseup`）后 debounce 800 ms PATCH 一次，避免一帧一个请求。

---

## 9. 性能预算（前端可测指标）

| 场景 | 目标 | 手段 |
|---|---|---|
| 首屏（200 行 × 30 列） | < 1 s 可交互 | 按需加载、列定义缓存、骨架屏 |
| 滚动 | 稳定 55~60 fps | 每页 ≤ 500 行、`customLayout` 轻量、关闭 `autoWidth` |
| 单元格编辑生效 | < 50 ms 视觉反馈 | 乐观更新，不等服务端 |
| 换页 | < 300 ms | 预取下一页、`AbortController` 取消过期请求 |
| 大表（10 万行只读） | 可滚动浏览 | `CachedDataSource`，明确放弃内部排序 |

必做的三件事：
1. **按需引入**：`ListTableSimple` + 逐项 `register*`；插件的路由级 `import()`。
2. **不要 `autoWidth`**：会遍历整列算宽，和分页/懒加载天然冲突。
3. **控制行数**：VTable 能渲染百万行 ≠ 你应该把百万行塞进浏览器。内存、编辑、命中测试、序列化都会先崩。

---

## 10. 已知限制清单（1.26.8，官方文档口径）

1. Canvas 渲染 ⇒ 没有 DOM 文本节点，浏览器原生选中/复制不可用，复制走 `COPY_DATA` + `formatCopyValue`；无障碍支持文档未覆盖。
2. 容器宽高必须是整数，否则抖动（`tableSizeAntiJitter` 兜底）。
3. 默认只显示前 200 字符（`maxCharactersNumber`）。
4. 包体大（核心 26.7 MB 解包），必须按需加载。
5. 内部排序/筛选都是前端行为，异步/分页场景必须后端做。
6. 编辑器基于原生 input，第三方弹层要自己处理 `isEditorElement`。
7. 没有 HTML SSR，Node 侧只能渲染成图片。
8. React 19 需要对齐 `react-reconciler` 版本，否则 custom-layout 报错。
9. 导出插件默认导当前页，大数据量导出走后端。

---

## 11. 验收清单（P0 结束时逐条打勾）

- [ ] 元数据变更（加/改名/改选项/改顺序）不需要刷新页面就能反映到表格
- [ ] 200 行 × 30 列首屏 < 1 s，滚动无白屏
- [ ] 5 种基础字段类型的编辑器可用，校验失败有提示且不提交
- [ ] 编辑后 50 ms 内界面更新，断网时进待同步队列，恢复后自动重试
- [ ] 409 冲突有明确提示且能一键用最新值
- [ ] 列宽/隐藏/冻结保存后刷新页面仍在（视图级）
- [ ] 筛选条件 3 个以上、含 `in` / `isEmpty` / 多选 `contains`，结果与后端 SQL 一致
- [ ] 复制粘贴 10×10 区域内容正确（含中文、多选）
- [ ] 1 万行只读表用懒加载可流畅滚动，且明确禁用内部排序
- [ ] 弱网（3G 模拟）换页有 loading，过期请求被取消

---

## 相关

- [README 总体方案](README.md)
- [01 数据模型与存储引擎](01%20数据模型与存储引擎.md)
- [03 协同、权限与审计](03%20协同、权限与审计.md)
- [04 从零落地路线](04%20从零落地路线.md)

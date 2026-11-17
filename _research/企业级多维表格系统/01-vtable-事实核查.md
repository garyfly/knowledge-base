---
title: VTable 前端能力事实核查（官方文档级）
type: research
status: verified-as-of-2026-11-16
tags: [vtable, visactor, 表格, 多维表格, 前端]
---

# VTable 前端能力事实核查

> 核查日期：2026-11-16。版本与包信息核对自 npm registry（权威数据源）；文档事实读自官方仓库 `docs/assets/**` 的 Markdown 原文（与官网同源），API 方法名核对自 npm 包 `@visactor/vtable@1.26.8` 的 `.d.ts`。
> 说明：本环境下 `www.visactor.io` / `visactor.com` 程序化抓取返回 `unsupported content type`，因此正文给出「官网 URL + 仓库原文 URL」双链接，后者可直接核验；官网路径由 `docs/menu.json` 的映射规则推出。
> 标注约定：`〔需自查〕` = 官方文档未覆盖；`〔推断〕` = 我的判断而非文档原文。

---

## 1. 包与版本

npm 官方最新稳定版：**`@visactor/vtable` 1.26.8**，发布时间 **2026-09-11**（registry 里 `_npmOperationalInternal.tmp` 时间戳 2026-09-11T10:10:47Z，与 GitHub Release `v1.26.8` 标注的 2026-09-11 一致）。
来源：[registry latest](https://registry.npmjs.org/@visactor/vtable/latest)、[npm 包页](https://www.npmjs.com/package/@visactor/vtable)、[Release v1.26.8](https://github.com/VisActor/VTable/releases/tag/v1.26.8)

| 包 | 版本 | License | 用途（README / 包元数据 / 文档） |
|---|---|---|---|
| `@visactor/vtable` | 1.26.8 | MIT | 核心：ListTable / PivotTable / PivotChart（Canvas 渲染），核心包 `dependencies` 里已带 `@visactor/vtable-editors@1.26.8` — [registry](https://registry.npmjs.org/@visactor/vtable/latest) |
| `@visactor/react-vtable` | 1.26.8 | MIT | React 封装；peer `react ^18.2.0 \|\| ^19.0.0`；依赖 `react-reconciler@0.29.0` — [registry](https://registry.npmjs.org/@visactor/react-vtable/latest)、[文档](https://www.visactor.io/vtable/guide/Developer_Ecology/react) |
| `@visactor/vue-vtable` | 1.26.8 | MIT | Vue 3 封装 — [registry](https://registry.npmjs.org/@visactor/vue-vtable/latest) |
| `@visactor/vtable-editors` | 1.26.8 | MIT | 单元格编辑器包（InputEditor 等）— [registry](https://registry.npmjs.org/@visactor/vtable-editors/latest) |
| `@visactor/vtable-gantt` | 1.26.8 | MIT | 甘特图组件 — [registry](https://registry.npmjs.org/@visactor/vtable-gantt/latest) |
| `@visactor/vtable-plugins` | 1.26.8 | MIT | 插件包：FilterPlugin、TableExportPlugin、HistoryPlugin 等；peer `@visactor/vtable@1.26.8` — [registry](https://registry.npmjs.org/@visactor/vtable-plugins/latest)、[插件文档](https://www.visactor.io/vtable/guide/plugin/filter) |
| `@visactor/vtable-export` | 1.26.8 | MIT | **官方文档已标注「不再维护」**，改用 `vtable-plugins` 的 `TableExportPlugin` — [registry](https://registry.npmjs.org/@visactor/vtable-export/latest)、[原文](https://github.com/VisActor/VTable/blob/develop/docs/assets/guide/zh/export/csv.md) |
| `@visactor/vtable-search` | 1.26.8 | MIT | 搜索工具（文档章节「搜索」）— [registry](https://registry.npmjs.org/@visactor/vtable-search/latest)、[文档](https://www.visactor.io/vtable/guide/search) |
| `@visactor/vtable-sheet` | 同期发布（1.26.x release notes 出现），版本未逐条核 | LICENSE 未核〔需自查〕 | 电子表格形态 VTable-Sheet — [Release v1.26.1](https://github.com/VisActor/VTable/releases/tag/v1.26.1)、[文档](https://www.visactor.io/vtable/guide/sheet/introduction) |

仓库包清单（README 官方列出 9 个 package：vtable / vtable-gantt / vtable-editors / vtable-plugins / vtable-export / vtable-search / react-vtable / vue-vtable / docs）— [README](https://github.com/VisActor/VTable/blob/develop/README.md)

## 2. License

全部 MIT，无附加商用限制条款。仓库 `LICENSE` = MIT，README 徽章标注 MIT，npm 各包 `license: "MIT"`。
来源：[LICENSE](https://github.com/VisActor/VTable/blob/main/LICENSE)、[README](https://github.com/VisActor/VTable/blob/develop/README.md)、[registry](https://registry.npmjs.org/@visactor/vtable/latest)
注意：MIT 只覆盖 VisActor 自己的包；`vtable-plugins`/`vtable-export` 还依赖第三方包 `exceljs@4.4.0`、`file-saver@2.0.5`（其 license 未在本次核查范围内〔需自查〕）—— [registry vtable-plugins](https://registry.npmjs.org/@visactor/vtable-plugins/latest)

## 3. 核心 API

### 3.1 构造方式（两种都是官方签名）

`new VTable.ListTable(options)`（container 写在 option 里）与 `new VTable.ListTable(container, options)` 都在 `.d.ts` 里重载；`container` 在 option 文档中标注「非必填，可放到初始化函数第一个参数」。
来源：[ListTable.d.ts@1.26.8](https://unpkg.com/@visactor/vtable@1.26.8/es/ListTable.d.ts)、[快速上手](https://www.visactor.io/vtable/guide/Getting_Started/Getting_Started)、[option 文档](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/table/listTable.md)

硬性约束：容器宽高**必须是整数**，否则 offsetWidth/clientWidth 取值有误差会出现表格抖动（可配 `tableSizeAntiJitter: true` 兜底）— [快速上手](https://www.visactor.io/vtable/guide/Getting_Started/Getting_Started)、[option](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/table/listTable.md)

### 3.2 options 真实字段（只列官方文档确有的）

数据/结构：`container`、`records`、`columns`、`transpose`、`showHeader`、`pagination`、`groupConfig`、`rowSeriesNumber`、`emptyTip`、`title`、`legends`、`axes`、`chartOption`
尺寸/布局：`widthMode`(standard/adaptive/autoWidth)、`heightMode`、`widthAdaptiveMode`、`heightAdaptiveMode`、`autoHeightInAdaptiveMode`、`autoWrapText`、`autoFillWidth`、`autoFillHeight`、`containerFit`、`maxCharactersNumber`(默认 200)、`limitMaxAutoWidth`(450)、`limitMinWidth`、`defaultRowHeight`(40)、`defaultHeaderRowHeight`、`defaultColWidth`(80)、`defaultHeaderColWidth`、`columnWidthConfig`、`customComputeRowHeight`
冻结：`frozenColCount`、`frozenRowCount`、`rightFrozenColCount`、`bottomFrozenRowCount`、`allowFrozenColCount`、`maxFrozenWidth`('80%')、`unfreezeAllOnExceedsMaxWidth`、`showFrozenIcon`、`scrollFrozenCols`/`scrollRightFrozenCols`/`maxRightFrozenWidth`/`scrollFrozenColsPassThroughToBody`
排序/筛选/聚合：`sortState`、`multipleSort`、`aggregation`、`showAggregationWhenEmpty`、`enableCheckboxCascade`、`enableHeaderCheckboxCascade`
编辑：`editor`、`headerEditor`、`editCellTrigger`('doubleclick'|'click'|'api'|'keydown')、`excelOptions.fillHandle`
交互：`hover`、`select`、`keyboardOptions`、`eventOptions`、`resize`、`dragOrder`、`disableInteraction`、`defaultCursor`、`overscrollBehavior`
样式/渲染：`theme`、`customRender`、`customMergeCell`、`customCellStyle`、`customCellStyleArrangement`、`menu`、`tooltip`、`animationAppear`、`formatCopyValue`、`canvasWidth`/`canvasHeight`/`maxCanvasWidth`/`maxCanvasHeight`、`canvas`/`viewBox`、`componentLayoutOrder`、`plugins`、`clearDOM`
ListTable 专有：`addRecordRule`、`hierarchyIndent`、`hierarchyExpandLevel`、`headerHierarchyType`、`headerExpandLevel`
来源：[公共主配置](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/common/option-secondary.md)、[ListTable 配置](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/table/listTable.md)

### 3.3 columns 字段（官方列配置文档）

`field`（必填；**支持 `['details','productName']` 多级路径**）、`title`、`width`（number / `'auto'` / `'20%'`）、`maxWidth`、`minWidth`、`headerType`(`text|link|image|video|audio|checkbox`)、`cellType`(`text|link|image|video|audio|sparkline|progressbar|chart|checkbox|radio|switch|button`)、`fieldFormat: (record)=>any`、`style`、`headerStyle`、`headerIcon`、`icon`、`sort`(boolean|fn)、`showSort`、`description`、`dropDownMenu`、`customRender`/`headerCustomRender`、`customLayout`/`headerCustomLayout`、`editor`/`headerEditor`、`aggregation`、`columns`（**嵌套即表头分组**）、`levelSpan`、`hide`、`hideColumnsSubHeader`、`disableHover`/`disableSelect`/`disableHeaderHover`/`disableHeaderSelect`、`dragHeader`、`columnWidthComputeMode`、`disableColumnResize`、`tree`，text 类型专有 `mergeCell`(boolean|fn)。
来源：[列基础配置](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/column/base-column-type.md)、[text 列](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/column/text-column-type.md)、[列类型清单](https://www.visactor.io/vtable/guide/table_type/List_table/list_table_define_and_generate)
**注意**：任务清单里的 `format`、`frozen` 在 ListTable 列文档中**不存在**——ListTable 用 `fieldFormat`；`format` 只出现在透视表 `indicators`（示例见 [主题文档](https://www.visactor.io/vtable/guide/theme_and_style/theme) 的 `format: value => ...`）；冻结是全局 `frozenColCount` 等，不是列级字段。`new VTable.ListTable(container, options)` 也确认存在（见 3.1）。

### 3.4 records 结构

- JSON 对象数组，每对象一行（字段名 = 列 `field`）；**也支持二维数组**，列写 `field: '0'`、`'1'`…；
- 多级对象：records 内嵌对象，列 `field: ['details','productName']`；
- 透视表用 `rowTree` / `columnTree` / `indicators`（聚合后的结果集）。
来源：[数据源](https://www.visactor.io/vtable/guide/data/data_format)

### 3.5 更新数据的方法（1.26.8 真实签名，均已核对 d.ts）

`setRecords(records, option?: {sortState?})`、`addRecord` / `addRecords`、`deleteRecords`、`updateRecords(records, recordIndexs?)`、`setRecordChildren`、`updateColumns` / `addColumns` / `deleteColumns`、`updateOption(options, updateConfig?)`、`updatePagination(pagination)`、`updateSortState`、`updateFilterRules` / `getFilteredRecords`、`changeCellValue` / `changeCellValues` / `changeCellValueByRecord`（+`BySource`、`changeCellValuesByRecords`）、`mergeCells` / `unmergeCells`、`startEditCell` / `completeEditCell` / `cancelEditCell`、`release()`。
`records` 是**只读**属性，直接赋值不会重绘，必须 `setRecords()`。
来源：[ListTable.d.ts](https://unpkg.com/@visactor/vtable@1.26.8/es/ListTable.d.ts)、[属性文档](https://github.com/VisActor/VTable/blob/develop/docs/assets/api/zh/properties.md)、[数据源文档](https://www.visactor.io/vtable/guide/data/data_format)
树形/分组结构下 `updateRecords` 的 `recordIndex` 需用 `getRecordIndexByCell(col,row)` 取，不要自己推层级索引（官方明确）— [数据源文档](https://www.visactor.io/vtable/guide/data/data_format)

## 4. 自定义渲染（三条真实路径）

1. **`customRender` / `headerCustomRender`（底层坐标式）**：回调用参数 `CustomRenderFunctionArg { row, col, table, value, dataValue, rect? }`，返回 `{ elements, expectedHeight, expectedWidth }`；elements 支持 `text` / `rect` / `circle` / `icon`（svg）等，坐标自己算。可全局配，也可按列配。
2. **`customLayout` / `headerCustomLayout`（推荐，盒模型/flex 布局）**：返回 `{ rootContainer, renderDefault }`；JSX 写法用 `VGroup/VText/VImage/VTag/VRadio/VCheckbox`，也可用 `createText/createGroup`（`import { createText, createGroup } from '@visactor/vtable/es/vrender'`）命令式创建。支持 flex 布局属性（display/flexDirection/flexWrap/justifyContent/alignItems/alignContent）与 `boundsPadding`。
3. **React 侧自定义单元格**：`<ListColumn>` 内放自定义组件并标 `role="custom-layout"`（表头用 `role="header-custom-layout"`），组件 props 自带 `{table,row,col,value,dataValue,rect}`；只能返回 react-vtable 的图元标签，DOM 组件需走 `attribute.react = {pointerEvents, container: table.bodyDomContainer, anchorType, element}` 或外层 `CustomComponent`。
来源：[customRender](https://www.visactor.io/vtable/guide/custom_define/custom_render)、[customLayout](https://www.visactor.io/vtable/guide/custom_define/custom_layout)、[CustomRenderFunctionArg](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/common/CustomRenderFunctionArg.md)、[React 自定义组件](https://www.visactor.io/vtable/guide/custom_define/react-custom-component)
**不存在名为 `CustomCell` 的 API/组件**（官方文档检索不到；React 侧的对应物是上面的 `role="custom-layout"` 与 `CustomComponent` 容器）〔需自查〕

## 5. 单元格编辑器

- 包：`@visactor/vtable-editors`（核心包已依赖，通常无需单独装，但官方教程仍要求安装一致版本）。
- **内置 4 个编辑器**：`InputEditor`、`TextAreaEditor`、`DateInputEditor`、`ListEditor({ values: ['女','男'] })`——官方原文「目前提供了四种编辑器类型」。文档示例里还注册了 `number-editor`，但该对象在片段中未定义（是自定义的）〔需自查〕。
- 注册：`VTable.register.editor('name-editor', inputEditor)`；列上 `editor: 'name-editor' | IEditor | ((args)=>{...})`，全局也可配 `editor`。
- 触发：双击（默认），可由 `editCellTrigger` 改为 click/api/keydown。
- 自定义编辑器实现 `IEditor`：`onStart({container, referencePosition, value, endEdit, col, row})`、`onEnd()`、`getValue()`、`isEditorElement?(target)`、`prepareEdit?(ctx)`、`validateValue?(newValue, oldValue, position, table)`。
- **校验**：`validateValue` 返回 `true/false` 或 `ValidateEnum.validateExit | invalidateExit | validateNotExit | invalidateNotExit`，也支持返回 Promise 做异步校验；未实现则默认不校验。
- **提交事件（真实事件名）**：`'change_cell_value'`（常量 `CHANGE_CELL_VALUE`），参数 `{ col, row, rawValue, currentValue, changedValue }`；批量聚合事件 `'change_cell_values'`（`CHANGE_CELL_VALUES`）；另有 `'checkbox_state_change'`/`'radio_state_change'`/`'switch_state_change'`/`'button_click'`、`COPY_DATA`、`PASTED_DATA`。`tableInstance.on('change_cell_value', cb)` 是官方示例写法。
- 编辑后取数：直接读 `tableInstance.records`。
- **`onChangeCellValue` 回调在官方 options/事件文档中未找到**〔需自查〕，请用 `change_cell_value` 事件或 `changeCellValue(col,row,value,workOnEditableCell?,triggerEvent?)`。
- 坑（官方自述）：内置编辑器基于浏览器原生 input，输入法/弹窗场景可能出问题；第三方 Select/DatePicker 的 portal 弹层要在 `isEditorElement` 里判断，否则会提前退出编辑。
来源：[编辑单元格](https://www.visactor.io/vtable/guide/edit/edit_cell)、[事件列表](https://github.com/VisActor/VTable/blob/develop/docs/assets/api/zh/event/event.md)、[编辑器类型定义](https://github.com/VisActor/VTable/blob/main/packages/vtable-editors/src/types.ts)

## 6. 大数据量 / 分页 / 服务端能力（架构关键）

**虚拟滚动机制**：底层 Canvas 渲染，「每次更新只会绘制可视区域内容」；`scrollToCell` 可编程滚动。
来源：[滚动](https://www.visactor.io/vtable/guide/interaction/scroll)

**官方性能口径**：README「Supports fast computation and rendering of millions of data points」、文档「VTable 支持百万级数据的秒级渲染」，官方 100 万行 Demo：`/vtable/demo/performance/100W`。**官方没有给出任何行数/列数/单元格数硬上限**〔需自查〕。
来源：[README](https://github.com/VisActor/VTable/blob/develop/README.md)、[VTable 介绍](https://www.visactor.io/vtable/guide/introduction)

**内置分页：有，但是前端分页**。配置 `pagination: { totalCount, perPageCount, currentPage }`（IPagination），实例方法 `updatePagination(pagination)`；导出文档明确「默认只导出表格当前页数据」→ 说明分页是对 `records` 的切片渲染。官方**没有**「向后端请求第 N 页」的配置项或数据协议。
来源：[ListTable 配置·pagination](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/table/listTable.md)、[ListTable.d.ts updatePagination](https://unpkg.com/@visactor/vtable@1.26.8/es/ListTable.d.ts)、[导出（当前页）](https://www.visactor.io/vtable/guide/plugin/table-export)

**服务端分页/懒加载：有"行级懒加载"能力，没有"分页协议"**。
- `VTable.data.CachedDataSource({ get(index){return Promise<record>}, length: 总条数 })`，挂载方式是**实例属性** `tableInstance.dataSource = dataSource`（不是 option.records）；`CachedDataSource.ofArray(array, dataConfig?, pagination?, columns?, ...)` 也可用。
- 官方明示局限：① 用 VTable 内部排序时需全量数据，异步失效，应后端排序、前端只显示图标；② `widthMode:'autoWidth'` 或列 `width:'auto'` 需遍历全列求宽，异步失效；③ 双击列边界自动调宽会拉全量数据，需 `resize.disableDblclickAutoResizeColWidth: true`；④ 表头右键会汇总所有选中 cells，需 `eventOptions.contextmenuReturnAllSelectedCells: false`。
- 结论（架构用）：**VTable 不提供数据层**。没有服务端行模型（无 AG Grid 那种 infinite/serverSide row model），也没有"总条数+页请求"的分页数据协议。要服务端分页，两种可行路线：**(A) 自己拉当前页 → `setRecords(pageRows)` + 自建分页器**（最贴文档、风险最低）；**(B) 数据量极大但要连续滚动 → `dataSource = CachedDataSource` 行级懒加载**（放弃内部排序/自动列宽）。内置 `pagination` 建议只用在全量数据已在内存的场景；把它和服务端页数据混用**是否兼容官方没有示例**〔需实测〕。
来源：[异步懒加载](https://www.visactor.io/vtable/guide/data/async_data)、[async-data demo（含 dataSource 挂载）](https://github.com/VisActor/VTable/blob/develop/docs/assets/demo/zh/performance/async-data.md)、[CachedDataSource.d.ts](https://unpkg.com/@visactor/vtable@1.26.8/es/data/CachedDataSource.d.ts)

## 7. 其他能力速查（均为文档确认）

| 能力 | 事实 | 来源 |
|---|---|---|
| 冻结行列 | `frozenColCount`/`frozenRowCount`/右冻结/底冻结；表头有图钉按钮（`showFrozenIcon`、`allowFrozenColCount`）；超宽自动解冻（`maxFrozenWidth` 默认 '80%'），可开冻结区内部横滚 `scrollFrozenCols` | [option-secondary](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/common/option-secondary.md) |
| 表头分组/折叠 | 列配置嵌套 `columns` 即分组，`hideColumnsSubHeader` 可隐藏子表头；`headerHierarchyType:'grid-tree'` + `headerExpandLevel` 做树形展开 | [列配置](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/column/base-column-type.md)、[ListTable](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/table/listTable.md) |
| 合并单元格 | API `mergeCells(startCol,startRow,endCol,endRow)` / `unmergeCells`；列级 `mergeCell: true` 自动合并相同相邻内容；`customMergeCell` 自定义（含 text/range/style） | [ListTable.d.ts](https://unpkg.com/@visactor/vtable@1.26.8/es/ListTable.d.ts)、[合并单元格](https://www.visactor.io/vtable/guide/basic_function/merge_cell) |
| tooltip | `tooltip: {renderMode:'html', isShowOverflowTextTooltip, overflowTextTooltipDisappearDelay, confine, position}`（**仅 html 实现完整，canvas 方案官方说未开发**） | [option-secondary](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/common/option-secondary.md) |
| 右键菜单 | 核心内置：`menu.contextMenuItems`（数组或函数）、`menu.renderMode`('html'/'canvas')、`menu.contextMenuWorkOnlyCell`；事件 `CONTEXTMENU_CELL`/`SHOW_MENU`/`HIDE_MENU`。另有 context-menu 插件 | [option-secondary](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/common/option-secondary.md)、[事件](https://github.com/VisActor/VTable/blob/develop/docs/assets/api/zh/event/event.md) |
| 主题 | 内置 `VTable.themes.DEFAULT/ARCO/DARK/BRIGHT/SIMPLIFY`，`themes.DEFAULT.extends({...})` 扩展，`themes.setDefaultTheme(theme)` 设全局默认（1.26.8 新增） | [主题](https://www.visactor.io/vtable/guide/theme_and_style/theme)、[Release](https://github.com/VisActor/VTable/releases/tag/v1.26.8) |
| 行高列宽 | `defaultRowHeight`/`defaultColWidth`/`heightMode`/`widthMode`；拖拽调整由 `resize.columnResizeMode`('all'/'none'/'header'/'body')、`rowResizeMode` 控制；`disableColumnResize` 列级禁用 | [option-secondary](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/common/option-secondary.md) |
| 排序 | **内置 UI 有**：列 `sort: true` 出排序图标，事件 `SORT_CLICK` → `AFTER_SORT`，`sortState` 可编程，`multipleSort` 多列排序；排序在前端对 records 完成 | [事件](https://github.com/VisActor/VTable/blob/develop/docs/assets/api/zh/event/event.md)、[数据源](https://www.visactor.io/vtable/guide/data/data_format) |
| 筛选 | **核心不内置筛选 UI**，需装 `@visactor/vtable-plugins` 的 `FilterPlugin`（按值/按条件、操作符、状态持久化）；仅支持 ListTable，不支持 PivotTable；核心侧另有 `updateFilterRules` 等 API | [筛选插件](https://www.visactor.io/vtable/guide/plugin/filter)、[ListTable.d.ts](https://unpkg.com/@visactor/vtable@1.26.8/es/ListTable.d.ts) |
| 键盘 | `keyboardOptions`：`copySelected`/`cutSelected`/`pasteValueToCell`/`selectAllOnCtrlA`/`moveFocusCellOnTab`/`editCellOnEnter`/`moveEditCellOnArrowKeys`/`shiftMultiSelect`/`ctrlMultiSelect`；撤销重做需 `HistoryPlugin` | [快捷键](https://www.visactor.io/vtable/guide/shortcut) |
| 行选择 | `select` 配置（highlightMode/headerSelectMode/disableSelect…）+ `rowSeriesNumber: {cellType:'checkbox'}` + `getCheckboxState`/`getCellCheckboxState`；`SELECTED_CELL`/`DRAG_SELECT_END` 事件 | [option-secondary](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/common/option-secondary.md)、[ListTable.d.ts](https://unpkg.com/@visactor/vtable@1.26.8/es/ListTable.d.ts) |
| 导出 | 用 `@visactor/vtable-plugins` 的 `TableExportPlugin`，给实例加 `exportToCsv`/`exportToExcel`；`exportAllData`、`formatExportOutput`、`formatExcelJSCell`、`fileName` 等；Excel 基于 exceljs，图片类型单元格可出图 | [导出插件](https://www.visactor.io/vtable/guide/plugin/table-export) |
| 搜索 | `@visactor/vtable-search` | [搜索](https://www.visactor.io/vtable/guide/search) |
| 按需加载 | `ListTableSimple`/`PivotTableSimple` + `registerTitle/registerTooltip/registerMenu/registerChartCell...` 瘦身 | [按需加载](https://www.visactor.io/vtable/guide/Load_on_Demand) |

## 8. 已知限制（可验证的部分）

1. **Canvas ⇒ 没有 DOM 文本**：无法用浏览器原生方式选中/复制单元格文字；复制走 `keyboardOptions.copySelected` + `COPY_DATA` 事件 + `formatCopyValue`。无障碍/ARIA/屏幕阅读器支持**官方文档未提及**〔需自查〕。移动端支持说明**未找到**〔需自查〕。— [键盘配置](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/common/option-secondary.md)、[快捷键](https://www.visactor.io/vtable/guide/shortcut)
2. **容器宽高必须整数**，否则抖动（有 `tableSizeAntiJitter` 兜底）。— [快速上手](https://www.visactor.io/vtable/guide/Getting_Started/Getting_Started)
3. **默认只显示前 200 字符**（`maxCharactersNumber` 默认 200），长文本需配 tooltip 或调参。— [option-secondary](https://github.com/VisActor/VTable/blob/develop/docs/assets/option/zh/common/option-secondary.md)
4. **`width:'auto'` / `widthMode:'autoWidth'` 需遍历整列数据**：大表首屏慢，且与异步懒加载互斥。— [异步懒加载·局限](https://www.visactor.io/vtable/guide/data/async_data)
5. **内部排序/筛选是前端行为**：异步/分页场景要后端排序，前端只留图标。— 同上
6. **编辑器是原生 input 封装**，输入法、第三方弹层（Select/DatePicker portal）需自行兜底 `isEditorElement`。— [编辑单元格](https://www.visactor.io/vtable/guide/edit/edit_cell)
7. **包体大**：`@visactor/vtable@1.26.8` unpackedSize 26.7 MB、2116 files；`vtable-plugins` 7.3 MB（带 exceljs/file-saver）。必须按需加载，否则首屏/构建体积有压力。— [registry](https://registry.npmjs.org/@visactor/vtable/latest)、[registry plugins](https://registry.npmjs.org/@visactor/vtable-plugins/latest)
8. **SSR**：官方只提供 Node 端「渲染成图片」（`mode:'node'` + `modeParams{createCanvas,createImageData,loadImage,Resvg}` + `getImageBuffer()`），**不是 HTML SSR**；在 Next/Nuxt 里需客户端挂载 + dynamic import〔推断〕。— [Node 服务端渲染](https://www.visactor.io/vtable/guide/Developer_Ecology/node)
9. **React 19 需要 reconciler 对齐**（18 用 `react-reconciler@0.29.x`，19 用 `0.33.x`），否则 custom-layout/DOM overlay 报 `ReactCurrentOwner` 之类错误。— [React-VTable 文档](https://www.visactor.io/vtable/guide/Developer_Ecology/react)
10. 编辑态性能/内存官方**没有给出量化数据**〔需自查〕；导出 Excel 官方注明「正在完善中，目前只支持文字类型单元格导出（后续支持迷你图等）」——注意该句写在已废弃的 vtable-export 文档里，插件版有 `skipImageExportCellType` 说明非文本默认导图。— [excel 导出](https://www.visactor.io/vtable/guide/export/excel)、[导出插件](https://www.visactor.io/vtable/guide/plugin/table-export)

## 9. 与 AG Grid / Handsontable 的定位差异（客观、简短）

- **VTable**：Canvas 渲染 + 多维分析基因（ListTable / PivotTable / PivotChart / Gantt / Calendar / Sheet），强在「百万行渲染 + 单元格内自由绘图（迷你图、进度条、图表、JSX 卡片）」。数据层、筛选 UI、导出、撤销重做都在插件/业务侧。
- **AG Grid**：DOM 渲染、有完整的数据层概念（client/server-side/infinite row model、分页协议、明细面板、集成图表），企业版收费；表格语义、无障碍、列能力（分组/聚合/服务端排序筛选）更完整，生态更工业化。
- **Handsontable**：DOM `<table>` 的 Excel 式电子表格，公式、快捷键、单元格类型、校验成熟，偏「在线 Excel」；不是多维透视分析表。
- 判断〔推断〕：要「分析型大表 + 高度定制单元格视觉」，VTable 合适；要「标准企业数据网格 + 服务端数据协议 + 无障碍合规」，AG Grid 更省事；要「在线 Excel 编辑」，Handsontable / VTable-Sheet 更贴。官方没有竞品对比文档，上述为基于文档能力的定位判断。

## 10. React + VTable 从后端分页接口加载数据（最小骨架）

思路（贴第 6 节结论）：**后端分页 + `setRecords` 换页 + 自建分页器**；不依赖内置 `pagination` 的切片行为。
数据更新方式：`@visactor/react-vtable` 的 props 变化会触发 `updateOption` 或 `setRecords`（官方原文），因此把 `records` 作为 React state 传入即可。

```tsx
// EmployeeTable.tsx —— React 18/19 + @visactor/react-vtable@1.26.8
import { useCallback, useEffect, useRef, useState } from 'react';
import { ListTable } from '@visactor/react-vtable';

type Row = { id: number; name: string; dept: string; score: number };
type Page = { records: Row[]; total: number };

const PAGE_SIZE = 50;

const columns = [
  { field: 'id', title: 'ID', width: 80, sort: true },
  { field: 'name', title: '姓名', width: 160 },
  { field: 'dept', title: '部门', width: 160 },
  { field: 'score', title: '评分', width: 120, fieldFormat: (r: Row) => r.score.toFixed(1) }
];

export default function EmployeeTable() {
  const [page, setPage] = useState(1);
  const [rows, setRows] = useState<Row[]>([]);
  const [total, setTotal] = useState(0);
  const tableRef = useRef<any>(null); // TODO 待核实：ref 指向 VTable 实例的确切类型（文档示例用 useRef(null)）

  const fetchPage = useCallback(async (p: number) => {
    const res = await fetch(`/api/employees?page=${p}&pageSize=${PAGE_SIZE}&sort=id&order=asc`);
    const data: Page = await res.json();
    setRows(data.records); // props 变更 → react-vtable 内部 setRecords
    setTotal(data.total);
  }, []);

  useEffect(() => { fetchPage(page); }, [page, fetchPage]);

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div>
      <ListTable
        ref={tableRef}
        height={600}
        option={{
          columns,
          records: rows,          // 当前页数据
          widthMode: 'standard',  // 不要用 autoWidth：会遍历全量求宽（见第 8 节）
          frozenColCount: 1,
          hover: { highlightMode: 'row' },
          keyboardOptions: { copySelected: true },
          emptyTip: true
          // 不用内置 pagination：它是前端切片，服务端分页场景由下方按钮控制
          // TODO 待核实：若想用内置分页条，需自行验证 pagination:{currentPage,perPageCount,totalCount} 与“records 只放当前页”是否兼容
        }}
        onReady={(instance: any, isInitial: boolean) => {
          console.log('vtable ready', isInitial, instance);
        }}
        // 编辑提交（可选）：React-VTable 未在 EventsProps 里暴露 change_cell_value，用原生 on 监听
        // TODO 待核实：onReady 里 instance.on('change_cell_value', cb) 的绑定时机
      />
      <div style={{ marginTop: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
        <button disabled={page <= 1} onClick={() => setPage(p => p - 1)}>上一页</button>
        <span>{page} / {pageCount}（共 {total} 条）</span>
        <button disabled={page >= pageCount} onClick={() => setPage(p => p + 1)}>下一页</button>
      </div>
    </div>
  );
}
```

若一定要「滚动式无限加载」（不是翻页），把上面换成行级懒加载：

```ts
import * as VTable from '@visactor/vtable';
// 挂到实例属性上，不是 option.records（官方 demo 写法）
const dataSource = new VTable.data.CachedDataSource({
  get(index) { return fetchBatch(Math.floor(index / 100) * 100, 100).then(list => list[index % 100]); },
  length: totalCount
});
// 注意：开启后内部排序、width:'auto' 自动列宽都会失效（官方明示）
(tableRef.current as any).dataSource = dataSource; // TODO 待核实：react-vtable 下拿实例并赋值的时机
```

## 11. 待核实清单（写架构文档前必须实测）

1. 内置 `pagination` 与「records 只放当前页」是否兼容；`updatePagination` 是否只改页脚状态不重发数据。
2. `change_cell_value` 在 React-VTable 下的绑定方式（EventsProps 未列该事件）；`onChangeCellValue` 是否存在（官方文档检索不到）。
3. 100 万行真实首屏时间、单元格编辑态的帧率/内存（官方无量化数据）。
4. 移动端触控支持程度、无障碍（ARIA）方案——官方文档均未覆盖。
5. `@visactor/vtable-sheet` 的版本、License 与成熟度（文档有 VTable-Sheet 章节、release notes 出现该包名，但未核包元数据）；日历图（docs 有 calendar 章节）是否已独立成 npm 包——**未找到独立包名，需自查**。
6. 文档读的是 `develop` 分支，个别新增能力（如 `themes.setDefaultTheme`）可能不在 1.26.8 之外的历史版本中；方法名已按 1.26.8 的 d.ts 核对。

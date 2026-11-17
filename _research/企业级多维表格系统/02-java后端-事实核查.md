# Java 后端技术选型事实核查（多维表格场景）

> 核查时间：2026-11-16（Asia/Shanghai）。规则：版本号只取自官方 release 页 / Maven Central / 官方文档；找不到就写「待确认」，不做记忆式填充。标注「推断」的内容不是官方原文。

---

## 0. 结论速览

| 维度 | 结论 |
| --- | --- |
| 运行时 | Java 25（LTS，2025-09 GA）+ Spring Boot 4.1.2（GA，要求 Java 17+，兼容至 Java 27） |
| 元数据库 | PostgreSQL 18（18.7 为当前 minor；19 仍是 RC，见 §2） |
| 缓存/协同 | Redis 8.10.3 |
| 动态字段存储 | 推荐「JSONB 单列 + 热点字段表达式索引/STORED 生成列」混合；纯 EAV 与纯动态加列都不适合千万行 |
| 协同 | 没有可用的 Yjs Java 绑定；现实选项是「前端 Yjs、后端只做持久化+广播」或自研 changeset/OT |
| 最大风险 | 协同一致性、千万行 × 动态字段的索引/分页、行级权限实现（RLS 连接池与 owner 绕过陷阱） |

---

## 1. 参考实现对比（技术栈 / License / 部署）

| 项目 | 技术栈（一句话） | License | 私有化 | 来源 |
| --- | --- | --- | --- | --- |
| APITable | 前端 TS（NextJS），后端 Java（Spring Boot）的 `backend-server` + Node.js/NestJS 的 `room-server`（OT 协同房间），MySQL + Redis + RabbitMQ + S3/MinIO | AGPL-3.0 | 支持（docker compose 一键） | [README](https://github.com/apitable/apitable/blob/develop/README.md)、[docker-compose.yaml](https://github.com/apitable/apitable/blob/develop/docker-compose.yaml)、[LICENSING.md](https://github.com/apitable/apitable/blob/develop/LICENSING.md) |
| Baserow | Django（Python）+ Vue.js，PostgreSQL；docker 单镜像可自托管 | MIT（open-core：非 premium/enterprise 部分） | 支持 | [README](https://github.com/baserow/baserow/blob/develop/README.md) |
| NocoDB | Node.js/TypeScript（NestJS 后端 + Vue 前端），可接 SQLite / PostgreSQL / MySQL 等 | **Sustainable Use License**（已不是 AGPL，注意商用限制） | 支持 | [README](https://github.com/nocodb/nocodb/blob/develop/README.md)、[packages/nocodb/package.json](https://github.com/nocodb/nocodb/blob/develop/packages/nocodb/package.json) |
| Teable | NestJS（TS）后端，PostgreSQL + Redis + S3；每个 Space 可绑定独立 PG 库（BYODB） | AGPL-3.0（Community Edition，`packages/` 为 MIT） | 支持（standalone / full） | [README](https://github.com/teableio/teable/blob/develop/README.md)、[自托管架构](https://help.teable.ai/en/deploy/architecture)、[BYODB](https://help.teable.ai/en/basic/admin-panel/database-tenant) |
| SeaTable | **数据以 JSON 文件存储**（每个 base 一个 JSON，载入内存；MariaDB 只存 operation log 与元数据，每 5 分钟落盘、24h 快照），dtable-web 是 Django，另有 dtable-server / dtable-db / dtable-events | 组件许可分裂：**dtable-server 专有许可**，dtable-web/dtable-events/thumbnail Apache-2.0，seaf-server AGPLv3 | 支持 | [架构文档](https://admin.seatable.com/introduction/architecture/)、[官方组件与 LICENSE 说明](https://github.com/seatable/seatable/blob/master/Readme.md) |

### 1.1 APITable 重点确认

- **后端是不是 Java/Spring Boot**：是。README 明示技术栈为 TypeScript（NextJS + NestJS）+ Java（Spring Boot）；仓库 `backend-server/` 是 Gradle 工程（`build.gradle`、`gradlew`）：[backend-server 目录](https://github.com/apitable/apitable/tree/develop/backend-server)。
- **房间/协同服务是什么语言**：Node.js/TypeScript。架构文档定义 `Room Server` 处理数据表的 `OTJSON` 操作、与 `Socket Server` 通过 gRPC 通信；`room-server` 容器环境变量是 `NODE_OPTIONS`、`INSTANCE_MAX_MEMORY`（[docker-compose.yaml](https://github.com/apitable/apitable/blob/develop/docker-compose.yaml)）。Socket 层用 WebSocket 长连接（架构文档）。
  - 注：架构文档在上游 `develop` 已不在该路径，引用的是 fork 中的副本：[architecute-overview.md](https://raw.githubusercontent.com/siri-ming/apitable/refs/heads/develop/docs/contribute/architecute-overview.md)（文件名拼写 `architecute` 为原文）。
- **数据库**：MySQL（compose 中 `mysql` 服务，`utf8mb4`），配 Redis（会话/热点）、RabbitMQ、MinIO（S3）。架构文档列 `MySQL` 存数据表/记录/视图，`Redis` 存缓存，`S3` 存附件。
- **License**：AGPL-3.0（README 徽章 + 许可段；仓库根 `LICENSE`）。企业版另有托管/商业授权。
- **私有化部署**：支持，`curl https://apitable.github.io/install.sh | bash` 或直连 docker compose；README 另提供 `apitable/all-in-one` 镜像（官方明说仅供 demo，不建议生产）。
- **协同/操作日志设计（文档级）**：README 写「数据库原生架构：Changeset / Operation / Action / Snapshot」+「Operational Transformation (OT) 算法」+「10 万+ 行实时协同」；架构文档写房间服务处理 `OTJSON` 操作、经 gRPC 与 socket server 通信。
  - 更细的 changeset 增量落库格式、action 表结构，README/架构文档都没有展开 → 若要抄它的设计需读源码，**属推断范围**，不要当文档引用。
  - 可借鉴的核心思路（推断，基于上述文档 + 常规做法）：变更以 changeset（操作数组）为最小单位；房间内存持有当前快照，操作按 revision 追加到操作日志并广播；新加入者先拉快照再重放增量；定期把内存快照压实成新的快照版本。

---

## 2. 版本现状与推荐矩阵（截至 2026-11-16）

### 2.1 Java

- **Java 25（LTS，2025-09 GA）** 为当前最新 LTS，Oracle 免费许可覆盖；Java 21（LTS，2023-09）仍受支持，Premier 至 2028-09。
- LTS 序列 8/11/17/21/25，**下一个 LTS 是 Java 29（2027-09）**；Java 26（2026-03）/ 27（2026-09）均为非 LTS。

来源：[Oracle Java SE Support Roadmap（Updated October 20, 2026）](https://www.oracle.com/java/technologies/java-se-support-roadmap.html)。

### 2.2 Spring 家族（均来自 Spring Boot 4.1.2 的 BOM 与官方 requirements 页）

| 组件 | 版本 | 来源 |
| --- | --- | --- |
| **Spring Boot** | **4.1.2**（`current=true`，GENERAL_AVAILABILITY）；4.2.0-RC2 为 PRERELEASE | [api.spring.io releases](https://api.spring.io/projects/spring-boot/releases)、[Maven Central metadata](https://repo1.maven.org/maven2/org/springframework/boot/spring-boot/maven-metadata.xml) |
| Spring Boot 4.1.2 的硬性要求 | **至少 Java 17，兼容到 Java 27（含）**，要求 Spring Framework **7.0.10 或以上** | [System Requirements](https://docs.spring.io/spring-boot/system-requirements.html) |
| Spring Framework | **7.0.10**（BOM `spring-framework.version`；7.1.0-RC2 为预发布，不是 GA） | [BOM 4.1.2 pom](https://repo1.maven.org/maven2/org/springframework/boot/spring-boot-dependencies/4.1.2/spring-boot-dependencies-4.1.2.pom)、[spring-core metadata](https://repo1.maven.org/maven2/org/springframework/spring-core/maven-metadata.xml) |
| Spring Security | **7.1.2**（BOM `spring-security.version`） | 同上 BOM |
| Tomcat | 11.0.27（BOM） | 同上 BOM |
| HikariCP | 7.0.2（BOM） | 同上 BOM |
| PostgreSQL JDBC | 42.7.14（BOM） | 同上 BOM |
| jOOQ | 3.21.9（BOM） | 同上 BOM |
| Flyway | 12.4.0（BOM，Postgres 走 `flyway-database-postgresql` 模块） | 同上 BOM |
| Liquibase | 5.0.4（BOM） | 同上 BOM |
| Micrometer / Micrometer Tracing | 1.17.2 / 1.7.2（BOM） | 同上 BOM |
| OpenTelemetry（API/SDK 依赖管理） | 1.62.0（BOM） | 同上 BOM |
| Lettuce / Netty | 7.5.2.RELEASE / 4.2.19.Final（BOM） | 同上 BOM |
| Jackson | 3.1.7（BOM；Jackson 2 线仍并行管理 2.21.7） | 同上 BOM |
| RSocket | 1.1.5（BOM） | 同上 BOM |

**推荐矩阵（供 Lead 写方案）**：Java 25 LTS + Spring Boot 4.1.2 + Spring Framework 7.0.10 + Spring Security 7.1.2 + PostgreSQL 18.7 + Redis 8.10.3 + PostgreSQL JDBC 42.7.14 + Flyway 12.4.0。Boot 4.2.0 未 GA，不用于生产基线（4.2.0-RC2 已在里程碑仓库）。

其他库（Maven Central `latest`，逐条核对）：

| 库 | 最新发布 | 备注 |
| --- | --- | --- |
| Apache Calcite core | 1.42.0（2026-05-31） | [metadata](https://repo1.maven.org/maven2/org/apache/calcite/calcite-core/maven-metadata.xml) |
| Aviator | 5.4.4（2026-07-20） | [metadata](https://repo1.maven.org/maven2/com/googlecode/aviator/aviator/maven-metadata.xml) |
| QLExpress | 3.3.4（**最后更新 2024-09-27**） | [metadata](https://repo1.maven.org/maven2/com/alibaba/QLExpress/maven-metadata.xml) |
| Apache POI（poi-ooxml） | 6.0.0（2026-10-22） | [metadata](https://repo1.maven.org/maven2/org/apache/poi/poi-ooxml/maven-metadata.xml) |
| FastExcel（cn.idev.excel） | 1.3.0（2025-08-25） | [metadata](https://repo1.maven.org/maven2/cn/idev/excel/fastexcel/maven-metadata.xml) |
| 阿里 EasyExcel | 4.0.3（**最后更新 2024-09-11**） | [metadata](https://repo1.maven.org/maven2/com/alibaba/easyexcel/maven-metadata.xml) |
| Redisson | 4.8.0（2026-10-02） | [metadata](https://repo1.maven.org/maven2/org/redisson/redisson/maven-metadata.xml) |

### 2.3 PostgreSQL

| 事实 | 值 | 来源 |
| --- | --- | --- |
| 当前稳定大版本 | **18**；当前 minor **18.7**；18 首版 2025-09-25，支持到 2030-11-14 | [Versioning Policy](https://www.postgresql.org/support/versioning/) |
| 19 状态 | **仍在 RC**：2026-11-12 发布「18.7 / … / 19 RC 2」 | [官方 news](https://www.postgresql.org/about/news/postgresql-187-1712-1616-1520-1425-and-19-rc-2-released-3442/) |
| 与多维表格相关的 18 新特性 | 虚拟生成列（virtual）成为默认、生成列可逻辑复制（仅 STORED）、GIN 索引支持并行创建、AI/O 子系统、B-tree skip scan、`uuidv7()`、`jsonb` null 转标量类型与 `jsonb_strip_nulls` 增强 | [Release 18](https://www.postgresql.org/docs/18/release-18.html)、[Generated Columns](https://www.postgresql.org/docs/18/ddl-generated-columns.html) |

### 2.4 Redis

- 最新稳定 release：**8.10.3**（2026-10-26，非 prerelease；含集群总线 `PUBLISH` 的安全修复），[GitHub release](https://github.com/redis/redis/releases/tag/8.10.3)。

---

## 3. 存储三方案：JSONB / EAV / 动态加列

### 3.1 对比

| 维度 | JSONB 单列 | EAV（行列转置） | 动态加列（每表物理列） |
| --- | --- | --- | --- |
| 加字段 | 零 DDL，改元数据 | 零 DDL | `ALTER TABLE ADD COLUMN`（PG 11+ 无默认值时仅改 catalog，很快） |
| 等值/包含过滤 | GIN 可用（`@>`、`?`、`@?`、`@@`） | 需要按 field_id 自连接，字段多时 join 爆炸 | 普通 B-tree 最优 |
| 范围过滤/排序 | **GIN 不支持范围**；需表达式索引或 STORED 生成列 | 每个 field 行有值列可索引，但组合过滤要多次 join | 最优（原生索引） |
| 千万行规模 | 行数不膨胀（1 表 = 1 行/记录），GIN 体积大、写放大 | **行数 = 记录 × 字段**（100 字段 × 1000 万 = 10 亿行级），聚合/分页代价高 | 行数不膨胀、查询最好；DDL 与索引数量随字段爆炸，跨表统一查询难 |
| 典型使用者 | 适合字段稀疏、以视图筛选为主的场景 | 传统 EAV 系统 | Teable / Baserow 类「真 PG 表」路线（Teable 官方措辞「real PostgreSQL underneath」，字段落为物理列属**推断**） |

**倾向**：主存储用 JSONB（元数据驱动、零 DDL），对高频筛选/排序字段建**表达式索引**或 **STORED 生成列**；单表字段数固定且查询极重的场景再考虑动态加列（但每表 DDL 与迁移会成为运维负担）。EAV 在千万行 × 几十字段时基本不可用。

### 3.2 可执行 DDL（方案 A：JSONB 单列）

```sql
CREATE TABLE records (
  tbl_id      bigint      NOT NULL,
  record_id   bigint      GENERATED ALWAYS AS IDENTITY,
  data        jsonb       NOT NULL DEFAULT '{}'::jsonb,
  created_at  timestamptz NOT NULL DEFAULT now(),
  deleted_at  timestamptz,
  PRIMARY KEY (tbl_id, record_id)
);

-- 整文档包含查询：jsonb_path_ops 更小更快，但不支持 ?/|?/&?（键存在）与空对象
CREATE INDEX idx_records_data_gin ON records USING GIN (data jsonb_path_ops);

-- 热点字段：表达式 B-tree（等值 + 范围 + 排序都能用）
CREATE INDEX idx_records_f_status ON records ((data->>'status')) WHERE deleted_at IS NULL;
CREATE INDEX idx_records_f_due    ON records (((data->>'due')::timestamptz)) WHERE deleted_at IS NULL;

-- 10 万行以上大表可分区（按 tbl_id 或时间），配合局部索引
-- 包含查询写法（走 GIN）
SELECT * FROM records
WHERE tbl_id = 42 AND data @> '{"status":"进行中"}' AND deleted_at IS NULL
ORDER BY record_id LIMIT 100;
```

GIN 行为要点（官方文档原文归纳，[jsonb 索引](https://www.postgresql.org/docs/18/datatype-json.html#JSON-INDEXING)）：
- 默认 `jsonb_ops` 支持 `?`、`?|`、`?&`、`@>`、`@?`、`@@`；`jsonb_path_ops` **只支持** `@>`、`@?`、`@@`。
- `jsonb_path_ops` 索引通常显著更小、命中更精确，但对 `{"a": {}}` 这类无值结构不产生索引项，这类查询会退化成全索引扫描。
- 表达式索引可只索引 `data->'tags'` 等子树，比整文档 GIN 小且快（官方示例）。
- 单独对 `jsonb` 建 btree/hash 只在整文档等值时有用，不适合字段级过滤。
- JSONB 更新是整行行锁（官方「Designing JSON Documents」），字段越多的表写冲突概率越高 → 大体量表格应控制单行 JSON 大小。

### 3.3 方案 B / C 的 DDL 骨架

```sql
-- B：EAV
CREATE TABLE fields (
  field_id bigint PRIMARY KEY, tbl_id bigint NOT NULL,
  name text NOT NULL, type text NOT NULL
);
CREATE TABLE cell_values (
  record_id bigint NOT NULL, field_id bigint NOT NULL,
  val_text text, val_num numeric, val_ts timestamptz,
  PRIMARY KEY (record_id, field_id)
);
CREATE INDEX idx_cv_num ON cell_values (field_id, val_num);

-- C：动态加列（每张数据表一条物理表，字段 = 列）
CREATE TABLE t_42 (
  record_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  c_1001 text,           -- 字段 1001
  c_1002 numeric,        -- 字段 1002
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX CONCURRENTLY idx_t42_c1002 ON t_42 (c_1002);
```

注意：`ALTER TABLE ... ADD COLUMN` 无默认值时 PG 11+ 只改 catalog（快）；带易变默认值会重写全表。建索引用 `CONCURRENTLY` 避免长锁。虚拟生成列（PG 18 默认）不能引用用户函数/类型，且**逻辑复制只支持 STORED 生成列**（[Generated Columns](https://www.postgresql.org/docs/18/ddl-generated-columns.html)）——要做生成列 + CDC，务必显式写 `STORED`。

---

## 4. 筛选 DSL → SQL 的编译

| 方案 | 能力 | 代价 |
| --- | --- | --- |
| MyBatis 动态 SQL | 团队熟悉、SQL 可控 | 字符串拼装难做类型安全与嵌套布尔表达式；动态字段名必须白名单，否则注入风险 |
| jOOQ（BOM 3.21.9） | 类型安全的 DSL，能精确表达 `@>`、`->>`、表达式索引写法，可拼任意复杂条件 | 代码生成对「动态表/动态字段」不友好，通常用 `DSL.table("records")` 无 schema 模式，失去部分类型安全 |
| Spring Data JPA Specification | 与实体模型绑定 | 动态 JSONB 字段/表达式索引不自然，容易生成次优 SQL；不推荐做核心查询层 |
| **自研 AST + 编译到 jOOQ/参数化 SQL** | 筛选 DSL（and/or/not/字段比较/关联）→ AST → SQL 片段 + 参数，可白名单字段、可缓存计划、可做权限注入 | 需要自己维护类型系统与 NULL/类型转换语义，测试量大 |

**Apache Calcite 的定位与代价**：Calcite 是「动态数据管理框架」，提供 SQL 解析/校验/优化与 adapter 框架，本身不存数据（[calcite.apache.org](https://calcite.apache.org/)；其官方描述为 query planning/optimization 框架）。用它做「多维表格筛选 DSL → SQL」的代价（推断）：
- 要先把动态表结构映射成 Calcite 的 `RelDataType`/`Table`（动态 schema 是它最不擅长的部分）；
- 多一层优化器，最终还是要落到 PG SQL 或自身执行器，等于维护两套计划；
- 适合的是「用户写 SQL / 跨数据源联邦查询」场景，不适合编译一个封闭的筛选 DSL。
- 结论：**不用 Calcite 做筛选编译**；自研 AST + jOOQ/参数化 SQL 更直接。Calcite 更适合后面「公式/查询联邦」这类重场景（见 §5）。

---

## 5. 公式引擎

| 方案 | 最新版本 | 能力 | 风险 |
| --- | --- | --- | --- |
| Aviator | 5.4.4 | 表达式编译成字节码，性能好，支持自定义函数/变量 | 无默认沙箱，需自行白名单函数与变量；语法是类 Java 表达式，非电子表格语法 |
| QLExpress | 3.3.4（2024-09 后无新版本） | 阿里系脚本引擎，安全控制（黑/白名单、超时）较完善 | 维护活跃度低；语法与表格公式差异大 |
| Jakarta EL | 规范（实现随容器） | 简单表达式，易集成 | 能力弱（无数组/聚合/跨表引用），不适合公式语言 |
| GraalJS | GraalVM 25 线 | 完整 JS 语义，生态好，可做沙箱（allowlist） | 重（内存/启动），JDK 25 上跑 JS 需额外依赖；沙箱配置易出错 |
| Apache Calcite | 1.42.0 | 可做表达式求值与 SQL 计划 | 为 SQL 设计，不是表格公式语言；学习成本高 |
| 自研 Pratt 解析器 | — | 完全可控的 AST、易接依赖图与增量求值、可精确对齐 Airtable/飞书公式语义 | 工作量最大（解析/类型/函数库/错误定位） |

**推荐倾向（推断）**：自研「Pratt 解析 + AST 求值」或「AST → Aviator 表达式」两层：解析与语义自己控，求值借 Aviator 的编译性能。

**依赖图与循环引用检测（公开实现思路）**：
- 公式解析成 AST 后提取单元格/字段引用；以「单元格（record, field）」为节点建有向图，按拓扑序求值；用 DFS 三色标记或 Tarjan 找强连通分量检测环 → 报「循环引用」并把涉及单元格置错误值。
- 参考实现：HyperFormula（表格公式引擎，含依赖图与循环引用处理，[github.com/handsontable/hyperformula](https://github.com/handsontable/hyperformula)）；Univer 表格引擎（[github.com/dream-num/univer](https://github.com/dream-num/univer)）。二者都是 JS/TS，需读源码移植，**具体算法属推断**。
- 产品语义参考 Excel 官方说明：[Remove or allow a circular reference in Excel](https://support.microsoft.com/en-us/office/remove-or-allow-a-circular-reference-in-excel-8540bd0f-6e97-4483-bcf7-1b49cd50d123)。
- 千万行数据上不要做全表依赖图：以「字段级公式 + 按需计算/物化」为主，跨行聚合（rollup）走 SQL 而非图求值。

---

## 6. 实时协同

### 6.1 Yjs / y-crdt 的 Java 绑定：**没有**

- y-crdt 官方仓库只提供 `yrs`（Rust 核心）、`yffi`（C FFI）、`ywasm`（WASM）；社区绑定列表为 pycrdt（Python）、yrb（Ruby）、yr（R）、ydotnet（.NET）、yswift（Swift）、**ykt（Kotlin）**，**没有 Java/JVM 官方绑定**：[y-crdt README](https://github.com/y-crdt/y-crdt/blob/main/README.md)。
- 可绕的路线（按成熟度排序，均为推断）：
  1. 前端用 Yjs + y-websocket，后端只做「消息转发 + 快照持久化」，不做 CRDT 合并（Java 侧最省事，但服务端无法校验/查询文档内结构）；
  2. 引入 `ykt`（Kotlin 绑定）在 JVM 内跑，Java 可调用 Kotlin 类，但社区规模小，**成熟度待确认**；
  3. JNI/JNA 包 `yffi`（自己封装生命周期与线程安全，工作量大）；
  4. 自研 changeset/OT（APITable 路线）。
- 查证方式：GitHub 搜索「yjs java binding」返回 **0 个仓库**（2026-11-16 查询）。

### 6.2 APITable 的 changeset / OT 思路（文档可见部分）

- OT 算法 + `OTJSON` 操作；`Changeset / Operation / Action / Snapshot` 分层；房间服务持有数据表操作，socket 层与房间服务经 gRPC 通信（[架构文档副本](https://raw.githubusercontent.com/siri-ming/apitable/refs/heads/develop/docs/contribute/architecute-overview.md)、[README](https://github.com/apitable/apitable/blob/develop/README.md)）。
- 对「操作日志」的直接证据：README 的架构描述 + 房间服务职责；**具体的 changeset 表结构与 rev 机制属推断**（需读 `packages/` 源码）。

### 6.3 Java 侧 WebSocket 与多实例广播

| 能力 | 方案 | 备注 |
| --- | --- | --- |
| WebSocket | Spring `spring-boot-starter-websocket`：原生 `WebSocketHandler` 或 STOMP（[Spring Framework WebSocket 参考](https://docs.spring.io/spring-framework/reference/web/websocket.html)、[STOMP](https://docs.spring.io/spring-framework/reference/web/websocket/stomp.html)） | 与 Spring Security / 会话集成最顺；STOMP 适合 topic 订阅模型 |
| 高性能网关 | Netty 4.2.19（BOM 管理） | 自己写协议与心跳，控制力强、成本高 |
| RSocket | RSocket 1.1.5（BOM 管理），Boot 有 `spring-boot-starter-rsocket` | 双向流语义好，生态与前端支持弱于原生 WebSocket |
| 多实例广播 | Redis Pub/Sub（Spring Data Redis `RedisMessageListenerContainer`）、Redisson 4.8.0（`RTopic`）、Redis Streams、Kafka | **Pub/Sub 不持久**：实例掉线期间消息丢失，重连后必须靠「快照 + 增量补齐」而不是广播补发 |

---

## 7. 权限

### 7.1 认证/授权栈

- Spring Security **7.1.2**（Boot 4.1.2 BOM）。JWT 走 `spring-boot-starter-oauth2-resource-server`（Bearer Token + `JwtDecoder`），OIDC 登录走 `oauth2-client`，SAML2 也有 starter；参考 [OAuth2 Resource Server / JWT 文档](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)。企业内网常见组合：外部 IdP（Keycloak / 飞书 / 企业微信）出 OIDC/JWT → 后端只做资源服务器 + 本地 RBAC/ACL 表。

### 7.2 行级权限：Postgres 原生 RLS vs 应用层查询改写

| 维度 | 原生 RLS | 应用层改写 |
| --- | --- | --- |
| 实现 | `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY`，按 `current_setting('app.user_id')` 之类过滤 | 在 §4 的 AST→SQL 编译层注入 `where` 条件 |
| 强制力 | 数据库层兜底，任何 SQL 都受约束 | 依赖所有查询都走编译层，漏一处即越权 |
| 性能 | 每行求值策略表达式；复杂/跨表策略会影响计划 | 与业务条件一起优化，通常更好 |
| 连接池 | 必须每请求/每事务 `SET LOCAL app.user_id = ...`，且保持在同一连接同一事务；用 pgbouncer 时需 transaction pooling 并确保不串会话 | 无此问题 |
| 陷阱（官方明确） | **表 owner 默认绕过 RLS**（需 `ALTER TABLE ... FORCE ROW LEVEL SECURITY`）；**超级用户与 `BYPASSRLS` 角色永远绕过**；参照完整性检查永远绕过 RLS；`row_security=off` 会让被过滤的查询直接报错 | 需要在所有入口（API、导出、定时任务）统一注入 |

官方依据：[Row Security Policies（PG 18）](https://www.postgresql.org/docs/18/ddl-rowsecurity.html)（owner 绕过、`FORCE ROW LEVEL SECURITY`、BYPASSRLS、参照完整性绕过、permissive 用 OR / restrictive 用 AND 等均为原文）。
`SET LOCAL` 的事务作用域见 [SET](https://www.postgresql.org/docs/18/sql-set.html)；「每请求 SET LOCAL + 连接池归还前 reset」属工程实践（推断），官方没有专门的连接池章节。

**取舍建议（推断）**：内网单租户、权限模型稳定 → RLS 做兜底 + 应用层条件做优化；多租户/复杂字段级权限 → 应用层改写为主，RLS 只在「数据表物理隔离」场景用；两者叠加时务必用非 owner 角色连接并 `FORCE RLS`。

---

## 8. 导入导出（百万行级）

| 方案 | 版本 | 内存/性能特征 |
| --- | --- | --- |
| EasyExcel | 4.0.3（2024-09 后停更） | SAX 流式读写，内存占用低；社区已停止更新，新项目不选 |
| FastExcel（cn.idev.excel） | 1.3.0 | EasyExcel 作者的后续版本（同包结构迁移），流式 + 性能优化；迁移成本低 |
| Apache POI | 6.0.0 | `XSSFWorkbook` 全内存（大文件 OOM）；`SXSSFWorkbook` 滑动窗口流式写、`XSSFReader`/事件 API 流式读；功能最全但 API 重 |
| PostgreSQL COPY | PG 18 内置 | **最快**的批量导入路径：`COPY ... FROM STDIN`（CSV/文本），服务端解析；百万行通常几十秒级；PG JDBC 可用 `CopyManager` 流式写入（JDBC 侧细节**待确认**具体 API 文档链接）。导出同理 `COPY ... TO STDOUT` |

补充（推断）：Excel 写 xlsx 单文件有行数上限（1,048,576 行，Excel 规格），百万行导出要么拆 sheet/拆文件，要么只导出 CSV；导入大文件应在后端做「流式解析 → 分批 COPY/多值 INSERT」，不要先全量读进内存。

---

## 9. 可观测与运维

- **Metrics/Tracing**：Spring Boot 4.1.2 BOM 管理 Micrometer 1.17.2 + Micrometer Tracing 1.7.2 + OpenTelemetry 1.62.0；Boot 4.1 文档里存在 `spring-boot-opentelemetry` 与 `spring-boot-micrometer-tracing-opentelemetry` 自动配置模块（[Boot 4.1.2 文档自动配置列表](https://docs.spring.io/spring-boot/appendix/auto-configuration-classes/spring-boot-opentelemetry.html)）。工程做法仍是：`spring-boot-starter-actuator` + Prometheus registry + OTLP exporter 推 Tempo/Jaeger。
- **数据库迁移**：Flyway 12.4.0（PG 需 `flyway-database-postgresql`，BOM 已含）；Liquibase 5.0.4。官方站点：[flywaydb.org](https://documentation.red-gate.com/flyway)、[liquibase.com](https://www.liquibase.com/)。Flyway 10 起拆数据库模块、社区版与商业版功能分层，选型时核对团队许可需求（版本事实来自 BOM；许可分层细节**待确认**）。

---

## 10. 风险清单（给 Lead 的方案输入）

1. **协同一致性是最大不确定性**：Yjs 无 Java 绑定（官方列表可查），若要求服务端权威合并，只能 JNI/Rust 封装、Kotlin 绑定或自研 OT；任一选择都要预留 2-4 人月与一致性测试成本。
2. **千万行 × 动态字段的索引与分页**：JSONB GIN 只覆盖等值与包含，范围过滤/排序必须靠表达式索引或 STORED 生成列；字段一多，索引数量与 GIN 写放大都会成为瓶颈；偏移分页在千万行上不可用（应改 keyset 分页，属推断/通用实践）。
3. **行级权限容易「配置正确但实际越权」**：RLS 的表 owner 绕过、`BYPASSRLS`、连接池串会话是本项目最容易踩的坑；建议以应用层查询改写为主，RLS 只做兜底并配集成测试。
4. **License 风险**：APITable 为 AGPL-3.0（二次分发/网络服务有传染性）；SeaTable 的 `dtable-server` 是专有许可、不是开源件；NocoDB 已从 AGPL 改为 Sustainable Use License，不能当 AGPL 用。

## 11. 待确认项（不猜）

- Spring Boot 4.1.2 的具体 GA 发布日期（api.spring.io 未给日期，只有 `current=true`）。
- GraalVM Polyglot（GraalJS）Maven Central 上与 GraalVM 发行版对齐的准确版本号。
- `ykt`（Kotlin Yjs 绑定）的成熟度与维护活跃度。
- PostgreSQL 19 的 GA 日期（当前 19 RC2，2026-11-12）。
- Flyway 12 的社区版/商业版功能边界。
- 百万行 Excel 导入时 PG JDBC `CopyManager` 的官方文档链接。

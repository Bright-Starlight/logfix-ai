# Feature Specification: 数据库注释规范

**Feature Branch**: `005-db-comment-standards`
**Created**: 2026-04-12
**Status**: Draft
**Input**: User description: "数据表必须要有表注释及字段注释；id使用long类型禁止使用uuid"

> 生成内容的正文必须使用中文；标题保留英文标签仅用于模板标准化。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 所有数据表必须包含表注释 (Priority: P1)

数据库中的每个数据表都必须包含表注释（COMMENT），用于描述表的用途、适用范围和业务含义。表注释是数据库文档化的基础，帮助开发者和运维人员快速理解表的作用。

**Why this priority**: 没有表注释的数据库表难以维护，长期积累会导致"表名即文档"的混乱，增加新人上手难度和系统维护成本。

**Independent Test**: 可以通过数据库元数据查询验证所有表的 COMMENT 是否存在且非空。

**Acceptance Scenarios**:

1. **Given** 任意数据表，**When** 表被创建或修改时，**Then** 必须同时指定 COMMENT，且 COMMENT 内容不为空
2. **Given** 已有表缺少注释，**When** 执行数据库迁移脚本时，**Then** 迁移脚本应包含补全注释的 ALTER 语句
3. **Given** 存在没有注释的表，**Then** CI/CD 流程应检测到并阻止合并

---

### User Story 2 - 所有字段必须包含字段注释 (Priority: P1)

数据库中的每个字段都必须包含字段注释（COMMENT），用于描述字段的含义、取值范围、单位、关联关系等。字段注释是理解数据模型的关键。

**Why this priority**: 没有字段注释的表会导致字段用途模糊，尤其是时间戳、状态码、外键等字段，新开发者难以推断其真实含义。

**Independent Test**: 可以通过数据库元数据查询验证所有字段的 COMMENT 是否存在且非空。

**Acceptance Scenarios**:

1. **Given** 任意数据表的任意字段，**When** 字段被创建或修改时，**Then** 必须同时指定 COMMENT，且 COMMENT 内容不为空
2. **Given** 已有字段缺少注释，**When** 执行数据库迁移脚本时，**Then** 迁移脚本应包含补全注释的 ALTER 语句
3. **Given** 存在没有注释的字段，**Then** CI/CD 流程应检测到并阻止合并

---

### User Story 3 - 主键ID必须使用Long类型禁止UUID (Priority: P1)

所有表的主键 ID 必须使用 Long 类型（Java）/ bigint（数据库），严格禁止使用 UUID 作为主键类型。

**Why this priority**: UUID 作为主键会导致索引体积膨胀、写入放大、页分裂、性能下降；Long 类型主键更紧凑、顺序性好、利于分库分表。

**Independent Test**: 可以通过数据库元数据查询验证所有主键列的类型是否为 bigint/int/bigserial 等整数类型，而非 uuid/varchar 等字符串类型。

**Acceptance Scenarios**:

1. **Given** 任意新建数据表，**When** 定义主键时，**Then** 主键类型必须为 Long/bigint，禁止使用 UUID/varchar
2. **Given** 已有表使用 UUID 作为主键，**Then** 迁移计划应包含将 UUID 主键迁移为 Long 主键的方案
3. **Given** 存在 UUID 主键的表，**Then** CI/CD 流程应检测到并阻止合并

---

### User Story 4 - 迁移脚本自动检查注释完整性 (Priority: P2)

数据库迁移脚本（Liquibase/Flyway）在执行前自动检查表和字段的注释完整性，对缺少注释的变更进行阻止或警告。

**Why this priority**: 人工检查容易遗漏，自动化检查可以确保规范被无例外地执行。

**Independent Test**: 可以通过执行一个缺少注释的迁移脚本来验证检查机制是否生效。

**Acceptance Scenarios**:

1. **Given** 包含建表语句的迁移脚本，**When** 执行迁移时，**Then** 系统自动检查表注释和字段注释是否存在，缺少则报错退出
2. **Given** 修改现有表添加新字段，**When** 新字段没有注释，**Then** 迁移脚本被拒绝执行
3. **Given** 修改现有表修改字段，**When** 保留原有注释同时更新字段，**Then** 迁移正常执行

---

### User Story 5 - 数据库文档自动生成 (Priority: P3)

基于数据库注释自动生成数据库文档（HTML/Markdown 格式），包含所有表、字段、注释、类型、约束等信息的完整文档。

**Why this priority**: 减少人工维护文档的工作量，确保文档与数据库实际结构始终保持同步。

**Independent Test**: 可以通过运行文档生成命令，验证输出的文档是否包含所有表、字段及其注释。

**Acceptance Scenarios**:

1. **Given** 数据库中的所有表和字段都有注释，**When** 执行文档生成命令，**Then** 生成的文档包含所有表、字段、类型、注释信息
2. **Given** 数据库表结构发生变化，**When** 重新生成文档时，**Then** 新文档反映最新结构

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: 所有数据表 **MUST** 在创建时指定表注释（COMMENT），注释内容不得为空
- **FR-002**: 所有数据表的每个字段 **MUST** 在创建时指定字段注释（COMMENT），注释内容不得为空
- **FR-003**: 所有表的主键 ID **MUST** 使用 Long/bigint 类型，**MUST NOT** 使用 UUID/varchar 类型
- **FR-004**: 数据库迁移脚本 **MUST** 在执行前检查注释完整性，缺少注释的脚本应被拒绝执行
- **FR-005**: 已有缺少注释的表和字段 **MUST** 通过迁移脚本补全注释

### Observability & Diagnostics *(mandatory if feature changes runtime behavior)*

- **OBS-001**: 迁移脚本执行时记录检查结果（通过/失败），包含检查的表数量和字段数量
- **OBS-002**: 迁移失败时记录缺少注释的具体表名和字段名
- **OBS-003**: 日志文件命名：`logfix-ai_YYYYMMDD.log`，输出到 `/log` 目录

### Key Entities *(include if feature involves data)*

- **DatabaseTable**: 数据库表元信息，包含表名、表注释、创建时间等
- **DatabaseColumn**: 数据库字段元信息，包含字段名、字段类型、字段注释、是否为主键等

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 新建表的注释覆盖率（表注释 + 字段注释）达到 100%
- **SC-002**: 所有现有表的注释覆盖率在迁移后达到 100%
- **SC-003**: 所有主键 ID 使用 Long 类型，UUID 主键数量为零
- **SC-004**: CI/CD 流程能够检测并阻止缺少注释的迁移脚本
- **SC-005**: 数据库文档可自动生成且包含完整注释信息

## Assumptions

- 项目使用 Liquibase 或 Flyway 进行数据库迁移管理
- 数据库为 PostgreSQL/MySQL 等支持 COMMENT 语法的关系型数据库
- 现有数据库存在部分缺少注释的表和字段，需要进行历史数据迁移

## Clarifications

### Session 2026-04-12

- Q: UUID 主键的现有数据如何处理 → A: 制定迁移计划时考虑数据迁移策略，可保留原 UUID 作为业务字段，新增 Long 主键
- Q: 外键关联是否也需要注释 → A: 是，外键字段应注释说明关联关系和级联规则
- Q: 枚举类型字段如何注释 → A: 应注释说明各枚举值的含义

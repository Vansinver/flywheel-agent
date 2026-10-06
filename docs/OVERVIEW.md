# 项目概览

## 这是什么

Flywheel Agent 是一套协助用户从真实行动中积累经验、整理证据、识别可复用方法的工作设计。“飞轮”指一个可以反复进行的循环：行动带来证据，证据帮助复盘，复盘形成下一步行动或可复用经验。

“主语”是当前飞轮围绕的目标或领域。它可以长期保持，也可以在用户确认后转向新的候选方向。AI 可以协助整理和提出建议，但不替用户选择目标、宣布阶段完成或切换主语。

这份仓库是可迁移设计草案和示例，不是完整可部署系统。它不包含个人资料，也没有接通任何外部数据源。

## 日常运行循环

数据源适配器提供状态摘要，Gate 校验输入并决定是否需要 Agent 继续处理。Gate 示例只检查传入的 JSON 状态，不连接 WDA、微信或其他数据源。

有新内容或整理欠账时，Agent 才按独立任务说明工作：先把内容收集到私有位置，再进行整理。只有写入和回读校验成功后，才分别推进收集水位和整理水位。Gate 本身只读水位，不修改它们。错误或校验失败时应保留原水位并交由处理。

**Gate 决策**

~~~mermaid
flowchart TD
    input["输入状态<br/>source_available、latest_marker、<br/>last_read_marker、last_organized_marker"]
    input --> valid{"字段齐全且格式合法？"}
    valid -->|否| input_error["status=error<br/>不输出 wakeAgent；非零退出<br/>交人工处理"]
    valid -->|是| source{"source_available = true？"}
    source -->|否| source_error["status=error<br/>不输出 wakeAgent；非零退出<br/>交人工处理"]
    source -->|是| mismatch{"latest_marker = null，且任一检查点非 null？"}
    mismatch -->|是| mismatch_error["status=error<br/>error=source_checkpoint_mismatch<br/>不输出 wakeAgent；非零退出<br/>交人工检查数据源与检查点"]
    mismatch -->|否| backlog{"last_read_marker !=<br/>last_organized_marker？"}
    backlog -->|是| backlog_wake["正常唤醒 Agent<br/>wakeAgent=true<br/>reason=organization_backlog"]
    backlog -->|否| unread{"latest_marker !=<br/>last_read_marker？"}
    unread -->|是| unread_wake["唤醒 Agent<br/>wakeAgent=true<br/>reason=unread_source"]
    unread -->|否| no_change["正常跳过<br/>wakeAgent=false<br/>reason=no_change_detected<br/>仅限三个 marker 全为 null，或三者相等"]
~~~

**收集、整理与双水位**

~~~mermaid
flowchart TD
    wake["Gate 唤醒 Agent<br/>organization_backlog 或 unread_source"] --> need_collect{"有未采集的新消息？"}
    need_collect -->|有| collect["收集到私有位置"]
    collect --> read_check{"写入并回读验证成功？"}
    read_check -->|是| readmark["推进收集水位<br/>last_read"]
    read_check -->|否| hold_read["保留原 last_read<br/>交由错误处理"]
    need_collect -->|无，仅有整理欠账| organize["整理与归档"]
    readmark --> organize
    organize --> org_check{"写入并回读验证成功？"}
    org_check -->|是| orgmark["推进整理水位<br/>last_organized"]
    org_check -->|否| hold_org["保留原 last_organized<br/>交由错误处理"]
~~~

双水位分别记录“哪些内容已安全收集”和“哪些内容已完成整理”。如果数据源报告为空，但任一检查点非空，说明数据源与检查点状态不一致。Gate 返回错误，不唤醒 Agent；需要人工确认数据源是否被清空或重置，再决定是否进行受控基线处理。

## 主语如何迁移

新想法先是候选，不会自动成为新主语。用户和 Agent 先回顾当前周期的行动、证据、成果和未解决问题，再评估新方向是否有真实需求或资源交换假设。评估可以记录已有资源、缺口、最小验证行动和能改变判断的反馈。

只有用户明确确认后，才开始新周期。用户暂不确认时，候选方向继续作为假设保留；原周期的记录和结论仍需保存，不因迁移而重写。

~~~mermaid
flowchart LR
    review["当前周期复盘<br/>行动、证据、缺口"] --> candidate["提出新主语候选"]
    candidate --> assess["评估资源交换<br/>需求、资源、验证行动"]
    assess --> confirm{"用户确认？"}
    confirm -->|确认| start["开始新周期"]
    confirm -->|暂不确认| hold["保留为候选<br/>继续收集证据"]
    hold --> assess
~~~

## 已验证与未验证

- **已验证的范围**：Gate 示例的内置自测覆盖状态比较、决策优先级、合法空源、源与检查点不一致，以及错误输入。自测只验证这个示例的本地逻辑和输出契约。
- **盘点报告中的现有环境记录**：前置盘点描述了一个正在使用的运行链；这不等于本草案已部署或本轮重新验证该运行链。
- **仍未验证**：Qoder CN 或其他替代平台的 MCP 接入、Gate 短路语义、定时无人值守运行、文件与检查点持久性、附件处理和故障恢复。
- **不可推定**：有 MCP 或文件工具，不代表平台已能完整替代现有运行环境。

## 图示说明

上方 SVG 是便于快速理解和分享的概念图，不是运行界面截图，也不代表任一平台已经实现全部流程。

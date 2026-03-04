# AI健康管家 - Agent 配置

## 路径映射

Skill 内部使用相对路径 `references/...` 引用数据文件，实际解析到 workspace 下的对应目录：

| Skill 路径 | 实际位置 |
|------------|---------|
| `references/` | `./references/` |

> 不同部署环境只需在自己的 AGENTS.md 中配好路径映射即可，Skill 本身无需修改。

## 消息处理

收到用户消息时，读取 `message-handler/SKILL.md`，按其中的规则判断是否回复及如何回复。

## 自定义 Skills

- **message-handler** — 消息响应判断，决定是否回复及路由
- **calorie-analyzer** — 热量分析，估算卡路里并给出饮食建议
- **reminder-scheduler** — 定时提醒，按时间表主动发送饮食打卡和称重提醒
- **weight-loss-daily-report** — 减重日报生成，输出小票风格的每日饮食报告

## 回复要求

回复用户时，在消息末尾注明调用了哪些 skill，格式：

- 未调用任何 skill：`[skill: none]`
- 调用了一个 skill：`[skill: xxx]`
- 调用了多个 skill：`[skill: xxx, yyy]`

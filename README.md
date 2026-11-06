# 多模型交叉审稿 Skill

让一个 Agent 协调两个外部模型，对已有论文或研究报告进行独立审阅、交叉评价和复审。Agent 负责整理材料、检查分歧、合并修订稿，并生成审稿报告和原稿对照。

适合已经有论文或研究报告，希望在投稿或汇报前多找两个视角检查的研究者。它也可以用于审阅分析报告、方法说明等文本。

## 工作流程

1. **准备材料**：提供稿件，以及需要审查的结果、代码或参考资料；配置两个模型的接口。
2. **检查连接**：Agent 分别测试两个模型，确认可以正常返回内容。
3. **独立审阅**：两个模型各自审阅同一份材料，首轮互不查看对方意见。
4. **交叉评价**：Agent 将双方意见交给对方，请它们逐项说明认同、部分认同或不认同的理由。
5. **修改与复审**：两个模型分别提出候选修订，Agent 检查、合并后交回双方复审；必要时继续修改。
6. **核查与交付**：Agent 查证重要分歧，对照原稿检查修改，并整理综合审稿报告、修订稿和修改对照。

默认最多进行四轮；关键问题解决后可以提前结束，仍有分歧时保留分歧及其依据。

## 安装

将整个 `cross-model-paper-review` 文件夹放入支持 `SKILL.md` 的 Agent 技能目录。例如 Codex 的个人技能目录：

```text
~/.codex/skills/cross-model-paper-review/
├── SKILL.md
├── README.md
├── references/
│   └── runner.md
└── scripts/
    └── review.py
```

安装后，在新的 Agent 会话中提出审稿请求，并说明使用 `cross-model-paper-review`。运行脚本需要 Python 3；脚本使用 Python 标准库。

## 使用

准备两份模型 API 密钥文件、已有稿件，以及可提供的研究材料。向 Agent 说明密钥文件位置、模型名称、服务地址和希望使用的推理挡位。例如：

> 请使用 cross-model-paper-review 审阅项目中的论文。两位审稿模型的接口信息分别保存在本机的两个 TXT 文件里，模型名称和挡位以我提供的配置为准。请先检查连接，再组织独立审阅、交叉评价和复审；对重要分歧核查依据，最后交付审稿报告、修订稿和原稿对照。

模型调用可能产生费用；具体模型名称、地址、可用挡位和计费方式以服务商文档为准。稿件及交接材料会发送给配置的模型服务商，请根据材料的保密要求选择服务。

### 手动运行各阶段

也可以让 Agent 使用提供的脚本逐阶段运行。以下配置中的地址、模型名称和路径均为占位示例，请替换为自己的信息。`url` 需要填写完整的 Chat Completions 请求地址；密钥单独放在本地文件中，不要直接写入配置。

```json
{
  "max_tokens": 5000,
  "models": [
    {
      "name": "A",
      "url": "https://provider-a.example/v1/chat/completions",
      "model": "model-a",
      "key_file": "/path/to/model-a-key.txt",
      "effort": "low"
    },
    {
      "name": "B",
      "url": "https://provider-b.example/v1/chat/completions",
      "model": "model-b",
      "key_file": "/path/to/model-b-key.txt",
      "effort": "low"
    }
  ]
}
```

脚本目前从密钥文件中识别 `sk-` 开头的密钥，支持 Bearer 认证、Chat Completions 和 `reasoning_effort` 参数的兼容接口。不同服务商的参数可能不同，请先核对其文档。

在 Skill 目录下，依次执行以下命令；每一步成功后再执行下一步：

```bash
python scripts/review.py probe  --config config.json --paper paper.md --out review-run
python scripts/review.py review --config config.json --paper paper.md --out review-run
python scripts/review.py cross  --config config.json --paper paper.md --out review-run
python scripts/review.py draft  --config config.json --paper paper.md --out review-run
```

Agent 检查两份候选稿、合并成一份统一稿后，再交还模型复审：

```bash
python scripts/review.py recheck --config config.json --paper paper.md --out review-run --revision revised.md
```

脚本负责分阶段调用和记录，**不会自动合并稿件、判断意见是否正确或生成最终报告**。这些工作需要 Agent 完成。再次运行同一阶段前，请先归档该阶段的输出，避免覆盖。更多配置和记录说明见 [运行器说明](references/runner.md)。

## 输出与使用边界

运行目录保存原稿快照、各阶段的输入和模型回复，以及不含密钥的调用状态。遇到回复为空或因长度限制截断时，脚本会保留状态，并在原挡位下增加输出额度重试一次。

模型之间达成一致不代表判断一定正确。数据、统计、引用及未解决的分歧仍需结合原始材料核查；未经提供或验证的资料不能视为已经审查。最终稿件和建议应由作者复核。

**请勿将 API 密钥、含敏感路径的配置文件、未公开稿件或审稿运行目录上传到公开仓库。**

## 已做测试

使用一篇专为演示编写的短文，测试了 Kimi K3.1 Pro 与 DeepSeek Flash 的连接、独立审稿、交叉评价、候选修改和两轮复审。请求设置为 Low；部分 DeepSeek 回复触及长度限制，增加输出额度后重试成功。这是单篇短文的功能测试，不能代表所有模型接口或长文场景均已验证。

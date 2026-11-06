# 运行器

使用JSON配置，两个模型各有 name、url（完整chat completions地址）、model、key_file（本地密钥文件路径）和effort；可选max_tokens。不要在配置中直接放密钥。示例：

```json
{"max_tokens": 5000, "models": [
  {"name":"A","url":"https://provider-a.example/v1/chat/completions","model":"model-a","key_file":"本地密钥文件路径A","effort":"low"},
  {"name":"B","url":"https://provider-b.example/v1/chat/completions","model":"model-b","key_file":"本地密钥文件路径B","effort":"low"}
]}
```

使用 `python scripts/review.py <stage> --config <配置路径> --paper <原稿路径> --out <新工作目录>`，依次执行 `probe`、`review`、`cross`、`draft`。模型候选稿由Agent检查合并或选择，保存单一版本后执行 `recheck`，额外提供 `--revision <统一稿路径>`。所有阶段必须等待前一阶段成功，必要时可重复cross/draft/recheck，但每轮使用新目录或先归档前一轮文件，防止覆盖。每次重试原始状态单独保存。脚本仅支持OpenAI兼容的Bearer认证及reasoning_effort参数；不适用时按官方接口自行处理。

输出均是真实模型正文与不含密钥的状态信息。Agent负责决定是否继续下一轮、独立查证、写最终报告和原稿对照；运行器不会自动判断模型意见正确。设置的effort仅表示请求值，除非服务回显实际挡位，否则不要声称已独立验证。

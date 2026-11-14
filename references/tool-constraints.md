# 工具限制与已验证死路（实跑沉淀）

> 本文件登记在试跑环境中**已验证**的环境基线、CLI 受限参数、本地传参坑与解析约定；「死路」指已经试过、当前环境走不通的路线。未实测项标「待验证」，不写死为通用结论。换执行环境后须按当前 `--help` / `--schema` / `--version` 复核，不照搬本清单。

## 1. 环境基线（试跑机实测；换环境须复核）

| 项 | 实测结论 | 复核途径 / 备注 |
|---|---|---|
| Shell | Windows PowerShell；不用 bash 语法，Unix 路径/重定向/heredoc 均为解析错误 | 版本以本机 `$PSVersionTable` 为准 |
| Python | 试跑机仅装 numpy，未装 faster-whisper / FunASR / Vosk | 本地语音栈不可用；可用包以本机 `pip list` 为准 |
| ffmpeg | 本机可用；ffprobe 不可用，元数据用 `ffmpeg -i <file>` 解析末尾 Duration 与 Stream 行（编码/分辨率/帧率/音频采样率声道）；横竖屏以 Display Matrix rotation 应用旋转后的显示方向为准，抽帧/裁切保留默认 autorotate，不加 `-noautorotate` | 版本以 `ffmpeg -version` 为准 |
| mediakit-cli | 鉴权由运行环境注入，不在命令/配置里写鉴权值 | 版本与能力清单以本机 `--version` / `--domains` 为准 |
| 母带（原始高画质文件） | 高分辨率 HEVC 母带在无独显环境下是本地硬瓶颈 | 具体分辨率、码率、时长以本期素材实测为准，不固化 |

## 2. CLI 已验证受限或不可用参数

| 工具 | 受限点 | 已验证结论 | 替代路线 |
|---|---|---|---|
| `video extract-frames --specified-time` | 时间点传参 | 只接受逗号分隔裸数字；JSON 数组、`@文件` 均失败 | 裸数字逗号拼接；超限批量分批 |
| `video video-understand-router --manual-option` | 对象参数 | 内联 JSON、`@文件`、`file:///` 均不被识别为 object；中文路径触发 UTF-8 错乱 | 省略该参数，在理解指令里写「笑声/声音/语气」等音频关键词触发音频多模态链路 |
| 整段上传 | 高码率大体积母带整段直传 | 已知瓶颈，未做整段上传计时 | 本地先裁候选小片/小段（720p 或纯音频）再上传；路线已验证可行 |
| `video asr-subtitles` 纯音频 | `audio_url` | mp3/m4a/wav，时长 ≤3h，本地路径可入；可开置信度、说话人、语言参数 | 整段先抽离 16kHz 单声道 AAC，再按区间裁小段送识别 |
| 配乐生成 | AI 音频生成（文生 WAV） | 文生音频工具支持人声/音效/音乐/环境声；单次生成 1–120s；无曲库检索或音频下载入口，不从既有曲库取曲；本机未装 faster-whisper / librosa | 垫乐按片情自拟提示词自创纯音乐；长片分段生成后本地合流/循环铺底，接缝淡出淡入；生成失败或风格不符出「无配乐样片」，不回退曲库；生成曲可商用授权不在本地核实，留发布前复核。机检用 `ffmpeg -i` 看编码/时长（无 ffprobe）、`volumedetect` 测响度削波、`silencedetect` 标静音；演唱词逐句比对、逐字时间戳、拍点表属 MV/带演唱专属，本地无语音/节拍栈时标待验证，不凭估算落切点 |

> 各工具的输入大小、时长、分辨率限制以当前环境机器合同（`--schema`）为准；未实测的整段上传、云端拼接、整段理解能力标待验证，不预设可用。

## 3. Windows PowerShell 传参坑（已踩过，勿重踩）

1. **JSON 对象参数**：禁单引号包裹、禁 `$json` 变量传入；单引号或变量会剥掉内部 `"`，CLI 报 `invalid character 's'/'t'`。须把 JSON flag 放在 `--%` 之后，整段 JSON 用双引号包裹、内部 `"` 写成 `\"`；文件载荷用 `file:///` 或 `@<本地文件路径>`。
2. **`--%` 之后**不能再跟 PowerShell 变量或语句。
3. **路径内数字格式**：`-f "seg{0:d2}.mp4"` 的冒号在 Windows 文件名规则下被截断，会生成 0 字节坏条目；须先用 `ToString("d2")` 拼成文件名变量再传路径，不在路径字符串内嵌 `-f` 格式。
4. 早期 PowerShell 批量裁片脚本在 PS7 下出现 ParserError 不可执行；批量裁片改写为可复用的 Python 或逐条 ffmpeg 命令。

## 4. 本地结果解析约定

- 早期 ASR JSON（run1/2/3）顶层是**字符串数组**：解析须先 `obj = json.loads("".join(arr))`，再取 `obj["subtitles"]`；字段为 `start_time / end_time / subtitle_text`，**无置信度字段**。
- 二轮 ASR JSON 顶层为对象：`status / subtitles[]`，字幕条目含 `confidence / speaker / start_time / end_time / subtitle_text`。
- 小段识别时间码为相对秒，须加回区间起点偏移映射回母带秒；偏移映射在对照脚本里集中维护，改区间后重跑对照。

## 5. 已验证可行路线（试跑采用）

- 母带整段抽离音频 → 按待核区间裁纯音频小段 → 云端 ASR 二次识别 → 加回偏移对照母带时间码；
- 本地 ffmpeg 先裁候选小片（720p、CRF 可调、音频降码率）再送云端理解/抽帧，避免整段上传；
- 云端异步任务取 `task_id` 后轮询终态；临时产物链接 24 小时有效，核验后及时下载留存。
- 本地人声+垫乐混音：`amix` 默认 `normalize=true`，每路按输入路数 N 归一化（人声被一并衰减约 20·log10(N) dB）；要保留原人声响度须显式 `normalize=0`，垫乐支路单独用 `volume` 压低，输出端 `alimiter` 限幅防两路相加削波；混音后按人声段 `volumedetect` 复核，人声峰值不低于无人声基线。
- 原片录音偏轻（台词段 mean 明显低于 −30dB、峰值余量充足）：人声轨先轻度压缩再 makeup 增益，输出 `alimiter` 兜底，整段峰值留 ≥3dB 余量不削波；分段 `volumedetect` 复核台词段 mean/max，不只看含板段静音的整段平均。`acompressor` 参数坑：`threshold` 为线性振幅（非 dB）、`ratio` 为纯数字（不写 `2:1`，冒号会被当参数分隔符）、`makeup` 为增益倍数（dB 须先换算 10^(dB/20)）。

## 6. 本地 ffmpeg 参数坑（已踩，换版本先复核）

- `dynaudnorm` 的 `r`（目标动态范围）取值范围仅 `[0,1]`；超出范围直接参数报错，不按更大数值生效。
- 片头/板段补静音音轨：`anullsrc` 静音源必须在 `-filter_complex` 之前作为输入 0 显式接入，音频 map 用 `0:a`；把静音源写进 filter_complex 内部或省略该输入，会拿不到对应音轨、段间断音。
- `ffmpeg -i <file>` 只探测元数据、不带输出文件时，退出码为 1 属正常（缺输出被 ffmpeg 记为错误）；元数据以末尾 Duration/Stream 行解析，不凭退出码判文件损坏。

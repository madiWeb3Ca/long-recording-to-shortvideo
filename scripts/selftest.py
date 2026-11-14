# -*- coding: utf-8 -*-
"""
节点自检脚本（P0 / P1 / P2 / P3 / P4）。
校验：提示词模板覆盖必填字段与关键机制；字段契约枚举与映射完整；
测试样例断言齐全。退出码 0 = 全部通过；1 = 存在失败项。
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(path: Path) -> str:
    if not path.exists():
        print(f"[FAIL] 文件缺失: {path}")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def check(ok: bool, msg: str) -> bool:
    print(("[PASS] " if ok else "[FAIL] ") + msg)
    return ok


def validate_node(node: str, prompt: Path, contract: Path, cases: Path,
                  fields: list[str], mechanisms: list[str],
                  contract_rules: list[str], guard_keywords: list[str],
                  stale_tokens: list[str] | None = None,
                  required_enums: list[str] | None = None,
                  l3_contract_rules: list[str] | None = None,
                  l3_case_keywords: list[str] | None = None) -> bool:
    ok = True
    p = read(prompt)
    c = read(contract)
    t = read(cases)

    for field in fields:
        ok &= check(field in p, f"[{node}] 提示词含字段 {field}")
    for token in mechanisms:
        ok &= check(token in p, f"[{node}] 提示词含关键机制: {token}")
    for token in contract_rules:
        ok &= check(token in c, f"[{node}] 契约含规则: {token}")

    for stale in (stale_tokens or []):
        leaked = [name for name, text in (("提示词", p), ("契约", c), ("样例", t)) if stale in text]
        ok &= check(not leaked, f"[{node}] 旧措辞已清除: {stale}" + (f"（残留于 {','.join(leaked)}）" if leaked else ""))
    for enum in (required_enums or []):
        ok &= check(enum in p and enum in c, f"[{node}] 枚举一致: {enum}")

    for token in (l3_contract_rules or []):
        ok &= check(token in c, f"[{node}] L3 机制规则: {token}")
    for token in (l3_case_keywords or []):
        ok &= check(token in t, f"[{node}] L3 档位样例覆盖: {token}")

    contract_fields = set(re.findall(r"\b([ABCD]\d(?:-\d)?)\b", c))
    missing = [f for f in fields if re.match(r"[ABCD]\d", f) and f not in contract_fields]
    ok &= check(not missing, f"[{node}] 契约覆盖字段（缺: {missing}）")

    case_count = len(re.split(r"\n## 样例 \d+", t)) - 1
    ok &= check(case_count >= 8, f"[{node}] 测试样例数量: {case_count}（≥8）")

    assertions = re.findall(r"- \[ \]", t)
    ok &= check(len(assertions) >= 20, f"[{node}] 断言条数: {len(assertions)}（≥20）")

    for keyword in guard_keywords:
        ok &= check(keyword in t, f"[{node}] 样例覆盖护栏场景: {keyword}")

    return ok


def main() -> int:
    ok = True

    # P0 需求建档
    ok &= validate_node(
        "P0",
        ROOT / "assets" / "prompt-p0-intake.md",
        ROOT / "references" / "p0-field-contract.md",
        ROOT / "references" / "p0-test-cases.md",
        fields=["F0", "A1", "A2", "A3", "A4", "A5-1", "A5-2", "A5-3", "A5-4", "A6",
                "B1", "B2", "B3", "B4", "B5", "C1", "C2", "C3", "D1", "D2", "D3"],
        mechanisms=["素材核验", "停止分支", "口径裁决表", "容量预检", "完整性自检",
                    "待补项分级", "需求单元信息", "口径封存说明", "下游归属",
                    "历史物料比对", "物料旁证", "转写状态", "按主体", "局部不可用",
                    "错位组合", "旧版弃用", "变更影响面", "主素材", "自带硬字幕",
                    "单选", "多选", "片头方式", "片尾方式", "切片板位", "流程档位"],
        contract_rules=["官方品牌规范", "主素材", "明确拒绝", "P1 开始前", "P3 开始前", "发布前",
                    "物料旁证", "转写状态", "按主体", "局部不可用", "错位组合", "回滚", "水印",
                    "单选", "多选", "自备尾片模板", "无板", "标题板", "9:16 竖屏", "16:9 横屏",
                    "L1 内部回顾", "档位裁剪"],
        guard_keywords=["品牌口径缺失", "授权不明", "停止分支", "诱导越界", "错位",
                    "历史物料", "旁证", "无逐字稿", "局部不可用", "授权按主体", "自带字幕",
                    "选项卡", "自备尾片模板", "无板", "标题板", "轻流程", "内部回顾"],
        required_enums=["无板", "标题板", "标题板+尾片", "9:16 竖屏", "16:9 横屏", "首句导入",
                    "L1 内部回顾", "L2 对外宣传", "L3 正式招募"],
        l3_contract_rules=["逐项留档", "品牌规范", "可商用", "发布前复核台账"],
        l3_case_keywords=["L2 对外宣传", "L3 正式招募"],
    )

    # P1 选段方案
    ok &= validate_node(
        "P1",
        ROOT / "assets" / "prompt-p1-selection.md",
        ROOT / "references" / "p1-field-contract.md",
        ROOT / "references" / "p1-test-cases.md",
        fields=["D1", "D2", "B1", "B2", "B3", "B4", "A5-1", "A5-2", "A5-3",
                "钩子", "主干", "金句", "笑点", "互动", "落点"],
        mechanisms=["段落粒度规则", "主角色", "副角色", "强制保留", "禁区反查",
                    "时间码校验", "授权不足", "原片顺序号", "净时长", "裁决顺序",
                    "转写预处理", "置信度", "原话一致性", "说话人映射", "转写缺失",
                    "术语校准", "证据来源", "碎片", "截取余量", "降级",
                    "主线环节归属", "情绪点缀", "首尾呼应",
                    "保留判定标准", "一律剔除", "选段流程", "选段结构单", "剔除段落清单",
                    "保留项核对", "转写风险清单", "时长与容量估算", "待确认项", "完成条件",
                    "同一完整案例", "动作峰值待补帧", "时间码不一致",
                    "段落自足性", "论点—论证—落点", "论点目的", "语境不通", "选项卡"],
        contract_rules=["时间码", "ASR 编号", "推定身份", "主线环节", "主角色", "副角色", "对外片", "口径待改",
                    "授权不足", "裁决顺序", "净时长", "P2 粗样", "截止节点", "置信度",
                    "证据来源", "措辞不符", "转写缺失", "首尾呼应", "需音频核验",
                    "同一完整案例", "动作峰值待补帧", "段落自足性", "落点句", "论点目的", "语境不通", "选项卡"],
        guard_keywords=["禁区反查", "授权不足", "口径混入", "低置信", "措辞不符", "说话人映射",
                    "转写缺失", "术语误写", "证据来源", "降级", "时间码校验",
                    "时长超出", "角色兼类", "落点取自原片", "诱导越界", "需音频核验", "情绪点缀",
                    "合并", "动作峰值待补帧", "时间码冲突", "不自足", "例证", "排练", "起哄", "语境不通",
                    "选项卡"],
        stale_tokens=["需画面声音佐证", "需画面佐证", "人工通读", "说话人未分离"],
        required_enums=["文字可证", "需画面核验", "需音频核验", "开场钩子", "情绪点缀", "收尾落点",
                    "动作峰值待补帧"],
    )

    # P2 粗样拼接
    ok &= validate_node(
        "P2",
        ROOT / "assets" / "prompt-p2-roughcut.md",
        ROOT / "references" / "p2-field-contract.md",
        ROOT / "references" / "p2-test-cases.md",
        fields=["B1", "B4", "A5", "D2",
                "钩子", "主干", "金句", "笑点", "互动", "落点"],
        mechanisms=["前置校验", "拼接执行规则", "截取余量", "断点完整", "画面核验", "音频核验",
                    "主线与连贯", "连贯与节奏核对", "问题回退", "粗样执行单", "核验记录",
                    "移交与回退清单", "口径待改", "原素材画幅", "完成条件",
                    "定点取帧", "AI 处理耗时", "p2-evidence-protocol",
                    "产物完整性自检", "草案试跑预览", "背景", "低清代理", "链路基准", "选项卡"],
        contract_rules=["时间码", "推定身份", "主角色", "衔接说明", "需画面核验", "需音频核验",
                    "净时长", "回 P1", "留 P3", "首尾呼应", "授权不足", "禁区", "结构单",
                    "锚定触发取帧", "音画合诊", "处理耗时", "p2-evidence-protocol",
                    "草案试跑预览", "产物完整性自检", "背景", "低清代理", "链路基准", "选项卡"],
        guard_keywords=["未确认", "定位不到", "断点完整", "口径待改", "画面核验", "音频核验",
                    "跳脱", "悬浮", "时长超差", "越界", "授权不足", "轻口径",
                    "锚点", "分项计时", "草案", "0 字节", "背景", "代理", "链路基准", "选项卡"],
        stale_tokens=["需画面声音佐证", "需画面佐证", "人工通读", "说话人未分离"],
        required_enums=["文字可证", "需画面核验", "需音频核验", "草案试跑预览"],
    )

    # P3 包装合成
    ok &= validate_node(
        "P3",
        ROOT / "assets" / "prompt-p3-packaging.md",
        ROOT / "references" / "p3-field-contract.md",
        ROOT / "references" / "p3-test-cases.md",
        fields=["B2", "B3", "B4", "B5", "C1", "C2", "D3", "A5-3", "A6"],
        mechanisms=["前置校验", "竖屏构图", "片头", "片尾", "字幕", "沿用原字幕", "擦除重压",
                    "断行", "术语", "配乐", "人声优先", "对外口径清理", "核验回写",
                    "问题回退", "包装记录", "完成条件", "产物完整性自检", "安全区",
                    "同框", "降格", "待复核", "品牌 logo", "选填", "可读字号", "曲风",
                    "底色", "板段", "片头方式", "片尾方式", "选项卡", "流程档位"],
        contract_rules=["构图方案", "沿用原字幕", "擦除重压", "安全区", "多人同框", "逐字",
                    "催单", "留资", "人声优先", "授权", "回 P1", "回 P2", "留 P4",
                    "R3", "降格", "叠双字幕", "完整性自检", "D3", "A6", "A5-3",
                    "反白", "选填", "字号", "人声形态", "底色", "版本记录", "自备尾片模板", "选项卡",
                    "L1 轻包装"],
        guard_keywords=["未确认", "逐字", "催单", "留资", "沿用", "擦除重压", "安全区",
                    "同框", "降格", "存疑", "术语", "人声优先", "内部口径",
                    "未授权", "待复核", "叠双字幕", "反白", "选填", "可读", "纯音乐",
                    "音轨断裂", "自备模板", "选项卡", "轻包装"],
        stale_tokens=["需画面声音佐证", "需画面佐证", "人工通读", "说话人未分离"],
        required_enums=["居中裁切", "底板填充", "适度缩放", "沿用原字幕", "擦除重压", "首句导入"],
        l3_contract_rules=["品牌规范", "可商用", "复核台账", "升档重做"],
        l3_case_keywords=["L3 正式招募"],
    )

    # P4 切片派生
    ok &= validate_node(
        "P4",
        ROOT / "assets" / "prompt-p4-clips.md",
        ROOT / "references" / "p4-field-contract.md",
        ROOT / "references" / "p4-test-cases.md",
        fields=["D1", "D3", "A5-1", "A5-2", "B4", "B5", "A5-3", "C3",
                "E1", "E2", "E3"],
        mechanisms=["前置校验", "选题来源", "时长区间", "独立成立判定", "口径沿用",
                    "切片包装", "核验回写", "问题回退", "切片清单", "包装记录",
                    "完成条件", "产物完整性自检", "人声优先", "硬裁", "剧透",
                    "待复核", "降格", "安全区", "同框", "选填", "切片板位",
                    "段证据等级", "遗留项", "拆片", "预览样片", "选项卡"],
        contract_rules=["选题类型", "源时间码区间", "独立成立结论", "授权核对", "口径沿用项",
                    "回 P1", "回 P3", "回 P0", "R3", "撤下", "需回补", "叠双字幕",
                    "完整性自检", "D3", "B5", "A5-3", "A5-1", "A5-2", "C3-模式",
                    "文字可证", "需画面核验", "需音频核验", "预览样片", "继承遗留项", "选项卡"],
        guard_keywords=["未确认", "未授权", "存疑", "降格", "不足", "依赖上下文", "硬裁",
                    "剧透", "夸大", "自检", "术语", "脱敏", "配乐", "独立成立",
                    "催单", "留资", "身份未推定", "口径待改", "无板", "标题板",
                    "未核验", "声音事件", "无配乐", "备选标题", "拆片", "选项卡"],
        stale_tokens=["需画面声音佐证", "需画面佐证", "人工通读", "说话人未分离"],
        required_enums=["金句", "观点", "笑点", "互动", "落点", "无板", "标题板", "标题板+尾片"],
    )

    print("\n结果: " + ("全部通过" if ok else "存在失败项"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

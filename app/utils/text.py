import re
from typing import List


def extract_symptoms(ci_log: str) -> List[str]:
    lines = [l.strip() for l in ci_log.splitlines() if l.strip()]
    key_lines: List[str] = []
    patterns = [
        # 일반적인 오류 패턴
        r"error[:\s]",
        r"exception",
        r"fail(ed)?",
        r"not found",
        r"missing",
        r"undefined",
        r"cannot (resolve|find)",
        r"exit code [1-9]",
        
        # 자동차 SW 특화 패턴
        r"compilation error",
        r"linker error",
        r"assembler error",
        r"code generation error",
        r"misra.*violation",
        r"polyspace.*error",
        r"tasking.*error",
        r"nxp.*error",
        r"s32.*error",
        r"autosar.*error",
        r"ecu extract.*failed",
        r"rte.*generation.*error",
        r"can.*timeout",
        r"canoe.*error",
        r"simulink.*error",
        r"targetlink.*error",
        r"vector.*error",
        r"davinci.*error",
        r"proof.*timeout",
        r"static analysis.*error",
        r"toolchain.*path.*not found",
        r"capl.*error",
        r"dbc.*error",
        r"arxml.*error",
        r"bsw.*error",
        r"build.*failed",
        r"test.*failed",
        r"verification.*failed",
    ]
    regex = re.compile("|".join(patterns), re.IGNORECASE)
    for line in lines:
        if regex.search(line):
            key_lines.append(line[:300])
    # fallback
    if not key_lines:
        key_lines = lines[-5:]
    # dedup preserving order
    seen = set()
    uniq: List[str] = []
    for l in key_lines:
        if l not in seen:
            seen.add(l)
            uniq.append(l)
    return uniq[:20]


def truncate_tokens(text: str, max_chars: int = 6000) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return head + "\n... [truncated] ...\n" + tail



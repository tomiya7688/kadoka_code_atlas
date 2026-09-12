"""Deterministic, language-independent comment candidate generation."""

from __future__ import annotations

import re
from dataclasses import dataclass

from Src.analyzers.ir import CodeEntity, EntityKind, ModuleIR
from Src.analyzers.ir_queries import qualified_name


@dataclass(frozen=True, slots=True)
class CommentCandidate:
    """A single line comment to insert before a source entity."""

    line: int
    indent: int
    text: str
    entity: str


class RuleBasedCommentGenerator:
    """Generate concise role comments without requiring an LLM."""

    def generate(self, module: ModuleIR) -> list[CommentCandidate]:
        candidates: list[CommentCandidate] = []
        for entity in module.entities:
            if entity.docstring:
                continue
            text = self._describe(entity)
            if not text:
                continue
            candidates.append(
                CommentCandidate(
                    line=entity.line,
                    indent=entity.indent,
                    text=text,
                    entity=qualified_name(entity),
                )
            )
        return candidates

    def _describe(self, entity: CodeEntity) -> str:
        words = self._words(entity.name)
        readable_name = " ".join(words) if words else entity.name

        if entity.kind is EntityKind.CLASS:
            return f"{readable_name} に関する状態と処理をまとめる。"

        verb = words[0] if words else entity.name
        subject = " ".join(words[1:]) if len(words) > 1 else "処理"
        templates = {
            "get": f"{subject}を取得する。",
            "load": f"{subject}を読み込む。",
            "read": f"{subject}を読み取る。",
            "parse": f"{subject}を解析する。",
            "create": f"{subject}を生成する。",
            "build": f"{subject}を構築する。",
            "generate": f"{subject}を生成する。",
            "render": f"{subject}を描画用表現へ変換する。",
            "save": f"{subject}を保存する。",
            "write": f"{subject}を書き出す。",
            "update": f"{subject}を更新する。",
            "delete": f"{subject}を削除する。",
            "remove": f"{subject}を取り除く。",
            "validate": f"{subject}を検証する。",
            "check": f"{subject}を確認する。",
            "find": f"{subject}を検索する。",
            "collect": f"{subject}を収集する。",
            "convert": f"{subject}を変換する。",
            "run": f"{subject}の処理を実行する。",
        }
        if verb in templates:
            return templates[verb]

        if entity.calls:
            return f"{readable_name} の処理を実行し、関連処理を連携させる。"
        return f"{readable_name} の処理を行う。"

    @staticmethod
    def _words(name: str) -> list[str]:
        normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name).strip("_")
        return [word.lower() for word in normalized.split("_") if word]

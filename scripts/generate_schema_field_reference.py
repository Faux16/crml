from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable


BEGIN_MARKER = "<!-- BEGIN: GENERATED FIELD REFERENCE -->"
END_MARKER = "<!-- END: GENERATED FIELD REFERENCE -->"


@dataclass(frozen=True)
class FieldRow:
    path: str
    json_type: str
    required: bool
    description: str
    constraints: str


def _repo_root() -> Path:
    # scripts/generate_schema_field_reference.py -> repo root
    return Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _json_pointer_get(doc: Any, pointer: str) -> Any:
    if not pointer.startswith("#/"):
        raise ValueError(f"Unsupported $ref pointer: {pointer!r}")

    cur: Any = doc
    for raw_part in pointer[2:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(f"Pointer {pointer!r} not found at {part!r}")
    return cur


def _resolve_ref(schema_root: dict[str, Any], node: Any) -> Any:
    if not isinstance(node, dict):
        return node

    ref = node.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/"):
        return _json_pointer_get(schema_root, ref)

    # External refs are not expected in these bundled schemas.
    return node


def _merge_all_of(schema_root: dict[str, Any], node: dict[str, Any]) -> dict[str, Any]:
    all_of = node.get("allOf")
    if not isinstance(all_of, list) or not all_of:
        return node

    merged: dict[str, Any] = {}
    for part in all_of:
        part_resolved = _resolve_ref(schema_root, part)
        if isinstance(part_resolved, dict):
            merged.update(part_resolved)

    for k, v in node.items():
        if k != "allOf":
            merged[k] = v
    return merged


def _type_str(node: dict[str, Any]) -> str:
    if "$ref" in node:
        return "ref"
    if "const" in node:
        return "const"

    t = node.get("type")
    if isinstance(t, list):
        return " | ".join(str(x) for x in t)
    if isinstance(t, str):
        return t

    if "enum" in node:
        return "enum"
    if "oneOf" in node:
        return "oneOf"
    if "anyOf" in node:
        return "anyOf"
    if "allOf" in node:
        return "allOf"

    return ""


def _constraints_str(node: dict[str, Any]) -> str:
    parts: list[str] = []

    if "const" in node:
        parts.append(f"const={node['const']!r}")
    if "enum" in node and isinstance(node["enum"], list):
        enums = node["enum"]
        if len(enums) <= 8:
            parts.append("enum=" + ", ".join(repr(e) for e in enums))
        else:
            parts.append(f"enum({len(enums)})")

    for key in (
        "pattern",
        "format",
        "minimum",
        "maximum",
        "exclusiveMinimum",
        "exclusiveMaximum",
        "multipleOf",
        "minLength",
        "maxLength",
        "minItems",
        "maxItems",
        "uniqueItems",
    ):
        if key in node:
            parts.append(f"{key}={node[key]!r}")
    if node.get("additionalProperties") is True:
        parts.append("additionalProperties=true")
    if node.get("additionalProperties") is False:
        parts.append("additionalProperties=false")

    if "default" in node:
        parts.append(f"default={node['default']!r}")

    return "; ".join(parts)


def _iter_fields(
    *,
    schema_root: dict[str, Any],
    node: Any,
    path: str,
    required_names: set[str] | None,
    visited_nodes: set[int],
) -> Iterable[FieldRow]:
    node = _resolve_ref(schema_root, node)
    if isinstance(node, dict):
        node = _merge_all_of(schema_root, node)

    if not isinstance(node, dict):
        return

    obj_id = id(node)
    if obj_id in visited_nodes:
        return
    visited_nodes.add(obj_id)

    json_type = _type_str(node)
    description = str(node.get("description") or "").strip()
    constraints = _constraints_str(node)

    if path:
        field_name = path.split(".")[-1]
        is_required = required_names is not None and field_name in required_names
        yield FieldRow(
            path=path,
            json_type=json_type,
            required=is_required,
            description=description,
            constraints=constraints,
        )

    if node.get("type") == "object" or "properties" in node:
        props = node.get("properties")
        if isinstance(props, dict):
            req = node.get("required")
            child_required = set(req) if isinstance(req, list) else set()
            for prop_name, prop_schema in props.items():
                child_path = f"{path}.{prop_name}" if path else prop_name
                yield from _iter_fields(
                    schema_root=schema_root,
                    node=prop_schema,
                    path=child_path,
                    required_names=child_required,
                    visited_nodes=visited_nodes,
                )

    if node.get("type") == "array" and "items" in node:
        items_path = f"{path}[]" if path else "[]"
        yield from _iter_fields(
            schema_root=schema_root,
            node=node.get("items"),
            path=items_path,
            required_names=None,
            visited_nodes=visited_nodes,
        )


def _render_table(rows: list[FieldRow]) -> str:
    header = "| Path | Type | Required | Description | Constraints |\n|---|---:|:---:|---|---|\n"

    def esc(s: str) -> str:
        return s.replace("\n", " ").replace("|", "\\|").strip()

    body_lines: list[str] = []
    for row in rows:
        body_lines.append(
            "| "
            + " | ".join(
                [
                    esc(row.path),
                    esc(row.json_type),
                    "yes" if row.required else "",
                    esc(row.description),
                    esc(row.constraints),
                ]
            )
            + " |"
        )

    return header + "\n".join(body_lines) + "\n"


def _schemas_to_scan(repo_root: Path) -> list[Path]:
    paths: list[Path] = []

    lang_dir = repo_root / "crml_lang" / "src" / "crml_lang" / "schemas"
    if lang_dir.is_dir():
        paths.extend(sorted(lang_dir.glob("crml-*-schema.json")))

    engine_dir = repo_root / "crml_engine" / "src" / "crml_engine" / "schemas"
    if engine_dir.is_dir():
        paths.extend(sorted(engine_dir.glob("crml-*-schema.json")))

    return paths


def _generate_markdown(repo_root: Path, schema_paths: list[Path]) -> str:
    lines: list[str] = []
    lines.append(
        f"Generated on {date.today().isoformat()} by `scripts/generate_schema_field_reference.py`.\n"
    )
    lines.append("This section is auto-generated. Do not hand-edit.\n")

    for schema_path in schema_paths:
        rel = schema_path.relative_to(repo_root).as_posix()
        schema = _load_json(schema_path)
        title = str(schema.get("title") or schema_path.name)
        lines.append(f"### {title}\n")
        lines.append(f"Source: `{rel}`\n")

        rows = list(
            _iter_fields(
                schema_root=schema,
                node=schema,
                path="",
                required_names=None,
                visited_nodes=set(),
            )
        )
        rows = [r for r in rows if r.path]
        lines.append(_render_table(rows))

    return "\n".join(lines).rstrip() + "\n"


def _ensure_markers(existing: str) -> str:
    if BEGIN_MARKER in existing and END_MARKER in existing:
        return existing

    if END_MARKER in existing and BEGIN_MARKER not in existing:
        anchor = "(Run `python scripts/generate_schema_field_reference.py` to populate this section.)"
        if anchor in existing:
            before, after = existing.split(anchor, 1)
            return before + anchor + "\n\n" + BEGIN_MARKER + "\n" + after

        return existing.replace(END_MARKER, BEGIN_MARKER + "\n\n" + END_MARKER)

    return existing


def _replace_generated_section(existing: str, generated: str) -> str:
    existing = _ensure_markers(existing)

    if BEGIN_MARKER not in existing or END_MARKER not in existing:
        raise ValueError(
            "Output file is missing generation markers. Expected markers:\n"
            f"  {BEGIN_MARKER}\n  {END_MARKER}\n"
        )

    before, rest = existing.split(BEGIN_MARKER, 1)
    _, after = rest.split(END_MARKER, 1)
    return before + BEGIN_MARKER + "\n\n" + generated + "\n" + END_MARKER + after


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Generate a Markdown field reference by walking the bundled JSON Schemas. "
            "Updates the content between markers in the output file."
        )
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=_repo_root() / "wiki" / "Reference" / "CRML-Schema-Field-Reference.md",
        help="Output Markdown file (must contain generation markers).",
    )
    parser.add_argument(
        "--schemas",
        type=Path,
        nargs="*",
        default=None,
        help=(
            "Optional explicit schema file paths. If omitted, scans the repo's "
            "crml_lang and crml_engine schema folders."
        ),
    )

    args = parser.parse_args()
    repo_root = _repo_root()

    if args.schemas is None:
        schema_paths = _schemas_to_scan(repo_root)
    else:
        schema_paths = [p if p.is_absolute() else (repo_root / p) for p in args.schemas]

    if not schema_paths:
        raise SystemExit("No schemas found to scan.")

    out_path: Path = args.out if args.out.is_absolute() else (repo_root / args.out)
    generated = _generate_markdown(repo_root, schema_paths)

    if not out_path.exists():
        raise SystemExit(
            f"Output file does not exist: {out_path}\n"
            "Create it with the required markers first (see wiki/Reference)."
        )

    updated = _replace_generated_section(out_path.read_text(encoding="utf-8"), generated)
    out_path.write_text(updated, encoding="utf-8", newline="\n")

    rel_out = out_path.relative_to(repo_root).as_posix()
    print(f"Updated {rel_out} from {len(schema_paths)} schemas")


if __name__ == "__main__":
    main()

"""
Oracle schema snapshot tool.

Reads connection info from `server/.env` (DB_USERNAME, DB_PASSWORD, DB_HOST, DB_PORT, DB_SERVICE_NAME)
and produces a markdown snapshot of tables/columns/constraints/indexes.

Usage:
  poetry run python tools/schema_dump.py
  poetry run python tools/schema_dump.py --out schema_snapshot.md
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class DbConfig:
    user: str
    password: str
    host: str
    port: str
    service_name: str

    @property
    def dsn(self) -> str:
        return f"{self.host}:{self.port}/{self.service_name}"


def _load_db_config(server_dir: Path) -> DbConfig:
    env_path = server_dir / ".env"
    load_dotenv(dotenv_path=env_path)

    import os

    return DbConfig(
        user=os.environ["DB_USERNAME"],
        password=os.environ["DB_PASSWORD"],
        host=os.environ.get("DB_HOST", "localhost"),
        port=os.environ.get("DB_PORT", "1521"),
        service_name=os.environ["DB_SERVICE_NAME"],
    )


def _query_all(cur, sql: str, params: dict | None = None) -> list[tuple]:
    cur.execute(sql, params or {})
    return cur.fetchall()


def build_snapshot_md(cfg: DbConfig) -> str:
    import oracledb

    lines: list[str] = []
    lines.append("# Oracle schema snapshot")
    lines.append("")
    lines.append(f"- **DSN**: `{cfg.dsn}`")
    lines.append("")

    conn = oracledb.connect(user=cfg.user, password=cfg.password, dsn=cfg.dsn)
    try:
        cur = conn.cursor()
        (schema,) = _query_all(
            cur, "select sys_context('USERENV','CURRENT_SCHEMA') from dual"
        )[0]
        lines.append(f"- **Schema**: `{schema}`")
        lines.append("")

        tables = [r[0] for r in _query_all(cur, "select table_name from user_tables order by table_name")]
        lines.append(f"## Tables ({len(tables)})")
        lines.append("")
        for t in tables:
            lines.append(f"- `{t}`")
        lines.append("")

        lines.append("## Columns")
        lines.append("")
        rows = _query_all(
            cur,
            """
            select table_name, column_id, column_name, data_type, data_length, data_precision,
                   data_scale, nullable
            from user_tab_columns
            order by table_name, column_id
            """,
        )
        current = None
        for (table_name, _, col, dtype, dlen, prec, scale, nullable) in rows:
            if table_name != current:
                current = table_name
                lines.append(f"### `{table_name}`")
                lines.append("")
                lines.append("| column | type | nullable |")
                lines.append("|---|---|---|")
            type_str = dtype
            if dtype in ("VARCHAR2", "CHAR", "NVARCHAR2", "NCHAR"):
                type_str = f"{dtype}({dlen})"
            elif dtype == "NUMBER":
                if prec is not None:
                    if scale is not None:
                        type_str = f"NUMBER({int(prec)},{int(scale)})"
                    else:
                        type_str = f"NUMBER({int(prec)})"
                else:
                    type_str = "NUMBER"
            null_str = "Y" if nullable == "Y" else "N"
            lines.append(f"| `{col}` | `{type_str}` | {null_str} |")
        lines.append("")

        lines.append("## Constraints (PK/UK/FK)")
        lines.append("")
        rows = _query_all(
            cur,
            """
            select c.table_name, c.constraint_name, c.constraint_type,
                   cc.column_name, cc.position, c.r_constraint_name
            from user_constraints c
            join user_cons_columns cc on c.constraint_name = cc.constraint_name
            where c.constraint_type in ('P','R','U')
            order by c.table_name, c.constraint_name, cc.position
            """,
        )
        lines.append("| table | name | type | columns | ref |")
        lines.append("|---|---|---|---|---|")
        # group columns by (table,constraint)
        grouped: dict[tuple[str, str, str, str | None], list[str]] = {}
        for table, name, ctype, col, _pos, rname in rows:
            key = (table, name, ctype, rname)
            grouped.setdefault(key, []).append(col)
        for (table, name, ctype, rname), cols in grouped.items():
            cols_str = ", ".join(f"`{c}`" for c in cols)
            ref = f"`{rname}`" if rname else ""
            lines.append(f"| `{table}` | `{name}` | `{ctype}` | {cols_str} | {ref} |")
        lines.append("")

        lines.append("## Indexes")
        lines.append("")
        rows = _query_all(
            cur,
            """
            select i.table_name, i.index_name, ic.column_name, ic.column_position
            from user_indexes i
            join user_ind_columns ic on i.index_name = ic.index_name
            order by i.table_name, i.index_name, ic.column_position
            """,
        )
        lines.append("| table | index | columns |")
        lines.append("|---|---|---|")
        grouped2: dict[tuple[str, str], list[str]] = {}
        for table, idx, col, _pos in rows:
            grouped2.setdefault((table, idx), []).append(col)
        for (table, idx), cols in grouped2.items():
            cols_str = ", ".join(f"`{c}`" for c in cols)
            lines.append(f"| `{table}` | `{idx}` | {cols_str} |")
        lines.append("")

    finally:
        conn.close()

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=str, default="schema_snapshot.md")
    args = parser.parse_args()

    server_dir = Path(__file__).resolve().parents[1]
    cfg = _load_db_config(server_dir)
    md = build_snapshot_md(cfg)

    out_path = (server_dir / args.out).resolve()
    out_path.write_text(md, encoding="utf-8")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

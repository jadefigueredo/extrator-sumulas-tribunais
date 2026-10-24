"""CLI: ``python -m sumulas tjpa tre-pa --output data/``."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from sumulas.http import HttpClient
from sumulas.pdf import pdf_to_text
from sumulas.pipeline import Result, collect
from sumulas.tribunais import TRIBUNAIS


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sumulas", description="Coleta súmulas de tribunais e gera um JSON por tribunal."
    )
    parser.add_argument(
        "tribunais",
        nargs="*",
        choices=sorted(TRIBUNAIS),
        default=sorted(TRIBUNAIS),
        help="tribunais a coletar (padrão: todos)",
    )
    parser.add_argument("-o", "--output", type=Path, default=Path("data"), help="pasta de saída")
    parser.add_argument("--concurrency", type=int, default=4, help="downloads simultâneos")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser.parse_args(argv)


async def run(args: argparse.Namespace) -> list[Result]:
    async with HttpClient(max_concurrency=args.concurrency) as client:
        return [await collect(TRIBUNAIS[slug], client, pdf_to_text) for slug in args.tribunais]


def write(result: Result, output: Path) -> Path:
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{result.tribunal}.json"
    payload = {
        "tribunal": result.tribunal,
        "total": len(result.sumulas),
        "sumulas": [s.to_dict() for s in result.sumulas],
        "falhas": result.falhas,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    results = asyncio.run(run(args))

    for result in results:
        path = write(result, args.output)
        print(
            f"{result.tribunal}: {len(result.sumulas)} súmulas, "
            f"{len(result.falhas)} falhas, {len(result.ignorados)} ignorados → {path}"
        )
    return 0 if all(r.sumulas for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())

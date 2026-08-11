"""Small read-only HTTP load gate for local and deployed Solara Hire services."""

from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

DEFAULT_TARGETS = (
    "api-live=http://127.0.0.1:8000/api/v1/health/live",
    "api-ready=http://127.0.0.1:8000/api/v1/health/ready",
    "frontend-home=http://127.0.0.1:3000/",
)
OpenUrl = Callable[..., object]


@dataclass(frozen=True)
class Target:
    name: str
    url: str


@dataclass(frozen=True)
class RequestResult:
    duration_ms: float
    status: int | None
    error: str | None = None


@dataclass(frozen=True)
class LoadSummary:
    target: str
    requests: int
    succeeded: int
    failed: int
    error_rate: float
    requests_per_second: float
    p50_ms: float
    p95_ms: float
    p99_ms: float
    max_ms: float
    errors: dict[str, int]


def parse_target(value: str) -> Target:
    name, separator, url = value.partition("=")
    parsed = urlparse(url)
    if (
        not separator
        or not name.strip()
        or parsed.scheme not in {"http", "https"}
        or not parsed.netloc
    ):
        raise argparse.ArgumentTypeError("targets must use NAME=http(s)://host/path")
    return Target(name=name.strip(), url=url)


def request_once(
    target: Target, *, timeout_seconds: float, opener: OpenUrl = urlopen
) -> RequestResult:
    request = Request(
        target.url,
        headers={"Accept": "*/*", "User-Agent": "SolaraHire-load-gate/1.0"},
    )
    started = time.perf_counter()
    try:
        with opener(request, timeout=timeout_seconds) as response:
            response.read(1)
            status = response.status
        error = None if 200 <= status < 400 else f"http_{status}"
    except HTTPError as exception:
        status = exception.code
        error = f"http_{exception.code}"
    except (OSError, URLError):
        status = None
        error = "transport_error"
    return RequestResult(
        duration_ms=(time.perf_counter() - started) * 1000,
        status=status,
        error=error,
    )


def percentile(values: Sequence[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def summarize(
    target: Target, results: Sequence[RequestResult], elapsed_seconds: float
) -> LoadSummary:
    durations = [result.duration_ms for result in results]
    errors = Counter(result.error for result in results if result.error is not None)
    failed = sum(errors.values())
    return LoadSummary(
        target=target.name,
        requests=len(results),
        succeeded=len(results) - failed,
        failed=failed,
        error_rate=failed / len(results),
        requests_per_second=len(results) / elapsed_seconds,
        p50_ms=percentile(durations, 0.50),
        p95_ms=percentile(durations, 0.95),
        p99_ms=percentile(durations, 0.99),
        max_ms=max(durations),
        errors=dict(errors),
    )


def run_target(
    target: Target,
    *,
    request_count: int,
    concurrency: int,
    timeout_seconds: float,
    opener: OpenUrl = urlopen,
) -> LoadSummary:
    request_once(target, timeout_seconds=timeout_seconds, opener=opener)
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = tuple(
            executor.map(
                lambda _: request_once(
                    target,
                    timeout_seconds=timeout_seconds,
                    opener=opener,
                ),
                range(request_count),
            )
        )
    return summarize(target, results, time.perf_counter() - started)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", action="append", type=parse_target)
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=float, default=10)
    parser.add_argument("--max-error-rate", type=float, default=0)
    parser.add_argument("--max-p95-ms", type=float)
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.requests < 1 or args.concurrency < 1 or args.timeout_seconds <= 0:
        print("ERROR requests, concurrency, and timeout must be positive.")
        return 2
    if not 0 <= args.max_error_rate <= 1:
        print("ERROR --max-error-rate must be between 0 and 1.")
        return 2
    if args.max_p95_ms is not None and args.max_p95_ms <= 0:
        print("ERROR --max-p95-ms must be positive.")
        return 2

    targets = args.target or [parse_target(value) for value in DEFAULT_TARGETS]
    summaries = [
        run_target(
            target,
            request_count=args.requests,
            concurrency=args.concurrency,
            timeout_seconds=args.timeout_seconds,
        )
        for target in targets
    ]
    failed = any(
        summary.error_rate > args.max_error_rate
        or (args.max_p95_ms is not None and summary.p95_ms > args.max_p95_ms)
        for summary in summaries
    )

    if args.json:
        print(json.dumps([asdict(summary) for summary in summaries], indent=2, sort_keys=True))
    else:
        for summary in summaries:
            print(
                f"{summary.target}: {summary.succeeded}/{summary.requests} ok, "
                f"{summary.requests_per_second:.1f} req/s, "
                f"p50={summary.p50_ms:.1f}ms p95={summary.p95_ms:.1f}ms "
                f"p99={summary.p99_ms:.1f}ms max={summary.max_ms:.1f}ms"
            )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

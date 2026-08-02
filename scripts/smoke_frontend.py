"""Non-destructive smoke checks for the canonical Solara Hire web boundary."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

MAX_RESPONSE_BYTES = 512 * 1024
DEFAULT_TIMEOUT_SECONDS = 10.0


class ResponseHeaders(Protocol):
    def get_content_type(self) -> str: ...


class SmokeResponse(Protocol):
    status: int
    headers: ResponseHeaders

    def __enter__(self) -> SmokeResponse: ...

    def __exit__(self, *args: object) -> None: ...

    def read(self, amount: int = -1) -> bytes: ...


OpenUrl = Callable[..., SmokeResponse]


@dataclass(frozen=True)
class EndpointCheck:
    """One bounded HTTP assertion in the cutover smoke gate."""

    name: str
    url: str
    content_type: str
    marker: bytes


class SmokeCheckError(RuntimeError):
    """Raised when a canonical web endpoint is not ready."""


def normalize_base_url(value: str, *, setting_name: str) -> str:
    """Validate and normalize one user-provided HTTP origin."""

    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError(f"{setting_name} must be an absolute HTTP(S) URL.")
    return normalized


def build_checks(api_url: str, frontend_url: str) -> tuple[EndpointCheck, ...]:
    """Build the fixed, non-mutating cutover checks."""

    api_base = normalize_base_url(api_url, setting_name="--api-url")
    frontend_base = normalize_base_url(frontend_url, setting_name="--frontend-url")
    return (
        EndpointCheck(
            name="FastAPI liveness",
            url=f"{api_base}/api/v1/health/live",
            content_type="application/json",
            marker=b'"status":"ok"',
        ),
        EndpointCheck(
            name="FastAPI readiness",
            url=f"{api_base}/api/v1/health/ready",
            content_type="application/json",
            marker=b'"status":"ready"',
        ),
        EndpointCheck(
            name="Next.js home",
            url=f"{frontend_base}/",
            content_type="text/html",
            marker=b"Solara Hire",
        ),
        EndpointCheck(
            name="Next.js workspace",
            url=f"{frontend_base}/workspace",
            content_type="text/html",
            marker=b"Drop your resume here.",
        ),
    )


def run_check(
    check: EndpointCheck,
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    opener: OpenUrl = urlopen,
) -> None:
    """Run one bounded HTTP check without transmitting product data."""

    request = Request(
        check.url,
        headers={
            "Accept": check.content_type,
            "User-Agent": "SolaraHire-cutover-smoke/1.0",
        },
    )

    try:
        with opener(request, timeout=timeout_seconds) as response:
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if response.status != 200:
                raise SmokeCheckError(f"{check.name} returned HTTP {response.status}.")
            if len(body) > MAX_RESPONSE_BYTES:
                raise SmokeCheckError(
                    f"{check.name} exceeded the {MAX_RESPONSE_BYTES}-byte smoke limit."
                )
            actual_content_type = response.headers.get_content_type()
            if actual_content_type != check.content_type:
                raise SmokeCheckError(
                    f"{check.name} returned {actual_content_type}, expected {check.content_type}."
                )
            if check.marker not in body:
                raise SmokeCheckError(
                    f"{check.name} did not contain its expected readiness marker."
                )
    except HTTPError as error:
        raise SmokeCheckError(f"{check.name} returned HTTP {error.code}.") from error
    except URLError as error:
        raise SmokeCheckError(f"{check.name} is unavailable.") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the running Solara Hire API and canonical Next.js routes "
            "without sending resume data or calling job providers."
        )
    )
    parser.add_argument("--api-url", default="http://127.0.0.1:8000")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:3000")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.timeout_seconds <= 0:
        print("ERROR --timeout-seconds must be greater than zero.", file=sys.stderr)
        return 2

    try:
        checks = build_checks(args.api_url, args.frontend_url)
        for check in checks:
            run_check(check, timeout_seconds=args.timeout_seconds)
            print(f"PASS {check.name}")
    except (SmokeCheckError, ValueError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1

    print("Solara Hire canonical web boundary is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

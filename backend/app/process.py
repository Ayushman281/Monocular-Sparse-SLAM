import asyncio
import os
import signal
from pathlib import Path
from .errors import JobError


async def run_process(args: list[str], log: Path, timeout: float, *, stdout=None):
    """No shell. Kill the whole POSIX group on timeout or task cancellation."""
    with log.open("ab") as handle:
        proc = await asyncio.create_subprocess_exec(
            *map(str, args), stdout=stdout if stdout is not None else handle,
            stderr=handle, start_new_session=True,
        )
        try:
            await asyncio.wait_for(proc.wait(), timeout)
        except (asyncio.TimeoutError, asyncio.CancelledError) as exc:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await proc.wait()
            if isinstance(exc, asyncio.CancelledError):
                raise
            raise JobError("Processing timed out. Try a shorter, lower-resolution clip.", "timeout") from exc
        return proc.returncode

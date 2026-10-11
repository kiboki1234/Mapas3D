from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Iterator

from app.models.schemas import GenerationJob, GenerationRequest, JobEvent, JobStatus


class JobRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self._initialize()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=20)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    progress INTEGER NOT NULL,
                    request_json TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    error TEXT,
                    cancel_requested INTEGER NOT NULL DEFAULT 0,
                    cached_from TEXT,
                    events_json TEXT NOT NULL DEFAULT '[]',
                    artifacts_json TEXT NOT NULL DEFAULT '{}'
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_jobs_request_hash ON jobs(request_hash, status)"
            )

    def create(self, job: GenerationJob, request_hash: str) -> None:
        with self.lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO jobs (
                    id, status, progress, request_json, request_hash, created_at, updated_at,
                    error, cancel_requested, cached_from, events_json, artifacts_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.status.value,
                    job.progress,
                    job.request.model_dump_json(),
                    request_hash,
                    job.created_at.isoformat(),
                    job.updated_at.isoformat(),
                    job.error,
                    int(job.cancel_requested),
                    job.cached_from,
                    json.dumps([event.model_dump(mode="json") for event in job.events]),
                    json.dumps(job.artifacts),
                ),
            )

    def _from_row(self, row: sqlite3.Row) -> GenerationJob:
        return GenerationJob(
            id=row["id"],
            status=JobStatus(row["status"]),
            progress=row["progress"],
            request=GenerationRequest.model_validate_json(row["request_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            error=row["error"],
            cancel_requested=bool(row["cancel_requested"]),
            cached_from=row["cached_from"],
            events=[JobEvent.model_validate(item) for item in json.loads(row["events_json"])],
            artifacts=json.loads(row["artifacts_json"]),
        )

    def get(self, job_id: str) -> GenerationJob | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return self._from_row(row) if row else None

    def find_completed(self, request_hash: str) -> GenerationJob | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM jobs
                WHERE request_hash = ? AND status = 'completed'
                ORDER BY updated_at DESC LIMIT 1
                """,
                (request_hash,),
            ).fetchone()
        return self._from_row(row) if row else None

    def update(
        self,
        job_id: str,
        *,
        status: JobStatus | None = None,
        progress: int | None = None,
        error: str | None = None,
        cancel_requested: bool | None = None,
        artifacts: dict[str, str] | None = None,
        event: JobEvent | None = None,
    ) -> GenerationJob:
        with self.lock:
            job = self.get(job_id)
            if job is None:
                raise KeyError(job_id)
            if status is not None:
                job.status = status
            if progress is not None:
                job.progress = progress
            if error is not None:
                job.error = error
            if cancel_requested is not None:
                job.cancel_requested = cancel_requested
            if artifacts is not None:
                job.artifacts = artifacts
            if event is not None:
                job.events.append(event)
            job.updated_at = datetime.now(timezone.utc)
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE jobs SET status=?, progress=?, updated_at=?, error=?, cancel_requested=?,
                        events_json=?, artifacts_json=? WHERE id=?
                    """,
                    (
                        job.status.value,
                        job.progress,
                        job.updated_at.isoformat(),
                        job.error,
                        int(job.cancel_requested),
                        json.dumps([item.model_dump(mode="json") for item in job.events]),
                        json.dumps(job.artifacts),
                        job.id,
                    ),
                )
            return job


def recover_interrupted_jobs(repository: JobRepository) -> None:
    active = tuple(status.value for status in JobStatus if status not in {JobStatus.completed, JobStatus.failed, JobStatus.cancelled})
    placeholders = ",".join("?" for _ in active)
    with repository._connect() as connection:
        connection.execute(
            f"UPDATE jobs SET status='failed', error='El proceso local se interrumpió antes de completar el trabajo.' WHERE status IN ({placeholders})",
            active,
        )


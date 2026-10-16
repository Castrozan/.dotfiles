"""SQLite metadata facade; never reads harness session stores."""

import time

from . import host_records, job_records, session_records, status_view, storage
from .snapshots import normalize as normalize
from .job_intents import DispatchIntent as DispatchIntent
from .session_records import Observation as Observation


class Registry:
    def __init__(self, path, clock=time.time):
        self.clock = clock
        self.db = storage.connect(path)

    def close(self):
        self.db.close()

    def host(self, host):
        return host_records.host(self.db, host)

    def confirm_host(self, host, transport, evidence):
        return host_records.confirm(self.db, self.clock, host, transport, evidence)

    def ingest(self, host, observation):
        return session_records.ingest(self.db, self.clock, host, observation)

    def failure(self, host, kind):
        return host_records.failure(self.db, self.clock, host, kind)

    def agent(self, host, pane, session):
        return session_records.agent(self.db, host, pane, session)

    def assign(self, host, pane, session, owner, task):
        return session_records.assign(self.db, (host, pane, session), owner, task)

    def status(self, live_hosts=(), freshness=300, limit=500):
        return status_view.status(self.db, self.clock(), live_hosts, freshness, limit)

    def job(self, request_id):
        return job_records.job(self.db, request_id)

    def reserve(self, intent):
        return job_records.reserve(self.db, self.clock, intent)

    def update_job(self, request_id, state, **values):
        return job_records.update(self.db, self.clock, request_id, state, values)

    def verify(self, request_id, evidence):
        return job_records.verify(self.db, self.clock, request_id, evidence)

    def reconcile(self, request_id, evidence, remote_task_id=None, outcome=None):
        return job_records.reconcile(
            self.db, self.clock, request_id, evidence, (remote_task_id, outcome)
        )

    def event(self, host, envelope, evidence):
        return host_records.event(self.db, self.clock, host, envelope, evidence)

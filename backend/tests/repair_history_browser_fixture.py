"""Disposable server used exclusively by the Chrome history test."""
import socket
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep

import uvicorn
from fastapi import FastAPI, Request
from pydantic import TypeAdapter

from app.api.v1.endpoints.repair import router
from app.services.repair.history import HistoryPage, StoredRecovery
from app.services.repair.integration import RepairBindings, RepairService
from examples.member6_demo import DemoTeam, GraphDemo


class BrowserHistoryFixture:
    def __init__(self, directory):
        self.paths = {}
        self.codec = TypeAdapter(StoredRecovery)
        for name in ("first", "slow", "rollback"):
            team = DemoTeam(regression=True, workflow_id=name) if name == "rollback" else GraphDemo(workflow_id=name)
            _, outcome = RepairService(team.bindings()).run(team.scope, Request({"type": "http"}), "recover")
            assert outcome.status == ("rolled_back" if name == "rollback" else "promoted")
            path = Path(directory, name + ".json")
            path.write_bytes(self.codec.dump_json(StoredRecovery("recovery-" + name, team.finished)))
            self.paths[team.scope] = path

    def allows(self, request, scope, action):
        return request.cookies.get("fixture_session") == "reader" and scope in self.paths and action == "history"

    def read(self, request, scope, offset, limit):
        if not self.allows(request, scope, "history"):
            raise PermissionError()
        if scope.workflow_id == "slow":
            sleep(0.5)
        records = (self.codec.validate_json(self.paths[scope].read_bytes()),)
        return HistoryPage(scope, records[offset:offset + limit])


if __name__ == "__main__":
    with TemporaryDirectory() as directory, socket.socket() as listener:
        store = BrowserHistoryFixture(directory)
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/repair")
        app.state.repair_service = RepairService(RepairBindings(access=store, history=store))
        listener.bind(("127.0.0.1", 0))
        listener.listen()
        print(listener.getsockname()[1], flush=True)
        uvicorn.Server(uvicorn.Config(app, log_level="error")).run(sockets=[listener])

"""Check the prototype's execution boundary, determinism, and HTTP transport."""

import json
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server import make_server
from session import DEFAULTS, Session


def model_state(session):
    """Exclude transport metadata when comparing scientific state."""
    state = session.snapshot()
    return state["time"], state["agents"], state["history"]


class SessionTests(unittest.TestCase):
    """Exercise commands without a browser or editor dependency."""

    def test_seed_and_reset_reproduce(self):
        """The same seed gives the same trajectory after reset."""
        session = Session()
        for _ in range(3):
            session.command("step")
        expected = model_state(session)
        old_run = session.run_id
        session.command("reset", DEFAULTS)
        for _ in range(3):
            session.command("step")
        self.assertEqual(expected, model_state(session))
        self.assertNotEqual(old_run, session.run_id)

    def test_observing_does_not_change_results(self):
        """Extra clients and frame requests cannot consume RNG or advance time."""
        observed, headless = Session(), Session()
        for _ in range(3):
            for _ in range(4):
                observed.snapshot()
            observed.command("step")
            headless.command("step")
        self.assertEqual(model_state(observed), model_state(headless))

    def test_pause_and_server_clock(self):
        """Only an explicitly running session advances on a clock tick."""
        session = Session()
        session.tick()
        self.assertEqual(session.model.time, 0)
        session.command("play")
        session.tick()
        self.assertEqual(session.model.time, 1)
        session.command("pause")
        session.tick()
        self.assertEqual(session.model.time, 1)

    def test_bad_parameters_preserve_model(self):
        """Failed reset validation leaves the previous model intact."""
        session = Session()
        before = model_state(session)
        for bad in (
            {"density": 1},
            {"seed": -1},
            {"homophily": float("nan")},
            {"extra": 1},
        ):
            with self.assertRaises(ValueError):
                session.command("reset", bad)
        self.assertEqual(before, model_state(session))

    def test_snapshots_are_detached(self):
        """Clients cannot mutate the session through its returned data."""
        session = Session()
        state = session.snapshot()
        state["agents"][0]["x"] = -999
        state["history"][0]["happy"] = -999
        state["parameters"]["seed"] = -999
        self.assertNotEqual(state, session.snapshot())
        self.assertEqual(session.parameters, DEFAULTS)

    def test_revision_and_reload(self):
        """Frames are ordered across both steps and code reload/reset."""
        session = Session()
        previous = session.snapshot()
        session.command("step")
        stepped = session.snapshot()
        session.command("reload", DEFAULTS)
        reloaded = session.snapshot()
        self.assertLess(previous["revision"], stepped["revision"])
        self.assertLess(stepped["revision"], reloaded["revision"])
        self.assertEqual(previous["agents"], reloaded["agents"])
        self.assertEqual(reloaded["time"], 0)

    def test_http_clients_share_session(self):
        """Both hosts see one state, protected by a local session token."""
        server, session, token = make_server(0)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{server.server_port}"

        def call(endpoint, body=None, auth=True, origin=None):
            headers = {"Content-Type": "application/json"}
            if auth:
                headers["X-Mesa-Token"] = token
            if origin:
                headers["Origin"] = origin
            request = Request(
                base + endpoint,
                data=json.dumps(body).encode() if body is not None else None,
                headers=headers,
            )
            with urlopen(request, timeout=5) as response:
                return json.load(response)

        try:
            with self.assertRaises(HTTPError) as error:
                call("/api/state", auth=False)
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
            first = call("/api/state")
            changed = call("/api/command", {"action": "step"})
            other_client = call("/api/state")
            self.assertEqual(first["run_id"], changed["run_id"])
            self.assertEqual(changed, other_client)
            self.assertEqual(session.model.time, 1)
            with self.assertRaises(HTTPError) as error:
                call("/api/command", {"action": "reset"}, origin="https://example.com")
            self.assertEqual(error.exception.code, 403)
            error.exception.close()
            with self.assertRaises(HTTPError) as error:
                call("/api/command", {"action": ["bad"]})
            self.assertEqual(error.exception.code, 400)
            error.exception.close()
            with urlopen(base + "/", timeout=5) as response:
                self.assertIn(b"<mesa-workspace>", response.read())
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=2)


if __name__ == "__main__":
    unittest.main()

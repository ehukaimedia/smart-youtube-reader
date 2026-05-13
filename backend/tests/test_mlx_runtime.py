import unittest
from unittest.mock import patch

from app import mlx_runtime


class _RunningProc:
    def poll(self):
        return None


class MlxRuntimeTests(unittest.TestCase):
    def tearDown(self):
        mlx_runtime._server_proc = None
        mlx_runtime._current_model = None
        mlx_runtime._health_cache = (None, 0.0, False)

    def test_ensure_server_reprobes_running_model_when_health_cache_expired(self):
        model = "mlx-community/gemma-4-e4b-it-4bit"
        mlx_runtime._server_proc = _RunningProc()
        mlx_runtime._current_model = model
        mlx_runtime._health_cache = (model, 0.0, False)

        probes = []

        def healthy_probe(probed_model):
            probes.append(probed_model)
            return True

        with (
            patch.object(mlx_runtime, "_is_healthy_for_model", side_effect=healthy_probe),
            patch.object(mlx_runtime, "_stop_server_locked") as stop_server,
            patch.object(mlx_runtime, "mlx_available") as mlx_available,
        ):
            mlx_runtime.ensure_server(model, timeout=1)

        self.assertEqual(probes, [model])
        stop_server.assert_not_called()
        mlx_available.assert_not_called()


if __name__ == "__main__":
    unittest.main()

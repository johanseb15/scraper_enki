from pathlib import Path

from src.infraestructura.real_world_trace_artifact import build_real_world_trace_artifacts


def main():
    root = Path(__file__).parents[1]
    metrics = build_real_world_trace_artifacts(root, root / "data")
    for key, value in metrics.items():
        print(f"{key}={value}")


if __name__ == "__main__":
    main()

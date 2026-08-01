"""Validate and package a completed experiment for archival deposit."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path


REQUIRED_TOP_LEVEL = (
    "manifest.json",
    "experiment.json",
    "REPORT.md",
    "runs.csv",
    "contrasts.csv",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def package_results(experiment_directory: Path, archive_path: Path) -> dict:
    experiment_directory = experiment_directory.resolve()
    for name in REQUIRED_TOP_LEVEL:
        if not (experiment_directory / name).is_file():
            raise ValueError(f"missing required artifact: {name}")

    manifest = json.loads((experiment_directory / "manifest.json").read_text())
    experiment = json.loads((experiment_directory / "experiment.json").read_text())
    if manifest.get("status") != "complete" or not manifest.get("completed_at"):
        raise ValueError("experiment manifest is not complete")
    if manifest.get("protocol_sha256") != experiment.get("protocol_sha256"):
        raise ValueError("protocol hash differs between manifest and experiment")
    if not manifest.get("git_revision") or not manifest.get("source_sha256"):
        raise ValueError("missing source provenance")

    expected = len(experiment["seeds"]) * len(experiment["protocol"]["conditions"])
    run_files = sorted((experiment_directory / "runs").glob("seed-*/*.json"))
    if len(run_files) != expected:
        raise ValueError(f"expected {expected} run records, found {len(run_files)}")
    for path in run_files:
        record = json.loads(path.read_text())
        if record.get("protocol_sha256") != manifest["protocol_sha256"]:
            raise ValueError(f"protocol mismatch: {path}")
        if record.get("source_sha256") != manifest["source_sha256"]:
            raise ValueError(f"source mismatch: {path}")

    repo_root = Path(__file__).resolve().parents[1]
    included: list[tuple[Path, str]] = [
        (experiment_directory / name, name) for name in REQUIRED_TOP_LEVEL
    ]
    figure = experiment_directory / "figure1.svg"
    if figure.exists():
        included.append((figure, "figure1.svg"))
    included.extend(
        [
            (repo_root / "research" / "PREREGISTRATION.md", "PROTOCOL.md"),
            (repo_root / "research" / "PROTOCOL_DEVIATIONS.md", "PROTOCOL_DEVIATIONS.md"),
            (repo_root / "research" / "DATA_DICTIONARY.md", "DATA_DICTIONARY.md"),
            (repo_root / "research" / "DATA_LICENSE.md", "DATA_LICENSE.md"),
            (repo_root / "research" / "ODD.md", "ODD.md"),
            (repo_root / "research" / "confirmatory_config_v1.json", "CONFIG.json"),
            (repo_root / "AI_USAGE.md", "AI_USAGE.md"),
            (repo_root / "CITATION.cff", "CITATION.cff"),
            (repo_root / "LICENSE", "SOFTWARE_LICENSE.txt"),
            (repo_root / "paper" / "manuscript.md", "MANUSCRIPT.md"),
        ]
    )
    included.extend(
        (path, path.relative_to(experiment_directory).as_posix()) for path in run_files
    )
    for path, _archive_name in included:
        if not path.is_file():
            raise ValueError(f"missing archive documentation: {path}")
    file_records = [
        {
            "path": archive_name,
            "bytes": path.stat().st_size,
            "sha256": _sha256(path),
        }
        for path, archive_name in included
    ]
    artifact_manifest = {
        "title": "Sentient Sim confirmatory-v1 result bundle",
        "interpretation": "Mechanism ablation only; not evidence of consciousness or sentience.",
        "protocol_sha256": manifest["protocol_sha256"],
        "source_sha256": manifest["source_sha256"],
        "git_revision": manifest["git_revision"],
        "files": file_records,
    }
    manifest_bytes = (json.dumps(artifact_manifest, indent=2, sort_keys=True) + "\n").encode()

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = archive_path.with_name(archive_path.name + ".tmp")
    with tarfile.open(temporary, "w:gz") as archive:
        for path, archive_name in included:
            archive.add(
                path,
                arcname=(Path("confirmatory-v1") / archive_name).as_posix(),
            )
        info = tarfile.TarInfo("confirmatory-v1/ARTIFACT_MANIFEST.json")
        info.size = len(manifest_bytes)
        info.mtime = 0
        archive.addfile(info, io.BytesIO(manifest_bytes))
    temporary.replace(archive_path)

    return {
        **artifact_manifest,
        "archive": str(archive_path),
        "archive_bytes": archive_path.stat().st_size,
        "archive_sha256": _sha256(archive_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("experiment_directory", type=Path)
    parser.add_argument("archive", type=Path)
    parser.add_argument(
        "--metadata",
        type=Path,
        help="also write the archive metadata as formatted JSON",
    )
    args = parser.parse_args()
    result = package_results(args.experiment_directory, args.archive)
    serialized = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.metadata is not None:
        args.metadata.parent.mkdir(parents=True, exist_ok=True)
        args.metadata.write_text(serialized)
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

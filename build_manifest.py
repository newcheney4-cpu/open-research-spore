#!/usr/bin/env python3
"""Preview or rebuild the formal package manifest from the release tree."""
import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
PACK = Path(__file__).resolve().parent
sys.path.insert(0, str(PACK / "payload" / "research" / "tools"))
import _spore_core as core  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        profile = "mentor" if (PACK / "payload" / "research").is_dir() else "student"
        individual = PACK / Path(*core.PurePosixPath(core.PROFILE_PAYLOAD[profile]).parts)
        release = core.load_release(individual)
        files = {}
        plan = core.Plan()
        for rel in core.walk_files(PACK):
            if rel == "MANIFEST.json" or core.is_dev_path(rel):
                continue
            source = PACK / Path(*core.PurePosixPath(rel).parts)
            data = source.read_bytes()
            files[rel] = data
            plan.source(source, data)
        manifest = core.build_package_manifest(
            files, profile, release["version"], kind="release")
        manifest["note"] = "Formal release snapshot; development scratch is excluded."
        manifest["source"] = {
            "artifact": "open-research-spore-v2.1.0.zip",
            "sha256": "663f43920520800cf67ad991ba33e3b2755f7d74c362b82675d3643951a185a1",
        }
        target = PACK / "MANIFEST.json"
        issue = core.blocker(PACK, target)
        if issue:
            raise core.SporeConflict(issue)
        old = target.read_bytes() if target.is_file() else None
        data = core.json_bytes(manifest)
        if old != data:
            plan.add("MANIFEST.json", target, data,
                     "replace" if old is not None else "write",
                     observed=core.observe(target))
        print("manifest: %s %s (%s) files=%d buildId=%s"
              % (manifest["name"], manifest["version"], profile,
                 len(files), manifest["buildId"]))
        if not args.write:
            print("dry run: no files written; use --write to commit")
            return 0
        core.commit(plan)
        print("committed: %s" % target)
        return 0
    except core.SporeError as exc:
        print("ERROR %s" % exc)
        return exc.exit_code


if __name__ == "__main__":
    sys.exit(main())

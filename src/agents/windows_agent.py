"""Windows Agent

Lightweight local agent that runs the existing pre-deployment checks and
digital-hygiene assessor and writes a JSON report to the instance/agent_reports
directory. This is intentionally self-contained so operators can run it on
Windows hosts and collect the resulting report for central ingestion.
"""
from __future__ import annotations

import json
import socket
from datetime import datetime, timezone
from pathlib import Path

from src.security.assessment.assessor import BusinessInfo, DigitalHygieneAssessor
from src.security.deployment.checker import PreDeploymentChecker

REPORT_DIR = Path("instance/agent_reports")


def collect_local_report(business_name: str = "local-host") -> dict:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Run pre-deployment checks
    checker = PreDeploymentChecker(project_root=str(Path.cwd()))
    readiness = checker.run_all()

    # Minimal business info placeholder so assessor can produce compatible output
    bi = BusinessInfo(name=business_name, id=socket.gethostname())
    assessor = DigitalHygieneAssessor(bi, assessment_tier="automated")
    # The assessor expects to run its own automated checks; run and keep results
    assessment = assessor.run_assessment()

    out = {
        "collected_at": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "hostname": socket.gethostname(),
        "readiness": readiness.to_dict(),
        "assessment": {
            "score": assessment.score,
            "total_possible": assessment.total_possible,
            "certification_level": assessment.certification_level,
            "controls": {k: v.__dict__ for k, v in assessment.controls.items()},
        },
    }

    path = REPORT_DIR / f"{out['hostname']}-{int(datetime.now(timezone.utc).timestamp())}.json"
    path.write_text(json.dumps(out, indent=2))
    return {"report_path": str(path), "report": out}


if __name__ == '__main__':
    import argparse

    p = argparse.ArgumentParser(description='Run local Windows agent checks')
    p.add_argument('--name', help='Business name to include in assessment', default='local-host')
    args = p.parse_args()
    r = collect_local_report(args.name)
    print(f"Report written: {r['report_path']}")

"""
Automated Pytest Test Suite for Ctcae Adverse Event Grader.
Domain: Radiology & Neuroimaging Systems
Standard: ACR RADS / Fleischner Society / ASPECTS Guidelines
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import tempfile
import pytest
from agents.base import PHIGuard, AuditLogger, SecurityException, AuditTrail
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.workers import InvariantQCWorker, SafetyEscalationWorker, ProtocolConformanceWorker
from agents.supervisor import SystemSupervisor
from cli import main
import ctcae


def test_phi_guard_enforcement():
    with pytest.raises(SecurityException):
        PHIGuard.assert_no_phi("Patient MRN-994827 blood culture positive for Staphylococcus")

    # Clean text passes
    PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")


def test_specialized_workers():
    # Worker 1: QC Invariant
    p1 = SystemTaskPayload(task_id="T1", target_identifier="KEY-01", primary_metric=35.0)
    alerts1 = InvariantQCWorker.evaluate(p1)
    assert len(alerts1) == 1
    assert alerts1[0].urgency == UrgencyLevel.ELEVATED

    # Worker 2: Safety
    p2 = SystemTaskPayload(task_id="T2", target_identifier="KEY-02", primary_metric=10.0, is_critical_flag=True)
    alerts2 = SafetyEscalationWorker.evaluate(p2)
    assert len(alerts2) == 1
    assert alerts2[0].urgency == UrgencyLevel.CRITICAL_STAT

    # Worker 3: Protocol Conformance
    p3 = SystemTaskPayload(task_id="T3", target_identifier="KEY-03", primary_metric=10.0, status_descriptor="DISCORDANT_ANOMALY")
    alerts3 = ProtocolConformanceWorker.evaluate(p3)
    assert len(alerts3) == 1


def test_supervisor_consensus_and_audit():
    supervisor = SystemSupervisor(model_provider="mock")
    payload = SystemTaskPayload(
        task_id="TASK-PROD-01",
        target_identifier="KEY-PROD-01",
        primary_metric=12.0,
        secondary_metric=4.0,
        status_descriptor="NOMINAL"
    )
    dossier = supervisor.process_task(payload)
    assert dossier.overall_urgency == UrgencyLevel.ROUTINE
    assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED
    assert dossier.audit_hash != ""

    # Verify cryptographic audit trail
    assert AuditLogger.verify_integrity() is True

    # CLI tests
    assert main(["audit", "--task-id", "CLI-TEST-01"]) == 0
    assert main(["chat", "Explain", "specifications"]) == 0
    assert main(["verify-audit"]) == 0


def test_process_csv_file_not_found():
    """process_csv raises FileNotFoundError for missing input."""
    with pytest.raises(FileNotFoundError):
        ctcae.process_csv("nonexistent_file.csv", "output.csv")


def test_process_csv_empty_headers():
    """process_csv raises ValueError for CSV with no headers."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
        f.write("")
        tmp_path = f.name
    try:
        with pytest.raises(ValueError):
            ctcae.process_csv(tmp_path, "output.csv")
    finally:
        os.unlink(tmp_path)


def test_process_csv_roundtrip():
    """process_csv correctly processes a valid CSV and writes output."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8", newline="") as f:
        f.write("patient_id,age,sex,prior_vte,cancer,immobility,surgery\n")
        f.write("P001,68,M,0,1,1,0\n")
        f.write("P002,45,F,0,0,0,1\n")
        input_path = f.name

    output_path = input_path.replace(".csv", "_out.csv")
    try:
        results = ctcae.process_csv(input_path, output_path)
        assert len(results) == 2
        assert all("score" in r and "tier" in r for r in results)
        assert os.path.isfile(output_path)
    finally:
        os.unlink(input_path)
        if os.path.isfile(output_path):
            os.unlink(output_path)


def test_cli_batch_missing_file():
    """CLI batch command returns non-zero exit code for missing input."""
    exit_code = main(["batch", "-i", "nonexistent_input.csv"])
    assert exit_code == 1


def test_audit_trail_integrity_tampering_detected():
    """Audit trail integrity verification detects tampering."""
    trail = AuditTrail(secret_key="test-key-for-integrity")
    trail.log("test", "test_tier", "TEST_EVENT", {"data": "value1"})
    trail.log("test", "test_tier", "TEST_EVENT", {"data": "value2"})
    assert trail.verify_integrity() is True

    # Tamper with an entry
    trail.logs[0]["payload_hash"] = "tampered_hash"
    assert trail.verify_integrity() is False


def test_audit_trail_requires_secret_or_env():
    """AuditTrail generates ephemeral key when no secret is provided."""
    import warnings
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        trail = AuditTrail(secret_key="test-key")
        assert len(trail.logs) == 0
        assert len(w) == 0  # No warning when key is provided

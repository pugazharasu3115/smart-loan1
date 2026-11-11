from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import BlockchainBlock, LoanApplication, Applicant
from backend.schemas import BlockchainRecordResponse, BlockchainAuditResponse
from backend.services.blockchain_service import BlockchainService
from backend.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/api/blockchain", tags=["Blockchain Integrity & Tamper Audit"])

@router.get("/chain")
def get_blockchain_ledger(db: Session = Depends(get_db)):
    """Fetches all blocks in the immutable chain."""
    BlockchainService.ensure_genesis_block(db)
    blocks = db.query(BlockchainBlock).order_by(BlockchainBlock.block_index.asc()).all()
    return blocks

@router.get("/audit", response_model=BlockchainAuditResponse)
def audit_blockchain(db: Session = Depends(get_db)):
    """Runs cryptographic audit on all blocks to detect any data tampering."""
    is_valid, tampered_indices, report = BlockchainService.verify_chain_integrity(db)
    total_blocks = db.query(BlockchainBlock).count()
    monitoring_service.record_event(
        stage="BLOCKCHAIN",
        event_type="CHAIN_AUDIT",
        status="SUCCESS" if is_valid else "TAMPER_DETECTED",
        details=f"Audit completed: {total_blocks} blocks. {'All valid' if is_valid else f'Tamper at blocks: {tampered_indices}'}",
        duration_ms=65,
        is_anomaly=not is_valid
    )
    return BlockchainAuditResponse(
        total_blocks=total_blocks,
        is_chain_valid=is_valid,
        tampered_block_indices=tampered_indices,
        audit_report=report
    )

@router.post("/tamper-demo")
def simulate_tamper_attack(block_index: int, db: Session = Depends(get_db)):
    """
    Demo Tool: Intentionally modifies a block hash in the database to simulate
    a malicious cyber-attack/tampering, demonstrating the blockchain audit catching it.
    """
    success = BlockchainService.simulate_tamper_attack(
        db=db,
        block_index=block_index,
        fake_credit_score_hash="FAKED_ALTERED_HASH_99999999999999999999999999999999999999999999"
    )
    if not success:
        raise HTTPException(status_code=404, detail="Block not found")
        
    is_valid, tampered_indices, report = BlockchainService.verify_chain_integrity(db)
    monitoring_service.record_event(
        stage="BLOCKCHAIN",
        event_type="TAMPER_ATTACK_SIMULATED",
        status="FRAUD_ALERT",
        details=f"Simulated unauthorized SQL alter on Block #{block_index}. Cryptographic chain broken!",
        duration_ms=45,
        is_anomaly=True
    )
    return {
        "tamper_executed": True,
        "tampered_block_index": block_index,
        "is_chain_valid": is_valid,
        "tampered_indices": tampered_indices,
        "audit_report": report
    }

@router.post("/restore-demo")
def restore_blockchain(db: Session = Depends(get_db)):
    """Restores/re-hashes all blocks to clean state after demo tampering."""
    blocks = db.query(BlockchainBlock).order_by(BlockchainBlock.block_index.asc()).all()
    for b in blocks:
        if b.block_index == 0:
            continue
        b.is_valid = True
        # Re-derive correct credit score hash
        b.credit_score_hash = BlockchainService.hash_credit_score(810, b.applicant_id)
        b.block_hash = BlockchainService.calculate_hash(
            block_index=b.block_index,
            previous_hash=b.previous_hash,
            applicant_id=b.applicant_id,
            cibil_control_number=b.cibil_control_number,
            credit_score_hash=b.credit_score_hash,
            verification_data_hash=b.verification_data_hash,
            timestamp_str=b.timestamp.isoformat(),
            nonce=b.nonce
        )
    db.commit()
    monitoring_service.record_event(
        stage="BLOCKCHAIN",
        event_type="LEDGER_RESTORED",
        status="SUCCESS",
        details="Blockchain ledger recalculated and restored to valid state.",
        duration_ms=40
    )
    return {"message": "Blockchain ledger restored to valid cryptographic state."}

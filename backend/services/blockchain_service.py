import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from backend.models import BlockchainBlock, Applicant, LoanApplication

class BlockchainService:
    @staticmethod
    def calculate_hash(
        block_index: int,
        previous_hash: str,
        applicant_id: str,
        cibil_control_number: str,
        credit_score_hash: str,
        verification_data_hash: str,
        timestamp_str: str,
        nonce: int = 0
    ) -> str:
        """Computes SHA-256 hash of the block contents."""
        block_string = (
            f"{block_index}|{previous_hash}|{applicant_id}|"
            f"{cibil_control_number}|{credit_score_hash}|"
            f"{verification_data_hash}|{timestamp_str}|{nonce}"
        )
        return hashlib.sha256(block_string.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_verification_payload(payload: Dict[str, Any]) -> str:
        """Generates cryptographic SHA-256 hash for sensitive verification trail."""
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def hash_credit_score(score: int, applicant_id: str) -> str:
        """Hashes credit score with applicant salt for privacy on blockchain."""
        raw = f"{applicant_id}_SCORE_{score}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def ensure_genesis_block(cls, db: Session) -> BlockchainBlock:
        """Creates the Genesis Block if the chain is empty."""
        genesis = db.query(BlockchainBlock).filter(BlockchainBlock.block_index == 0).first()
        if not genesis:
            timestamp = datetime(2026, 1, 1, 0, 0, 0)
            genesis_hash = cls.calculate_hash(
                block_index=0,
                previous_hash="0" * 64,
                applicant_id="GENESIS-SYSTEM",
                cibil_control_number="CIBIL-GENESIS-000000",
                credit_score_hash=hashlib.sha256(b"GENESIS_CREDIT").hexdigest(),
                verification_data_hash=hashlib.sha256(b"SMART_LOAN_GENESIS_ROOT").hexdigest(),
                timestamp_str=timestamp.isoformat(),
                nonce=0
            )
            genesis = BlockchainBlock(
                block_index=0,
                previous_hash="0" * 64,
                block_hash=genesis_hash,
                applicant_id="GENESIS-SYSTEM",
                cibil_control_number="CIBIL-GENESIS-000000",
                credit_score_hash=hashlib.sha256(b"GENESIS_CREDIT").hexdigest(),
                verification_data_hash=hashlib.sha256(b"SMART_LOAN_GENESIS_ROOT").hexdigest(),
                timestamp=timestamp,
                nonce=0,
                is_valid=True
            )
            db.add(genesis)
            db.commit()
            db.refresh(genesis)
        return genesis

    @classmethod
    def create_verification_block(
        cls,
        db: Session,
        applicant_id: str,
        cibil_control_number: str,
        credit_score: int,
        verification_payload: Dict[str, Any]
    ) -> BlockchainBlock:
        """Appends a new immutable verification block to the chain."""
        cls.ensure_genesis_block(db)
        
        last_block = db.query(BlockchainBlock).order_by(BlockchainBlock.block_index.desc()).first()
        next_index = last_block.block_index + 1 if last_block else 0
        prev_hash = last_block.block_hash if last_block else "0" * 64
        
        now = datetime.utcnow()
        credit_score_hash = cls.hash_credit_score(credit_score, applicant_id)
        verif_hash = cls.hash_verification_payload(verification_payload)
        
        block_hash = cls.calculate_hash(
            block_index=next_index,
            previous_hash=prev_hash,
            applicant_id=applicant_id,
            cibil_control_number=cibil_control_number,
            credit_score_hash=credit_score_hash,
            verification_data_hash=verif_hash,
            timestamp_str=now.isoformat(),
            nonce=100
        )
        
        new_block = BlockchainBlock(
            block_index=next_index,
            previous_hash=prev_hash,
            block_hash=block_hash,
            applicant_id=applicant_id,
            cibil_control_number=cibil_control_number,
            credit_score_hash=credit_score_hash,
            verification_data_hash=verif_hash,
            timestamp=now,
            nonce=100,
            is_valid=True
        )
        db.add(new_block)
        db.commit()
        db.refresh(new_block)
        return new_block

    @classmethod
    def verify_chain_integrity(cls, db: Session) -> Tuple[bool, List[int], str]:
        """Audits the full blockchain for hash tampering or broken links."""
        cls.ensure_genesis_block(db)
        blocks = db.query(BlockchainBlock).order_by(BlockchainBlock.block_index.asc()).all()
        
        tampered_indices = []
        
        for i, block in enumerate(blocks):
            # 1. Check link to previous block
            if i > 0:
                expected_prev = blocks[i - 1].block_hash
                if block.previous_hash != expected_prev:
                    tampered_indices.append(block.block_index)
                    block.is_valid = False
                    continue
            
            # 2. Check block hash recomputation
            recomputed_hash = cls.calculate_hash(
                block_index=block.block_index,
                previous_hash=block.previous_hash,
                applicant_id=block.applicant_id,
                cibil_control_number=block.cibil_control_number,
                credit_score_hash=block.credit_score_hash,
                verification_data_hash=block.verification_data_hash,
                timestamp_str=block.timestamp.isoformat(),
                nonce=block.nonce
            )
            
            if recomputed_hash != block.block_hash:
                tampered_indices.append(block.block_index)
                block.is_valid = False
            else:
                block.is_valid = True
        
        db.commit()
        
        if tampered_indices:
            report = f"TAMPER ALERT: Integrity failure detected at Block(s) {tampered_indices}. Hashes corrupted."
            return False, tampered_indices, report
        
        return True, [], f"BLOCKCHAIN INTEGRITY VERIFIED: All {len(blocks)} blocks valid and untampered."

    @classmethod
    def simulate_tamper_attack(cls, db: Session, block_index: int, fake_credit_score_hash: str) -> bool:
        """Simulates database modification attack for live defense demonstrations."""
        block = db.query(BlockchainBlock).filter(BlockchainBlock.block_index == block_index).first()
        if not block:
            return False
        
        block.credit_score_hash = fake_credit_score_hash
        db.commit()
        return True

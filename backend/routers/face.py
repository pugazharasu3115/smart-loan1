from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.models import Applicant, FaceVerification, LoanApplication
from backend.schemas import FaceVerificationRequest, FaceVerificationResponse
from backend.services.face_service import FaceService
from backend.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/api/face", tags=["Face Biometric Authentication"])

@router.post("/verify", response_model=FaceVerificationResponse)
def verify_face_biometrics(req: FaceVerificationRequest, db: Session = Depends(get_db)):
    applicant = db.query(Applicant).filter(Applicant.applicant_id == req.applicant_id).first()
    if not applicant:
        raise HTTPException(status_code=404, detail="Applicant not found")

    similarity_score, is_matched, live_hash, msg = FaceService.compare_faces(
        live_image_base64=req.image_base64,
        ref_image_base64=req.reference_image_base64 or applicant.registered_face_embedding
    )

    face_record = FaceVerification(
        applicant_id=applicant.applicant_id,
        live_face_hash=live_hash,
        registered_face_hash=applicant.registered_face_embedding[:64] if applicant.registered_face_embedding else None,
        similarity_score=similarity_score,
        threshold=75.0,
        is_matched=is_matched,
        verification_method="OpenCV_Biometric_Embedding"
    )
    db.add(face_record)
    db.commit()

    # Update loan application face status
    loan = db.query(LoanApplication).filter(
        LoanApplication.applicant_id == applicant.applicant_id
    ).order_by(LoanApplication.id.desc()).first()

    if loan:
        loan.face_status = "VERIFIED" if is_matched else "FAILED"
        db.commit()

    monitoring_service.record_event(
        stage="BIOMETRICS",
        event_type="FACE_MATCH",
        status="SUCCESS" if is_matched else "MISMATCH",
        details=f"Cosine similarity: {similarity_score}%. {msg}",
        applicant_id=applicant.applicant_id,
        duration_ms=310,
        is_anomaly=not is_matched
    )

    return FaceVerificationResponse(
        applicant_id=applicant.applicant_id,
        similarity_score=similarity_score,
        threshold=75.0,
        is_matched=is_matched,
        live_face_hash=live_hash,
        status="VERIFIED" if is_matched else "MISMATCH",
        message=msg
    )

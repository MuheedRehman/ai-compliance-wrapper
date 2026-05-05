import uuid
import copy

import pytest

from app.models import AiFeature, FeatureVersion, AiSystem, EvidenceLog
from app.services.feature_service import approve_feature_version, reject_feature_version
from app.services.hashing import sha256_text


def test_initial_feature_version_becomes_approved(client, app_headers, chat_payload, fake_provider, db_session):
    response = client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)

    assert response.status_code == 200

    feature = db_session.query(AiFeature).filter(
        AiFeature.feature_id == "customer_support_bot"
    ).first()

    versions = db_session.query(FeatureVersion).filter(
        FeatureVersion.feature_pk == feature.id
    ).all()

    assert len(versions) == 1
    assert versions[0].status == "approved"
    assert feature.current_feature_version_id == versions[0].feature_version_id


def test_prompt_change_creates_candidate_version(client, app_headers, chat_payload, fake_provider, db_session):
    response = client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)
    assert response.status_code == 200

    chat_payload["messages"][0]["content"] = "You are a stricter support assistant."

    response = client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)
    assert response.status_code == 200

    feature = db_session.query(AiFeature).filter(
        AiFeature.feature_id == "customer_support_bot"
    ).first()

    versions = db_session.query(FeatureVersion).filter(
        FeatureVersion.feature_pk == feature.id
    ).order_by(FeatureVersion.version.asc()).all()

    assert len(versions) == 2
    assert versions[0].status == "approved"
    assert versions[1].status == "candidate"


def test_approve_candidate_supersedes_old_approved_version(client, app_headers, chat_payload, fake_provider, db_session):
    client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)

    chat_payload["messages"][0]["content"] = "You are a stricter support assistant."
    client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)

    feature = db_session.query(AiFeature).filter(
        AiFeature.feature_id == "customer_support_bot"
    ).first()

    candidate = db_session.query(FeatureVersion).filter(
        FeatureVersion.feature_pk == feature.id,
        FeatureVersion.status == "candidate",
    ).first()

    approve_feature_version(
        db_session,
        feature.tenant_id,
        feature.feature_id,
        candidate.feature_version_id,
    )
    db_session.commit()

    versions = db_session.query(FeatureVersion).filter(
        FeatureVersion.feature_pk == feature.id
    ).all()

    statuses = sorted([version.status for version in versions])
    assert statuses == ["approved", "superseded"]

    db_session.refresh(feature)
    assert feature.current_feature_version_id == candidate.feature_version_id


def test_reject_current_approved_without_replacement_is_blocked(client, app_headers, chat_payload, fake_provider, db_session):
    client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)

    feature = db_session.query(AiFeature).filter(
        AiFeature.feature_id == "customer_support_bot"
    ).first()

    approved = db_session.query(FeatureVersion).filter(
        FeatureVersion.feature_pk == feature.id,
        FeatureVersion.status == "approved",
    ).first()

    with pytest.raises(Exception):
        reject_feature_version(
            db_session,
            feature.tenant_id,
            feature.feature_id,
            approved.feature_version_id,
        )


def test_reject_current_approved_with_replacement_repoints_feature(client, app_headers, chat_payload, fake_provider, db_session):
    client.post("/v1/chat/completions", headers=app_headers, json=chat_payload)

    feature = db_session.query(AiFeature).filter(
        AiFeature.feature_id == "customer_support_bot"
    ).first()

    original = db_session.query(FeatureVersion).filter(
        FeatureVersion.feature_pk == feature.id,
        FeatureVersion.status == "approved",
    ).first()

    replacement = FeatureVersion(
        feature_version_id=str(uuid.uuid4()),
        tenant_id=feature.tenant_id,
        feature_pk=feature.id,
        feature_id=feature.feature_id,
        version=2,
        provider="openai",
        model="gpt-4.1-nano",
        prompt_hash=sha256_text("replacement"),
        fingerprint="replacement_fingerprint",
        policy_bundle_version=feature.policy_bundle_version,
        change_reason="test_replacement",
        status="approved",
    )

    db_session.add(replacement)
    db_session.commit()

    reject_feature_version(
        db_session,
        feature.tenant_id,
        feature.feature_id,
        original.feature_version_id,
    )
    db_session.commit()

    db_session.refresh(feature)
    assert feature.current_feature_version_id == replacement.feature_version_id
    assert feature.current_fingerprint == replacement.fingerprint
    assert feature.current_prompt_hash == replacement.prompt_hash


def test_ai_system_crud(client, admin_headers):
    # Create
    payload = {"name": "Test System", "description": "System for testing"}
    response = client.post("/v1/ai-systems", headers=admin_headers, json=payload)
    assert response.status_code == 200
    system = response.json()
    assert system["name"] == "Test System"
    assert system["deployment_status"] == "draft"
    system_id = system["id"]

    # List
    response = client.get("/v1/ai-systems", headers=admin_headers)
    assert response.status_code == 200
    systems = response.json()
    assert any(s["id"] == system_id for s in systems)

    # Get
    response = client.get(f"/v1/ai-systems/{system_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Test System"

    # Update
    update_payload = {"name": "Updated System", "deployment_status": "deployed"}
    response = client.patch(f"/v1/ai-systems/{system_id}", headers=admin_headers, json=update_payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated System"
    assert response.json()["deployment_status"] == "deployed"


def test_ai_system_update_rejects_invalid_deployment_status(client, admin_headers):
    payload = {"name": "Status System"}
    response = client.post("/v1/ai-systems", headers=admin_headers, json=payload)
    system_id = response.json()["id"]

    update_payload = {"deployment_status": "invalid_status"}
    patch_response = client.patch(f"/v1/ai-systems/{system_id}", headers=admin_headers, json=update_payload)
    assert patch_response.status_code == 422
    
    get_response = client.get(f"/v1/ai-systems/{system_id}", headers=admin_headers)
    assert get_response.json()["deployment_status"] == "draft"


def test_ai_system_update_rejects_invalid_registration_status(client, admin_headers):
    payload = {"name": "Status System 2"}
    response = client.post("/v1/ai-systems", headers=admin_headers, json=payload)
    system_id = response.json()["id"]

    update_payload = {"registration_status": "invalid_status"}
    patch_response = client.patch(f"/v1/ai-systems/{system_id}", headers=admin_headers, json=update_payload)
    assert patch_response.status_code == 422
    
    get_response = client.get(f"/v1/ai-systems/{system_id}", headers=admin_headers)
    assert get_response.json()["registration_status"] == "draft"


def test_feature_linkage_to_ai_system(client, admin_headers, db_session):
    # Create AI System first
    sys_response = client.post("/v1/ai-systems", headers=admin_headers, json={"name": "Linkage System"})
    system_id = sys_response.json()["id"]

    # Create Feature with ai_system_id
    feature_payload = {
        "feature_id": "linked_feature",
        "name": "Linked Feature",
        "ai_system_id": system_id
    }
    response = client.post("/v1/features", headers=admin_headers, json=feature_payload)
    assert response.status_code == 200
    assert response.json()["ai_system_id"] == system_id

    # Update Feature to change/remove ai_system_id
    update_payload = {"ai_system_id": None}
    response = client.patch("/v1/features/linked_feature", headers=admin_headers, json=update_payload)
    assert response.status_code == 200
    assert response.json()["ai_system_id"] is None


def test_feature_linkage_validation(client, admin_headers, db_session):
    # Test invalid ai_system_id
    feature_payload = {
        "feature_id": "invalid_link_feature",
        "name": "Invalid Link Feature",
        "ai_system_id": "non-existent-id"
    }
    response = client.post("/v1/features", headers=admin_headers, json=feature_payload)
    assert response.status_code == 404

    # Test cross-tenant linkage
    # Create system in another tenant
    from app.models import Tenant
    
    other_tenant = Tenant(tenant_id="other_tenant", name="Other Tenant")
    db_session.add(other_tenant)
    db_session.commit()
    
    other_sys = AiSystem(id="other-sys", tenant_id="other_tenant", name="Other System")
    db_session.add(other_sys)
    db_session.commit()

    feature_payload["ai_system_id"] = "other-sys"
    response = client.post("/v1/features", headers=admin_headers, json=feature_payload)
    assert response.status_code == 403
    assert "another tenant" in response.json()["error"]["message"]


def test_feature_update_with_valid_ai_system_id(client, admin_headers):
    # 1. Create a feature without ai_system_id
    feature_payload = {
        "feature_id": "update_link_feature",
        "name": "Update Link Feature"
    }
    client.post("/v1/features", headers=admin_headers, json=feature_payload)

    # 2. Create a valid AI system
    sys_response = client.post("/v1/ai-systems", headers=admin_headers, json={"name": "Valid System"})
    system_id = sys_response.json()["id"]

    # 3. Patch the feature with the valid ai_system_id
    update_payload = {"ai_system_id": system_id}
    patch_response = client.patch("/v1/features/update_link_feature", headers=admin_headers, json=update_payload)
    
    assert patch_response.status_code == 200
    assert patch_response.json()["ai_system_id"] == system_id


def test_e2e_linkage_runtime_evidence(client, admin_headers, chat_payload, fake_provider, db_session):
    # 1. Create AI System
    sys_response = client.post("/v1/ai-systems", headers=admin_headers, json={"name": "E2E System"})
    system_id = sys_response.json()["id"]

    # 2. Create NEW Feature linked to that system
    feature_payload = {
        "feature_id": "new_e2e_feature",
        "name": "New E2E Feature",
        "ai_system_id": system_id
    }
    feat_response = client.post("/v1/features", headers=admin_headers, json=feature_payload)
    assert feat_response.status_code == 200
    assert feat_response.json()["ai_system_id"] == system_id

    # 3. Run runtime pipeline (Chat) using the NEW feature
    new_chat_payload = copy.deepcopy(chat_payload)
    new_chat_payload["feature_id"] = "new_e2e_feature"
    response = client.post("/v1/chat/completions", headers=admin_headers, json=new_chat_payload)
    assert response.status_code == 200

    # 4. Verify evidence includes ai_system_id
    evidence = db_session.query(EvidenceLog).filter(
        EvidenceLog.feature_id == "new_e2e_feature"
    ).order_by(EvidenceLog.created_at.desc()).first()

    assert evidence is not None
    assert evidence.ai_system_id == system_id


def test_legacy_feature_create_without_system_id(client, admin_headers):
    feature_payload = {
        "feature_id": "legacy_feature",
        "name": "Legacy Feature"
    }
    response = client.post("/v1/features", headers=admin_headers, json=feature_payload)
    assert response.status_code == 200
    assert "ai_system_id" in response.json()
    assert response.json()["ai_system_id"] is None


def test_legacy_feature_update_without_system_id(client, admin_headers):
    # Create first
    feature_payload = {
        "feature_id": "legacy_update_feature",
        "name": "Legacy Update Feature"
    }
    client.post("/v1/features", headers=admin_headers, json=feature_payload)
    
    # Update without system id
    update_payload = {"name": "Updated Legacy Name"}
    response = client.patch("/v1/features/legacy_update_feature", headers=admin_headers, json=update_payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Legacy Name"
    assert response.json()["ai_system_id"] is None


def test_ai_system_tenant_isolation(client, admin_headers, db_session):
    from app.models import Tenant
    
    # Create another tenant and a system under it
    other_tenant = Tenant(tenant_id="iso_tenant", name="Iso Tenant")
    db_session.add(other_tenant)
    db_session.commit()
    
    other_sys = AiSystem(id="iso-sys", tenant_id="iso_tenant", name="Iso System", deployment_status="draft", registration_status="draft")
    db_session.add(other_sys)
    db_session.commit()

    # List: should not see iso-sys
    response = client.get("/v1/ai-systems", headers=admin_headers)
    assert response.status_code == 200
    assert not any(s["id"] == "iso-sys" for s in response.json())

    # Get: should block getting iso-sys
    response = client.get("/v1/ai-systems/iso-sys", headers=admin_headers)
    assert response.status_code == 404

    # Update: should block updating iso-sys
    response = client.patch("/v1/ai-systems/iso-sys", headers=admin_headers, json={"name": "Hacked"})
    assert response.status_code == 404

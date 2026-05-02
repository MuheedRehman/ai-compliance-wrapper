import uuid

import pytest

from app.models import AiFeature, FeatureVersion
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

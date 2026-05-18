import ipaddress
import os
import re
import socket
import uuid
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AiSystem, ComplianceControl, EvidenceLog, WebsiteScan
from app.schemas import AiSystemCreate, IntakeCreate, WebsiteScanCreate
from app.services import ai_system_service
from app.services.classification_service import ClassificationService
from app.services.compliance_control_service import ComplianceControlService
from app.services.evidence_service import write_evidence_log
from app.services.regulatory_knowledge import match_annex_iii_categories, penalty_exposure_for_article, penalty_exposure_for_dimension


class WebsiteScannerError(Exception):
    pass


@dataclass
class PageArtifact:
    url: str
    status_code: int
    title: str | None
    text: str
    links: list[str]
    extraction_mode: str = "raw_html"
    render_metadata: dict[str, Any] = field(default_factory=dict)


class _ReadableHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self._in_title = False
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        value = unescape(data).strip()
        if not value:
            return
        if self._in_title:
            self.title_parts.append(value)
        elif not self._skip_depth:
            self.text_parts.append(value)

    @property
    def title(self) -> str | None:
        title = " ".join(self.title_parts).strip()
        return title[:180] if title else None

    @property
    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.text_parts)).strip()


class WebsiteScannerService:
    USER_AGENT = "AIComplianceScanner/0.2 (+https://example.com/compliance-scanner)"
    RENDER_TRIGGER_MIN_TEXT_CHARS = 900
    RENDER_TRIGGER_SCRIPT_COUNT = 8
    RENDER_TEXT_GAIN_CHARS = 400
    RENDER_TEXT_GAIN_RATIO = 1.15
    APP_SHELL_MARKERS = [
        "__next",
        "__nuxt",
        "id=\"root\"",
        "id=\"app\"",
        "data-reactroot",
        "ng-version",
        "vite/client",
    ]
    HIGH_VALUE_RENDER_PATH_KEYWORDS = [
        "ai",
        "responsible-ai",
        "trust",
        "security",
        "compliance",
        "privacy",
        "data-processing",
        "dpa",
        "subprocessor",
        "docs",
        "help",
    ]
    SAFE_EXPAND_LABELS = [
        "show more",
        "read more",
        "view more",
        "see more",
        "expand",
        "more details",
        "details",
    ]

    COMPLIANCE_PATHS = [
        "/privacy",
        "/privacy-policy",
        "/terms",
        "/terms-of-service",
        "/security",
        "/trust-center",
        "/trust",
        "/compliance",
        "/security-and-compliance",
        "/ai",
        "/responsible-ai",
        "/data-processing",
        "/dpa",
        "/subprocessors",
        "/docs",
        "/help",
        "/legal",
    ]

    SIGNAL_PATTERNS = {
        "ai_claim": [
            r"\bartificial intelligence\b",
            r"\bai\b",
            r"\bmachine learning\b",
            r"\bgenerative ai\b",
            r"\bautomation\b",
            r"\bmodel\b",
        ],
        "human_interaction": [
            r"\bchatbot\b",
            r"\bvirtual assistant\b",
            r"\bcopilot\b",
            r"\bagent\b",
            r"\binteracts? with (a )?user",
        ],
        "synthetic_content": [
            r"\bgenerate[sd]? content\b",
            r"\bsynthetic\b",
            r"\bdeepfake\b",
            r"\bimage generation\b",
            r"\btext generation\b",
        ],
        "high_risk_domain": [
            r"\bhiring\b",
            r"\brecruit(ing|ment)\b",
            r"\bemployment\b",
            r"\bcv screening\b",
            r"\bresume screening\b",
            r"\bcredit scor(e|ing)\b",
            r"\blending\b",
            r"\beducation\b",
            r"\badmission(s)?\b",
            r"\bexam(s|ination)?\b",
            r"\blaw enforcement\b",
            r"\bmigration\b",
            r"\basylum\b",
            r"\bbiometric\b",
            r"\bcritical infrastructure\b",
            r"\bessential service(s)?\b",
            r"\bpublic benefit(s)?\b",
            r"\bhealth insurance\b",
            r"\blife insurance\b",
            r"\bworker monitoring\b",
            r"\bemployee monitoring\b",
            r"\bperformance evaluation\b",
            r"\btask allocation\b",
            r"\bproctoring\b",
            r"\bemergency dispatch\b",
            r"\bemergency triage\b",
        ],
        "prohibited_risk": [
            r"\bsocial scoring\b",
            r"\bsubliminal\b",
            r"\bmanipulative\b",
            r"\bemotion recognition\b",
            r"\bbiometric categorisation\b",
        ],
        "gpai": [
            r"\bgeneral purpose ai\b",
            r"\bfoundation model\b",
            r"\blarge language model\b",
            r"\bllm\b",
            r"\bmodel provider\b",
        ],
        "governance": [
            r"\bresponsible ai\b",
            r"\bethical ai\b",
            r"\bhuman oversight\b",
            r"\bhuman review\b",
            r"\bhuman[- ]in[- ]the[- ]loop\b",
            r"\brisk management\b",
            r"\baudit log(s)?\b",
            r"\bactivity log(s)?\b",
            r"\bincident\b",
            r"\bpost-market monitoring\b",
            r"\bappeal(s)?\b",
            r"\bcontest (a )?decision\b",
            r"\bmodel card\b",
            r"\bmodel limitation(s)?\b",
        ],
        "privacy_security": [
            r"\bprivacy policy\b",
            r"\bgdpr\b",
            r"\bdata processing\b",
            r"\bsecurity\b",
            r"\bsoc 2\b",
            r"\biso 27001\b",
            r"\bdata protection addendum\b",
            r"\bdpa\b",
            r"\bsubprocessor(s)?\b",
            r"\bencryption\b",
        ],
    }

    PUBLIC_EVIDENCE_TOPICS = {
        "ai_disclosure": {
            "label": "User-facing AI disclosure",
            "dimension_id": "transparency_notice",
            "article": "Article 50",
            "evidence_domain": "transparency",
            "patterns": [
                r"\bai disclosure\b",
                r"\bai notice\b",
                r"\bclearly identif(y|ies|ied) as ai\b",
                r"\binteracting with (an )?ai\b",
                r"\bai-generated\b",
                r"\bmachine-generated\b",
                r"\bwatermark(ed|ing)?\b",
            ],
        },
        "human_oversight": {
            "label": "Human oversight or appeal path",
            "dimension_id": "deployer_high_risk_operations",
            "article": "Article 26",
            "evidence_domain": "human_oversight",
            "patterns": [
                r"\bhuman oversight\b",
                r"\bhuman review\b",
                r"\bhuman[- ]in[- ]the[- ]loop\b",
                r"\bmanual review\b",
                r"\bappeal(s)?\b",
                r"\bcontest (a )?decision\b",
            ],
        },
        "logging_monitoring": {
            "label": "Logging, monitoring, or incident process",
            "dimension_id": "post_market_monitoring",
            "article": "Articles 72-73",
            "evidence_domain": "post_market_monitoring",
            "patterns": [
                r"\baudit log(s)?\b",
                r"\bactivity log(s)?\b",
                r"\blog retention\b",
                r"\bmonitoring\b",
                r"\bincident reporting\b",
                r"\bpost-market monitoring\b",
                r"\bstatus page\b",
            ],
        },
        "limitations_accuracy": {
            "label": "Model limitations or accuracy warning",
            "dimension_id": "transparency_notice",
            "article": "Article 50",
            "evidence_domain": "transparency",
            "patterns": [
                r"\bmodel limitation(s)?\b",
                r"\blimitation(s)? of (the )?(ai|model|system)\b",
                r"\bmay be inaccurate\b",
                r"\baccuracy\b",
                r"\bhallucination(s)?\b",
                r"\bnot (legal|medical|financial) advice\b",
            ],
        },
        "data_governance": {
            "label": "Privacy and data governance",
            "dimension_id": "provider_high_risk_requirements",
            "article": "Articles 8-16",
            "evidence_domain": "provider_controls",
            "patterns": [
                r"\bprivacy policy\b",
                r"\bgdpr\b",
                r"\bdata processing\b",
                r"\bdata protection addendum\b",
                r"\bdpa\b",
                r"\bsubprocessor(s)?\b",
                r"\bdata retention\b",
                r"\btraining data\b",
            ],
        },
        "security_certification": {
            "label": "Security certification or controls",
            "dimension_id": "provider_high_risk_requirements",
            "article": "Articles 8-16",
            "evidence_domain": "provider_controls",
            "patterns": [
                r"\bsecurity\b",
                r"\bsoc 2\b",
                r"\biso 27001\b",
                r"\bencryption\b",
                r"\bpenetration test(ing)?\b",
                r"\bvulnerability management\b",
            ],
        },
        "vendor_documentation": {
            "label": "Technical or vendor documentation",
            "dimension_id": "importer_distributor_verification",
            "article": "Articles 23-24",
            "evidence_domain": "value_chain_review",
            "patterns": [
                r"\bmodel card\b",
                r"\btechnical documentation\b",
                r"\binstructions for use\b",
                r"\bdeclaration of conformity\b",
                r"\bce marking\b",
                r"\bvendor documentation\b",
            ],
        },
    }

    PAGE_KEYWORDS = {
        "privacy": ["privacy"],
        "terms": ["terms"],
        "security": ["security", "trust"],
        "ai": ["ai", "artificial-intelligence", "responsible-ai"],
        "compliance": ["compliance", "legal", "dpa", "data-processing", "subprocessor", "docs", "help"],
    }

    SIGNAL_CATEGORY_DIMENSIONS = {
        "ai_claim": ["ai_literacy"],
        "human_interaction": ["transparency_notice"],
        "synthetic_content": ["transparency_notice"],
        "high_risk_domain": ["high_risk_classification"],
        "prohibited_risk": ["prohibited_practice_review"],
        "gpai": ["gpai_provider_obligations"],
        "governance": [
            "ai_literacy",
            "provider_high_risk_requirements",
            "deployer_high_risk_operations",
            "post_market_monitoring",
        ],
        "privacy_security": ["provider_high_risk_requirements"],
    }

    ROLE_SCENARIOS = [
        {
            "actor_role": "Provider",
            "label": "Provider / builder",
            "description": "Use this scenario when the organisation develops or places the AI system on the market.",
            "is_developer": True,
            "is_deployer": False,
        },
        {
            "actor_role": "Deployer",
            "label": "Deployer / user",
            "description": "Use this scenario when the organisation uses a third-party AI system in its own operations.",
            "is_developer": False,
            "is_deployer": True,
        },
        {
            "actor_role": "Importer/Distributor",
            "label": "Importer or distributor",
            "description": "Use this scenario when the organisation makes a third-party AI system available in the EU value chain.",
            "is_developer": False,
            "is_deployer": False,
        },
    ]

    @classmethod
    async def create_scan(cls, db: Session, tenant_id: str, payload: WebsiteScanCreate) -> WebsiteScan:
        try:
            result = await cls().scan(payload.url, payload.max_pages)
            status = "completed"
            summary = result["summary"]
        except WebsiteScannerError as exc:
            normalized = cls.normalize_url(payload.url)
            result = cls.failed_result(normalized, str(exc))
            status = "failed"
            summary = str(exc)

        scan = WebsiteScan(
            id=f"scan-{uuid.uuid4().hex[:8]}",
            tenant_id=tenant_id,
            url=payload.url,
            normalized_url=result["normalized_url"],
            status=status,
            title=result.get("title"),
            summary=summary,
            detected_signals_json=result["detected_signals"],
            evidence_refs_json=result["evidence_refs"],
            gap_findings_json=result["gap_findings"],
            classification_json=result["classification"],
            suggested_actions_json=result["suggested_actions"],
            source_pages_json=result["source_pages"],
            confidence_score=result["confidence_score"],
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)
        return scan

    @staticmethod
    def list_scans(db: Session, tenant_id: str) -> list[WebsiteScan]:
        return (
            db.query(WebsiteScan)
            .filter(WebsiteScan.tenant_id == tenant_id)
            .order_by(WebsiteScan.created_at.desc())
            .all()
        )

    @staticmethod
    def get_scan(db: Session, tenant_id: str, scan_id: str) -> WebsiteScan:
        scan = (
            db.query(WebsiteScan)
            .filter(WebsiteScan.tenant_id == tenant_id, WebsiteScan.id == scan_id)
            .first()
        )
        if not scan:
            raise HTTPException(status_code=404, detail="Website scan not found")
        return scan

    @classmethod
    def convert_scan(
        cls,
        db: Session,
        tenant_id: str,
        scan_id: str,
        actor_role: str | None = None,
        commit: bool = True,
    ) -> tuple[WebsiteScan, AiSystem, Any, list[ComplianceControl], str | None]:
        try:
            scan = cls.get_scan(db, tenant_id, scan_id)
            if scan.status != "completed":
                raise HTTPException(status_code=400, detail="Only completed scans can be converted")

            if scan.ai_system_id and scan.intake_id:
                system = ai_system_service.get_ai_system(db, tenant_id, scan.ai_system_id)
                intake = ClassificationService.get_intake(db, tenant_id, scan.intake_id)
                if actor_role and intake.actor_role != actor_role:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Scan is already converted as {intake.actor_role}. Create a new scan to convert as {actor_role}.",
                    )
            else:
                classification = dict(scan.classification_json or {})
                answers = cls.answers_for_actor_role(classification.get("intake_answers") or {}, actor_role)
                system = ai_system_service.create_ai_system(
                    db,
                    tenant_id,
                    AiSystemCreate(
                        name=scan.title or urlparse(scan.normalized_url).hostname or scan.normalized_url,
                        description=f"Created from website scan of {scan.normalized_url}. {scan.summary or ''}".strip(),
                    ),
                    commit=False,
                )
                intake = ClassificationService.create_intake(
                    db,
                    tenant_id,
                    IntakeCreate(
                        title=f"{system.name} website compliance scan",
                        answers=answers,
                    ),
                    commit=False,
                )
                scan.ai_system_id = system.id
                scan.intake_id = intake.id
                classification["selected_actor_role"] = intake.actor_role
                scan.classification_json = classification
                db.flush()

            controls = ComplianceControlService.seed_from_obligation_graph(
                db,
                tenant_id,
                intake.obligation_graph_json or [],
                intake_id=intake.id,
                obligation_path=intake.obligation_path,
                ai_system_id=system.id,
                commit=False,
            )
            evidence_event_id = cls.ensure_conversion_evidence(
                db,
                tenant_id,
                scan,
                system,
                intake,
                controls,
                commit=False,
            )
            db.flush()
            if commit:
                db.commit()
                db.refresh(scan)
                db.refresh(system)
                db.refresh(intake)
                for control in controls:
                    db.refresh(control)
            return scan, system, intake, controls, evidence_event_id
        except Exception:
            if commit:
                db.rollback()
            raise

    @staticmethod
    def answers_for_actor_role(answers: dict[str, Any], actor_role: str | None) -> dict[str, Any]:
        selected = actor_role or "Provider"
        if selected not in {"Provider", "Deployer", "Importer/Distributor"}:
            raise HTTPException(status_code=400, detail="Unsupported scanner conversion actor role")

        converted = dict(answers)
        converted["selected_actor_role"] = selected
        converted["is_developer"] = selected == "Provider"
        converted["is_deployer"] = selected == "Deployer"
        return converted

    @staticmethod
    def ensure_conversion_evidence(
        db: Session,
        tenant_id: str,
        scan: WebsiteScan,
        system: AiSystem,
        intake: Any,
        controls: list[ComplianceControl],
        commit: bool = True,
    ) -> str | None:
        request_id = f"website-scan:{scan.id}"
        trace_id = f"scan-convert:{scan.id}"
        existing = db.query(EvidenceLog).filter(
            EvidenceLog.tenant_id == tenant_id,
            EvidenceLog.ai_system_id == system.id,
            EvidenceLog.event_type == "website_scan_converted",
            EvidenceLog.request_id == request_id,
        ).first()
        if existing:
            return existing.event_id

        classification = scan.classification_json or {}
        signals = scan.detected_signals_json or []
        evidence = write_evidence_log(
            db,
            {
                "tenant_id": tenant_id,
                "ai_system_id": system.id,
                "evidence_domain": "website_scan",
                "request_id": request_id,
                "trace_id": trace_id,
                "event_type": "website_scan_converted",
                "decision": "allow",
                "status": "completed",
                "risk_level": classification.get("risk_level") or "unknown",
                "risk_score": int(scan.confidence_score or 0),
                "triggered_rule_results": [
                    {
                        "category": signal.get("category"),
                        "label": signal.get("label"),
                        "source_url": signal.get("source_url"),
                    }
                    for signal in signals[:20]
                ],
                "policy_context": {
                    "system_classification": intake.system_classification,
                    "obligation_path": intake.obligation_path,
                    "scanner_classification": classification.get("classification"),
                },
                "metadata": {
                    "scan_id": scan.id,
                    "normalized_url": scan.normalized_url,
                    "intake_id": intake.id,
                    "control_ids": [control.id for control in controls],
                    "classification": classification,
                    "gap_findings": scan.gap_findings_json or [],
                    "evidence_refs": scan.evidence_refs_json or [],
                    "source_pages": scan.source_pages_json or [],
                },
            },
        )
        db.flush()
        if commit:
            db.commit()
            db.refresh(evidence)
        return evidence.event_id

    async def scan(self, raw_url: str, max_pages: int) -> dict[str, Any]:
        normalized_url = self.normalize_url(raw_url)
        self.validate_public_url(normalized_url)

        pages = await self.collect_pages(normalized_url, max_pages)
        if not pages:
            raise WebsiteScannerError("No readable public pages were found")

        analysis = self.analyze_pages(normalized_url, pages)
        return analysis

    async def collect_pages(self, normalized_url: str, max_pages: int) -> list[PageArtifact]:
        candidates = self.build_candidate_urls(normalized_url)
        pages: list[PageArtifact] = []
        seen: set[str] = set()

        for url in candidates:
            if len(pages) >= max_pages:
                break
            if url in seen:
                continue
            seen.add(url)
            page = await self.fetch_page(url)
            if page and self.should_render_page(page):
                page = await self.render_page_if_better(url, page)
            if page:
                pages.append(page)
                for discovered in self.discover_compliance_links(normalized_url, page.links):
                    if discovered not in seen and discovered not in candidates:
                        candidates.append(discovered)

        return pages

    async def fetch_page(self, url: str) -> PageArtifact | None:
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={
                        "user-agent": self.USER_AGENT,
                        "accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.5",
                    },
                )
            content_type = response.headers.get("content-type", "")
            if response.status_code >= 400 or "html" not in content_type and "text/plain" not in content_type:
                return None
            parser = _ReadableHTMLParser()
            parser.feed(response.text[:500_000])
            return PageArtifact(
                url=str(response.url),
                status_code=response.status_code,
                title=parser.title,
                text=parser.text[:120_000],
                links=parser.links,
                render_metadata={
                    "content_type": content_type,
                    "raw_html_bytes": len(response.text.encode("utf-8", errors="ignore")),
                    "raw_text_chars": len(parser.text),
                    "script_count": len(re.findall(r"<script\b", response.text, flags=re.IGNORECASE)),
                    "app_shell_detected": self.detect_app_shell(response.text, parser.text),
                    "render_candidate": False,
                },
            )
        except Exception:
            return None

    def should_render_page(self, page: PageArtifact) -> bool:
        if not self.rendered_crawl_enabled():
            return False
        metadata = page.render_metadata or {}
        path = urlparse(page.url).path.lower()
        high_value_path = any(keyword in path for keyword in self.HIGH_VALUE_RENDER_PATH_KEYWORDS)
        shallow_text = len(page.text or "") < self.RENDER_TRIGGER_MIN_TEXT_CHARS
        script_heavy = int(metadata.get("script_count") or 0) >= self.RENDER_TRIGGER_SCRIPT_COUNT
        app_shell = bool(metadata.get("app_shell_detected"))
        should_render = app_shell or (script_heavy and (shallow_text or high_value_path))
        metadata["render_candidate"] = should_render
        metadata["render_reason"] = {
            "app_shell": app_shell,
            "script_heavy": script_heavy,
            "shallow_text": shallow_text,
            "high_value_path": high_value_path,
        }
        page.render_metadata = metadata
        return should_render

    async def render_page_if_better(self, url: str, raw_page: PageArtifact) -> PageArtifact:
        rendered = await self.render_page(url, fallback_page=raw_page)
        if not rendered or rendered is raw_page:
            return raw_page

        raw_chars = len(raw_page.text or "")
        rendered_chars = len(rendered.text or "")
        enough_gain = (
            rendered_chars >= raw_chars + self.RENDER_TEXT_GAIN_CHARS
            or rendered_chars >= int(raw_chars * self.RENDER_TEXT_GAIN_RATIO)
        )
        if rendered_chars > raw_chars and enough_gain:
            rendered.render_metadata.update({
                "raw_text_chars": raw_chars,
                "render_kept": True,
                "render_text_gain": rendered_chars - raw_chars,
            })
            return rendered

        raw_page.render_metadata.update({
            "render_attempted": True,
            "render_kept": False,
            "render_text_chars": rendered_chars,
            "render_text_gain": rendered_chars - raw_chars,
        })
        return raw_page

    async def render_page(self, url: str, fallback_page: PageArtifact | None = None) -> PageArtifact | None:
        try:
            from playwright.async_api import TimeoutError as PlaywrightTimeoutError
            from playwright.async_api import async_playwright
        except Exception as exc:
            if fallback_page:
                fallback_page.render_metadata.update({
                    "render_attempted": True,
                    "render_error": f"Playwright unavailable: {exc.__class__.__name__}",
                })
            return fallback_page

        browser = None
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-gpu",
                        "--disable-background-networking",
                    ],
                )
                context = await browser.new_context(
                    user_agent=self.USER_AGENT,
                    viewport={"width": 1365, "height": 900},
                    java_script_enabled=True,
                    ignore_https_errors=True,
                )
                page = await context.new_page()
                timeout_ms = self.render_timeout_ms()
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                try:
                    await page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 5_000))
                except PlaywrightTimeoutError:
                    pass

                expanded_count = await self.expand_safe_content(page)
                scroll_metadata = await self.smart_scroll_page(page)
                text = await self.extract_rendered_text(page)
                links = await page.eval_on_selector_all(
                    "a[href]",
                    "els => els.map(el => el.href).filter(Boolean)",
                )
                title = await page.title()
                html_chars = await page.evaluate("document.documentElement.outerHTML.length")
                final_url = page.url
                await context.close()

                extraction_mode = "rendered_scrolled" if scroll_metadata["scroll_steps"] else "rendered_dom"
                if expanded_count:
                    extraction_mode = "rendered_interacted"
                return PageArtifact(
                    url=final_url,
                    status_code=200,
                    title=title[:180] if title else (fallback_page.title if fallback_page else None),
                    text=text[:120_000],
                    links=links,
                    extraction_mode=extraction_mode,
                    render_metadata={
                        "render_attempted": True,
                        "render_error": None,
                        "rendered_html_chars": html_chars,
                        "rendered_text_chars": len(text),
                        "safe_expansion_clicks": expanded_count,
                        **scroll_metadata,
                    },
                )
        except Exception as exc:
            if fallback_page:
                fallback_page.render_metadata.update({
                    "render_attempted": True,
                    "render_error": f"{exc.__class__.__name__}: {str(exc)[:180]}",
                })
            return fallback_page
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception:
                    pass

    async def expand_safe_content(self, page: Any) -> int:
        try:
            return int(await page.evaluate(
                """
                labels => {
                  const visible = el => {
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style.visibility !== 'hidden' && style.display !== 'none' && rect.width > 0 && rect.height > 0;
                  };
                  const candidates = Array.from(document.querySelectorAll('button,[role="button"],summary,[aria-expanded="false"]'));
                  let clicked = 0;
                  for (const el of candidates) {
                    if (clicked >= 8 || !visible(el)) continue;
                    const text = (el.innerText || el.textContent || el.getAttribute('aria-label') || '').trim().toLowerCase();
                    if (!text || !labels.some(label => text.includes(label))) continue;
                    try {
                      el.click();
                      clicked += 1;
                    } catch (_) {}
                  }
                  return clicked;
                }
                """,
                self.SAFE_EXPAND_LABELS,
            ))
        except Exception:
            return 0

    async def smart_scroll_page(self, page: Any) -> dict[str, Any]:
        max_steps = self.render_scroll_steps()
        stable_passes = 0
        last_height = await self.safe_page_metric(page, "height")
        last_text_chars = await self.safe_page_metric(page, "text")
        steps = 0

        for _ in range(max_steps):
            await page.evaluate("window.scrollBy(0, Math.max(window.innerHeight * 0.85, 700))")
            steps += 1
            await page.wait_for_timeout(450)
            try:
                await page.wait_for_load_state("networkidle", timeout=1_500)
            except Exception:
                pass

            height = await self.safe_page_metric(page, "height")
            text_chars = await self.safe_page_metric(page, "text")
            height_delta = height - last_height
            text_delta = text_chars - last_text_chars
            if height_delta <= 20 and text_delta <= 120:
                stable_passes += 1
            else:
                stable_passes = 0
            last_height = height
            last_text_chars = text_chars
            if stable_passes >= 2:
                break

        try:
            await page.evaluate("window.scrollTo(0, 0)")
        except Exception:
            pass

        return {
            "scroll_steps": steps,
            "scroll_stable_passes": stable_passes,
            "final_scroll_height": last_height,
            "final_text_chars": last_text_chars,
        }

    @staticmethod
    async def safe_page_metric(page: Any, metric: str) -> int:
        try:
            if metric == "height":
                return int(await page.evaluate("document.documentElement.scrollHeight || document.body.scrollHeight || 0"))
            return int(await page.evaluate("(document.body && document.body.innerText ? document.body.innerText.length : 0)"))
        except Exception:
            return 0

    @staticmethod
    async def extract_rendered_text(page: Any) -> str:
        try:
            text = await page.locator("body").inner_text(timeout=2_000)
        except Exception:
            text = await page.evaluate("document.body ? document.body.innerText : ''")
        return re.sub(r"\s+", " ", text or "").strip()

    @staticmethod
    def rendered_crawl_enabled() -> bool:
        return (os.getenv("SCANNER_RENDERED_CRAWL_ENABLED", "true") or "true").strip().lower() not in {"0", "false", "no", "off"}

    @staticmethod
    def render_timeout_ms() -> int:
        try:
            return max(2_000, min(int(os.getenv("SCANNER_RENDER_TIMEOUT_MS", "9000")), 20_000))
        except ValueError:
            return 9_000

    @staticmethod
    def render_scroll_steps() -> int:
        try:
            return max(0, min(int(os.getenv("SCANNER_RENDER_SCROLL_STEPS", "6")), 12))
        except ValueError:
            return 6

    @classmethod
    def detect_app_shell(cls, html: str, text: str) -> bool:
        value = html[:250_000].lower()
        text_chars = len(text or "")
        has_marker = any(marker in value for marker in cls.APP_SHELL_MARKERS)
        has_bootstrap_payload = "__next_data__" in value or "self.__next_f" in value
        return bool((has_marker or has_bootstrap_payload) and text_chars < cls.RENDER_TRIGGER_MIN_TEXT_CHARS)

    def analyze_pages(self, normalized_url: str, pages: list[PageArtifact]) -> dict[str, Any]:
        combined = "\n".join(page.text for page in pages)
        title = pages[0].title or urlparse(normalized_url).hostname
        signals, evidence_refs = self.detect_signals(pages)
        evidence_profile = self.extract_public_evidence_profile(pages)
        evidence_refs = self.merge_evidence_refs(evidence_refs, evidence_profile)
        annex_iii_matches = match_annex_iii_categories(combined)
        classification = self.classify(signals, annex_iii_matches)
        classification["public_evidence_profile"] = evidence_profile
        classification["crawl_quality"] = self.summarize_crawl_quality(pages)
        gaps = self.find_gaps(signals, pages, classification, evidence_profile)
        suggested_actions = self.suggest_actions(classification, gaps)
        confidence = self.score_confidence(pages, signals)
        source_pages = [
            {
                "url": page.url,
                "status_code": page.status_code,
                "title": page.title,
                "text_excerpt": page.text[:280],
                "extraction_mode": page.extraction_mode,
                "render_metadata": self.public_render_metadata(page.render_metadata),
                "evidence_topics": [
                    topic["topic"]
                    for topic in evidence_profile.get("topics", [])
                    if topic.get("source_url") == page.url
                ],
            }
            for page in pages
        ]

        return {
            "normalized_url": normalized_url,
            "title": title,
            "summary": self.build_summary(title, classification, signals, combined),
            "detected_signals": signals,
            "evidence_refs": evidence_refs,
            "gap_findings": gaps,
            "classification": classification,
            "suggested_actions": suggested_actions,
            "source_pages": source_pages,
            "confidence_score": confidence,
        }

    def detect_signals(self, pages: list[PageArtifact]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        signals: list[dict[str, Any]] = []
        evidence_refs: list[dict[str, Any]] = []
        seen_signals: set[tuple[str, str]] = set()

        for page in pages:
            text_lower = page.text.lower()
            for category, patterns in self.SIGNAL_PATTERNS.items():
                for pattern in patterns:
                    match = re.search(pattern, text_lower, flags=re.IGNORECASE)
                    if not match:
                        continue
                    key = (category, pattern)
                    if key in seen_signals:
                        continue
                    seen_signals.add(key)
                    excerpt = self.excerpt(page.text, match.start(), match.end())
                    label = self.humanize_pattern(pattern)
                    signal = {
                        "category": category,
                        "label": label,
                        "source_url": page.url,
                        "excerpt": excerpt,
                        "extraction_mode": page.extraction_mode,
                    }
                    signals.append(signal)
                    evidence_refs.append({
                        "type": "public_page",
                        "category": category,
                        "source_url": page.url,
                        "excerpt": excerpt,
                        "extraction_mode": page.extraction_mode,
                    })
                    break

        return signals, evidence_refs[:20]

    def extract_public_evidence_profile(self, pages: list[PageArtifact]) -> dict[str, Any]:
        topics: list[dict[str, Any]] = []
        seen_topics: set[str] = set()

        for page in pages:
            text_lower = page.text.lower()
            for topic, config in self.PUBLIC_EVIDENCE_TOPICS.items():
                if topic in seen_topics:
                    continue
                for pattern in config["patterns"]:
                    match = re.search(pattern, text_lower, flags=re.IGNORECASE)
                    if not match:
                        continue
                    seen_topics.add(topic)
                    topics.append({
                        "topic": topic,
                        "label": config["label"],
                        "source_url": page.url,
                        "excerpt": self.excerpt(page.text, match.start(), match.end()),
                        "extraction_mode": page.extraction_mode,
                        "dimension_id": config["dimension_id"],
                        "article": config["article"],
                        "evidence_domain": config["evidence_domain"],
                    })
                    break

        topic_ids = {topic["topic"] for topic in topics}
        return {
            "topics": topics,
            "coverage": {
                "ai_disclosure": "ai_disclosure" in topic_ids,
                "human_oversight": "human_oversight" in topic_ids,
                "logging_monitoring": "logging_monitoring" in topic_ids,
                "limitations_accuracy": "limitations_accuracy" in topic_ids,
                "data_governance": "data_governance" in topic_ids,
                "security_certification": "security_certification" in topic_ids,
                "vendor_documentation": "vendor_documentation" in topic_ids,
            },
            "coverage_score": self.score_public_evidence_coverage(topic_ids),
            "missing_topics": [
                config["label"]
                for topic, config in self.PUBLIC_EVIDENCE_TOPICS.items()
                if topic not in topic_ids
            ],
        }

    @staticmethod
    def score_public_evidence_coverage(topic_ids: set[str]) -> int:
        if not topic_ids:
            return 0
        core_topics = {"ai_disclosure", "human_oversight", "data_governance", "security_certification"}
        core_score = sum(18 for topic in core_topics if topic in topic_ids)
        supporting_score = sum(7 for topic in topic_ids - core_topics)
        return min(100, core_score + supporting_score)

    @staticmethod
    def merge_evidence_refs(
        signal_refs: list[dict[str, Any]],
        evidence_profile: dict[str, Any],
    ) -> list[dict[str, Any]]:
        refs = list(signal_refs)
        for topic in evidence_profile.get("topics", []):
            refs.append({
                "type": "public_evidence_topic",
                "category": topic["topic"],
                "label": topic["label"],
                "source_url": topic["source_url"],
                "excerpt": topic["excerpt"],
                "extraction_mode": topic.get("extraction_mode", "raw_html"),
                "dimension_id": topic["dimension_id"],
                "article": topic["article"],
                "evidence_domain": topic["evidence_domain"],
            })
        return refs[:30]

    @staticmethod
    def summarize_crawl_quality(pages: list[PageArtifact]) -> dict[str, Any]:
        extraction_modes: dict[str, int] = {}
        render_attempted = 0
        render_failures = 0
        render_kept = 0
        render_candidates = 0
        for page in pages:
            extraction_modes[page.extraction_mode] = extraction_modes.get(page.extraction_mode, 0) + 1
            metadata = page.render_metadata or {}
            if metadata.get("render_candidate"):
                render_candidates += 1
            if metadata.get("render_attempted"):
                render_attempted += 1
            if metadata.get("render_error"):
                render_failures += 1
            if metadata.get("render_kept") or page.extraction_mode.startswith("rendered"):
                render_kept += 1

        return {
            "page_count": len(pages),
            "extraction_modes": extraction_modes,
            "render_candidates": render_candidates,
            "render_attempted": render_attempted,
            "render_failures": render_failures,
            "render_kept": render_kept,
            "rendered_crawl_enabled": WebsiteScannerService.rendered_crawl_enabled(),
        }

    @staticmethod
    def public_render_metadata(metadata: dict[str, Any] | None) -> dict[str, Any]:
        metadata = metadata or {}
        allowed = {
            "content_type",
            "raw_html_bytes",
            "raw_text_chars",
            "script_count",
            "app_shell_detected",
            "render_candidate",
            "render_reason",
            "render_attempted",
            "render_error",
            "render_kept",
            "render_text_chars",
            "render_text_gain",
            "rendered_html_chars",
            "rendered_text_chars",
            "safe_expansion_clicks",
            "scroll_steps",
            "scroll_stable_passes",
            "final_scroll_height",
            "final_text_chars",
        }
        return {key: metadata[key] for key in allowed if key in metadata}

    def classify(
        self,
        signals: list[dict[str, Any]],
        annex_iii_matches: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        categories = {signal["category"] for signal in signals}
        annex_iii_matches = annex_iii_matches or []
        answers = {
            "is_developer": True,
            "is_deployer": False,
            "is_prohibited_use": "prohibited_risk" in categories,
            "is_high_risk_annex_iii": "high_risk_domain" in categories or bool(annex_iii_matches),
            "is_safety_component": False,
            "has_transparency_obligation": bool({"human_interaction", "synthetic_content"} & categories),
            "is_gpai": "gpai" in categories,
            "annex_iii_matches": annex_iii_matches,
        }
        if annex_iii_matches:
            answers["annex_iii_area"] = annex_iii_matches[0]["subcategory_id"]
            answers["annex_iii_category"] = annex_iii_matches[0]["category_id"]

        if answers["is_prohibited_use"]:
            risk_level = "prohibited_review"
            classification = "Potential Prohibited AI Pattern"
            obligation_path = "LEGAL_REVIEW_REQUIRED"
        elif answers["is_high_risk_annex_iii"]:
            risk_level = "high"
            classification = "Potential High-Risk AI System"
            obligation_path = "HIGH_RISK_TRIAGE"
        elif answers["is_gpai"]:
            risk_level = "gpai"
            classification = "Potential GPAI / Model Provider"
            obligation_path = "GPAI_TRIAGE"
        elif answers["has_transparency_obligation"] or "ai_claim" in categories:
            risk_level = "limited"
            classification = "Potential Limited-Risk / Transparency AI System"
            obligation_path = "TRANSPARENCY_TRIAGE"
        else:
            risk_level = "minimal_or_unknown"
            classification = "No Clear Public AI Risk Signal"
            obligation_path = "MANUAL_REVIEW"

        canonical = ClassificationService._run_classification_logic(answers)
        obligation_dimensions = self.map_obligation_dimensions(signals, canonical["obligation_graph"])
        role_scenarios = self.build_role_scenarios(answers, signals, canonical["actor_role"])

        return {
            "classification": classification,
            "risk_level": risk_level,
            "obligation_path": obligation_path,
            "actor_assumption": "Provider",
            "intake_answers": answers,
            "rationale": self.classification_rationale(classification, categories),
            "canonical_actor_role": canonical["actor_role"],
            "canonical_classification": canonical["system_classification"],
            "canonical_obligation_path": canonical["obligation_path"],
            "canonical_rationale": canonical["rationale"],
            "legal_basis": canonical["legal_basis"],
            "annex_iii_matches": annex_iii_matches,
            "evidence_requirements": canonical["evidence_requirements"],
            "obligation_dimensions": obligation_dimensions,
            "role_scenarios": role_scenarios,
            "manual_review_required": self.requires_manual_review(risk_level, obligation_dimensions),
            "scanner_to_obligation_confidence": self.score_obligation_mapping_confidence(obligation_dimensions, signals),
        }

    def build_role_scenarios(
        self,
        base_answers: dict[str, Any],
        signals: list[dict[str, Any]],
        default_actor_role: str,
    ) -> list[dict[str, Any]]:
        scenarios: list[dict[str, Any]] = []
        for scenario in self.ROLE_SCENARIOS:
            answers = {
                **base_answers,
                "is_developer": scenario["is_developer"],
                "is_deployer": scenario["is_deployer"],
            }
            result = ClassificationService._run_classification_logic(answers)
            dimensions = self.map_obligation_dimensions(signals, result["obligation_graph"])
            penalty_exposures = self.collect_penalty_exposures(dimensions)
            scenarios.append({
                "actor_role": result["actor_role"],
                "label": scenario["label"],
                "description": scenario["description"],
                "is_default": result["actor_role"] == default_actor_role,
                "system_classification": result["system_classification"],
                "obligation_path": result["obligation_path"],
                "rationale": result["rationale"],
                "legal_basis": result["legal_basis"],
                "obligation_dimensions": dimensions,
                "required_controls": self.summarize_required_controls(dimensions),
                "evidence_requirements": result["evidence_requirements"],
                "penalty_exposures": penalty_exposures,
                "primary_penalty_exposure": self.primary_penalty_exposure(penalty_exposures),
                "manual_review_required": self.requires_manual_review_for_role(result["system_classification"], dimensions),
            })
        return scenarios

    @staticmethod
    def summarize_required_controls(dimensions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        controls: list[dict[str, Any]] = []
        seen: set[str] = set()
        for dimension in dimensions:
            for control in dimension.get("required_controls", []):
                control_key = control.get("control_key")
                if not control_key or control_key in seen:
                    continue
                seen.add(control_key)
                controls.append({
                    **control,
                    "dimension_id": dimension["dimension_id"],
                    "article": dimension["article"],
                    "evidence_domain": dimension["evidence_domain"],
                    "penalty_exposure": dimension.get("penalty_exposure"),
                })
        return controls

    @staticmethod
    def collect_penalty_exposures(dimensions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        exposures: list[dict[str, Any]] = []
        seen: set[str] = set()
        for dimension in dimensions:
            penalty = dimension.get("penalty_exposure")
            band_id = penalty.get("band_id") if penalty else None
            if not band_id or band_id in seen:
                continue
            seen.add(band_id)
            exposures.append(penalty)
        return exposures

    @staticmethod
    def primary_penalty_exposure(exposures: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not exposures:
            return None
        return max(exposures, key=lambda item: item.get("max_eur") or 0)

    @staticmethod
    def requires_manual_review_for_role(system_classification: str, dimensions: list[dict[str, Any]]) -> bool:
        if system_classification in {"High-Risk AI System", "Prohibited AI System", "General Purpose AI (GPAI)"}:
            return True
        return any(
            dimension.get("status") in {"blocking", "review_required", "screening_required"}
            for dimension in dimensions
        )

    def map_obligation_dimensions(
        self,
        signals: list[dict[str, Any]],
        obligation_graph: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        search_text = " ".join(
            f"{signal.get('category', '')} {signal.get('label', '')} {signal.get('excerpt', '')}"
            for signal in signals
        ).lower()
        mappings: list[dict[str, Any]] = []

        for dimension in obligation_graph:
            dimension_id = dimension["dimension_id"]
            matched_public_signals: list[str] = []
            for expected_signal in dimension.get("scanner_signals", []):
                if expected_signal.lower() in search_text:
                    matched_public_signals.append(expected_signal)
            for signal in signals:
                category = signal.get("category")
                if dimension_id in self.SIGNAL_CATEGORY_DIMENSIONS.get(category, []):
                    matched_public_signals.append(signal.get("label") or category)

            matched_public_signals = self.dedupe_preserve_order(matched_public_signals)
            signal_support = "direct_public_match" if matched_public_signals else "classification_inferred"

            mappings.append({
                "dimension_id": dimension_id,
                "pillar": dimension["pillar"],
                "chapter": dimension["chapter"],
                "article": dimension["article"],
                "articles": dimension.get("articles", []),
                "annex_refs": dimension.get("annex_refs", []),
                "status": dimension["status"],
                "evidence_domain": dimension["evidence_domain"],
                "summary": dimension["summary"],
                "explanation": dimension["explanation"],
                "required_controls": dimension.get("required_controls", []),
                "required_evidence": dimension.get("required_evidence", []),
                "annex_iii_matches": dimension.get("annex_iii_matches", []),
                "penalty_exposure": dimension.get("penalty_exposure") or penalty_exposure_for_dimension(dimension_id, dimension["article"]),
                "scanner_signals": dimension.get("scanner_signals", []),
                "matched_public_signals": matched_public_signals,
                "signal_support": signal_support,
                "confidence_policy": dimension.get("confidence_policy"),
                "effective_dates": dimension.get("effective_dates", {}),
            })

        return mappings

    @staticmethod
    def requires_manual_review(risk_level: str, obligation_dimensions: list[dict[str, Any]]) -> bool:
        if risk_level in {"high", "prohibited_review", "gpai"}:
            return True
        return any(
            dimension.get("status") in {"blocking", "review_required", "screening_required"}
            for dimension in obligation_dimensions
        )

    @staticmethod
    def score_obligation_mapping_confidence(
        obligation_dimensions: list[dict[str, Any]],
        signals: list[dict[str, Any]],
    ) -> int:
        if not obligation_dimensions:
            return 0
        supported_count = sum(1 for dimension in obligation_dimensions if dimension.get("matched_public_signals"))
        support_ratio = supported_count / len(obligation_dimensions)
        signal_score = min(len(signals) * 6, 36)
        return max(20, min(95, 30 + signal_score + int(support_ratio * 29)))

    def find_gaps(
        self,
        signals: list[dict[str, Any]],
        pages: list[PageArtifact],
        classification: dict[str, Any],
        evidence_profile: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        categories = {signal["category"] for signal in signals}
        page_urls = " ".join(page.url.lower() for page in pages)
        coverage = (evidence_profile or {}).get("coverage", {})
        crawl_quality = classification.get("crawl_quality") or {}
        gaps: list[dict[str, Any]] = []

        if "ai_claim" in categories and "governance" not in categories and not coverage.get("human_oversight"):
            gaps.append({
                "severity": "medium",
                "title": "No public responsible AI governance signal found",
                "detail": "The site appears to mention AI, but the scan did not find public language about oversight, risk management, audit logs, incidents, or responsible AI practices.",
                "dimension_id": "ai_literacy",
                "article": "Article 4",
                "evidence_domain": "ai_literacy",
                "penalty_exposure": penalty_exposure_for_dimension("ai_literacy", "Article 4"),
            })
        if classification["risk_level"] in {"limited", "high", "prohibited_review"} and not coverage.get("ai_disclosure"):
            gaps.append({
                "severity": "medium",
                "title": "User-facing AI disclosure evidence not found",
                "detail": "The scanner found AI functionality but did not find a clear public notice that users are interacting with AI or receiving AI-generated content.",
                "dimension_id": "transparency_notice",
                "article": "Article 50",
                "evidence_domain": "transparency",
                "penalty_exposure": penalty_exposure_for_dimension("transparency_notice", "Article 50"),
            })
        if classification["risk_level"] in {"high", "prohibited_review"}:
            dimension_id = "prohibited_practice_review" if classification["risk_level"] == "prohibited_review" else "high_risk_classification"
            article = "Article 5" if classification["risk_level"] == "prohibited_review" else "Article 6 and Annex III"
            gaps.append({
                "severity": "high",
                "title": "High-risk language requires manual legal validation",
                "detail": "Public pages contain terms associated with Annex III or prohibited-risk review. Confirm the intended purpose and actual deployment context before relying on this classification.",
                "dimension_id": dimension_id,
                "article": article,
                "evidence_domain": "classification",
                "penalty_exposure": penalty_exposure_for_dimension(dimension_id, article),
            })
            if not coverage.get("human_oversight"):
                gaps.append({
                    "severity": "high",
                    "title": "Human oversight evidence missing for high-risk triage",
                    "detail": "High-risk or prohibited-review signals were detected, but public pages did not show human oversight, manual review, appeals, or decision-contestation evidence.",
                    "dimension_id": "deployer_high_risk_operations",
                    "article": "Article 26",
                    "evidence_domain": "human_oversight",
                    "penalty_exposure": penalty_exposure_for_dimension("deployer_high_risk_operations", "Article 26"),
                })
            if not coverage.get("logging_monitoring"):
                gaps.append({
                    "severity": "medium",
                    "title": "Logging or incident process evidence missing",
                    "detail": "The scanner did not find public evidence of audit logging, monitoring, incident reporting, or post-market monitoring for this higher-risk workflow.",
                    "dimension_id": "post_market_monitoring",
                    "article": "Articles 72-73",
                    "evidence_domain": "post_market_monitoring",
                    "penalty_exposure": penalty_exposure_for_dimension("post_market_monitoring", "Articles 72-73"),
                })
        if "human_interaction" in categories and "ai" not in page_urls and "responsible-ai" not in page_urls:
            gaps.append({
                "severity": "medium",
                "title": "AI interaction disclosure page not obvious",
                "detail": "The scan found chatbot/assistant signals, but no obvious AI disclosure or responsible AI page in the crawled URLs.",
                "dimension_id": "transparency_notice",
                "article": "Article 50",
                "evidence_domain": "transparency",
                "penalty_exposure": penalty_exposure_for_dimension("transparency_notice", "Article 50"),
            })
        if "privacy_security" not in categories and not (coverage.get("data_governance") or coverage.get("security_certification")):
            gaps.append({
                "severity": "medium",
                "title": "Privacy/security evidence not found in scanned pages",
                "detail": "The scanner did not find privacy, GDPR, security, SOC 2, or data processing signals in the crawled public pages.",
                "dimension_id": "provider_high_risk_requirements",
                "article": "Articles 8-16",
                "evidence_domain": "provider_controls",
                "penalty_exposure": penalty_exposure_for_dimension("provider_high_risk_requirements", "Articles 8-16"),
            })
        if crawl_quality.get("render_failures"):
            gaps.append({
                "severity": "medium",
                "title": "Rendered crawl fallback used on some pages",
                "detail": "One or more JavaScript-dependent pages could not be fully rendered, so the scanner fell back to available raw HTML evidence for those pages.",
                "dimension_id": "ai_literacy",
                "article": "Article 4",
                "evidence_domain": "scanner_limitations",
                "penalty_exposure": penalty_exposure_for_dimension("ai_literacy", "Article 4"),
            })
        if not gaps:
            gaps.append({
                "severity": "low",
                "title": "No critical public-page gaps detected",
                "detail": "The public website contains some governance or privacy evidence. Internal documentation is still required for compliance assurance.",
                "dimension_id": "ai_literacy",
                "article": "Article 4",
                "evidence_domain": "ai_literacy",
                "penalty_exposure": penalty_exposure_for_dimension("ai_literacy", "Article 4"),
            })

        return gaps

    def suggest_actions(self, classification: dict[str, Any], gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        actions = [
            {
                "priority": "high" if classification["risk_level"] in {"high", "prohibited_review"} else "medium",
                "title": "Confirm intended purpose and actor role",
                "detail": "Validate whether the organization is acting as provider, deployer, importer, or distributor, and document the intended purpose.",
                "dimension_id": "high_risk_classification" if classification["risk_level"] == "high" else None,
                "article": "Article 6 and Annex III" if classification["risk_level"] == "high" else None,
                "penalty_exposure": (
                    penalty_exposure_for_dimension("high_risk_classification", "Article 6 and Annex III")
                    if classification["risk_level"] == "high"
                    else penalty_exposure_for_article("EU AI Act")
                ),
            },
            {
                "priority": "medium",
                "title": "Convert scan into an intake record",
                "detail": "Use the generated intake answers as a draft and complete the classification with internal context.",
                "penalty_exposure": penalty_exposure_for_article("EU AI Act"),
            },
        ]
        if any(gap["severity"] == "high" for gap in gaps):
            dimension_id = "prohibited_practice_review" if classification["risk_level"] == "prohibited_review" else "high_risk_classification"
            article = "Article 5" if classification["risk_level"] == "prohibited_review" else "Article 6 and Annex III"
            actions.append({
                "priority": "high",
                "title": "Run counsel/compliance review",
                "detail": "Escalate high-risk or prohibited-risk indicators before using this result in customer-facing claims.",
                "dimension_id": dimension_id,
                "article": article,
                "penalty_exposure": penalty_exposure_for_dimension(dimension_id, article),
            })
        for dimension in classification.get("obligation_dimensions", [])[:5]:
            if dimension["dimension_id"] == "ai_literacy" and len(classification.get("obligation_dimensions", [])) > 1:
                continue
            actions.append({
                "priority": "high" if dimension["status"] in {"blocking", "review_required"} else "medium",
                "title": f"Prepare {dimension['pillar']} evidence",
                "detail": f"{dimension['article']}: {dimension['summary']}",
                "dimension_id": dimension["dimension_id"],
                "article": dimension["article"],
                "evidence_domain": dimension["evidence_domain"],
                "penalty_exposure": dimension.get("penalty_exposure") or penalty_exposure_for_dimension(dimension["dimension_id"], dimension["article"]),
            })
        return actions

    def score_confidence(self, pages: list[PageArtifact], signals: list[dict[str, Any]]) -> int:
        page_score = min(len(pages) * 10, 40)
        signal_score = min(len(signals) * 7, 45)
        governance_bonus = 15 if any(signal["category"] in {"governance", "privacy_security"} for signal in signals) else 0
        return max(20, min(95, page_score + signal_score + governance_bonus))

    def build_summary(
        self,
        title: str | None,
        classification: dict[str, Any],
        signals: list[dict[str, Any]],
        combined: str,
    ) -> str:
        signal_labels = ", ".join(signal["label"] for signal in signals[:4]) or "no clear AI signals"
        product = title or "Website"
        return (
            f"{product} was classified as {classification['classification']} from public-page evidence. "
            f"Detected signals include {signal_labels}. This is a preliminary triage result and requires internal validation."
        )

    @staticmethod
    def classification_rationale(classification: str, categories: set[str]) -> str:
        if "prohibited_risk" in categories:
            return "Public text contains terms associated with prohibited-practice review, so legal validation is required."
        if "high_risk_domain" in categories:
            return "Public text contains terms associated with Annex III high-risk domains such as employment, education, credit, essential services, biometrics, or law enforcement."
        if "gpai" in categories:
            return "Public text suggests a general-purpose AI or model-provider offering."
        if {"human_interaction", "synthetic_content", "ai_claim"} & categories:
            return "Public text suggests AI functionality that may trigger transparency or disclosure obligations."
        return "The scan did not find enough public evidence to classify the system beyond manual review."

    @classmethod
    def build_candidate_urls(cls, normalized_url: str) -> list[str]:
        parsed = urlparse(normalized_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        return [normalized_url] + [urljoin(origin, path) for path in cls.COMPLIANCE_PATHS]

    def discover_compliance_links(self, base_url: str, links: list[str]) -> list[str]:
        base = urlparse(base_url)
        discovered: list[str] = []
        for href in links:
            absolute = urljoin(base_url, href.split("#", 1)[0])
            parsed = urlparse(absolute)
            if parsed.netloc != base.netloc or parsed.scheme not in {"http", "https"}:
                continue
            path = parsed.path.lower()
            if any(keyword in path for keywords in self.PAGE_KEYWORDS.values() for keyword in keywords):
                discovered.append(urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", "")))
        return discovered[:8]

    @staticmethod
    def normalize_url(raw_url: str) -> str:
        value = (raw_url or "").strip()
        if not value:
            raise WebsiteScannerError("URL is required")
        if "://" not in value:
            value = f"https://{value}"
        parsed = urlparse(value)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise WebsiteScannerError("Only valid HTTP or HTTPS URLs can be scanned")
        return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path or "/", "", parsed.query, ""))

    @staticmethod
    def validate_public_url(url: str) -> None:
        parsed = urlparse(url)
        hostname = parsed.hostname
        if not hostname:
            raise WebsiteScannerError("URL hostname is required")
        try:
            addresses = socket.getaddrinfo(hostname, None)
        except socket.gaierror as exc:
            raise WebsiteScannerError(f"Could not resolve hostname: {hostname}") from exc

        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
            ):
                raise WebsiteScannerError("Private, local, or reserved network targets cannot be scanned")

    @staticmethod
    def failed_result(normalized_url: str, reason: str) -> dict[str, Any]:
        return {
            "normalized_url": normalized_url,
            "title": urlparse(normalized_url).hostname,
            "summary": reason,
            "detected_signals": [],
            "evidence_refs": [],
            "gap_findings": [{
                "severity": "high",
                "title": "Scan failed",
                "detail": reason,
            }],
            "classification": {
                "classification": "Scan Failed",
                "risk_level": "unknown",
                "obligation_path": "RETRY_OR_MANUAL_REVIEW",
                "actor_assumption": "Unknown",
                "intake_answers": {},
                "rationale": reason,
            },
            "suggested_actions": [{
                "priority": "medium",
                "title": "Retry with a public website URL",
                "detail": "Confirm the site is reachable and not blocking automated requests.",
            }],
            "source_pages": [],
            "confidence_score": 0,
        }

    @staticmethod
    def excerpt(text: str, start: int, end: int) -> str:
        left = max(start - 120, 0)
        right = min(end + 160, len(text))
        return re.sub(r"\s+", " ", text[left:right]).strip()

    @staticmethod
    def humanize_pattern(pattern: str) -> str:
        cleaned = re.sub(r"\\b|\(|\)|\?|\+|\*", "", pattern)
        cleaned = cleaned.replace("[sd]?", "d").replace("|", "/").replace("\\", "")
        return re.sub(r"\s+", " ", cleaned).strip().title()

    @staticmethod
    def dedupe_preserve_order(values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value in seen:
                continue
            seen.add(value)
            deduped.append(value)
        return deduped

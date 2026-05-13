import ipaddress
import re
import socket
import uuid
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import AiSystem, WebsiteScan
from app.schemas import AiSystemCreate, IntakeCreate, WebsiteScanCreate
from app.services import ai_system_service
from app.services.classification_service import ClassificationService


class WebsiteScannerError(Exception):
    pass


@dataclass
class PageArtifact:
    url: str
    status_code: int
    title: str | None
    text: str
    links: list[str]


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
    COMPLIANCE_PATHS = [
        "/privacy",
        "/privacy-policy",
        "/terms",
        "/terms-of-service",
        "/security",
        "/trust",
        "/compliance",
        "/ai",
        "/responsible-ai",
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
            r"\brisk management\b",
            r"\baudit log(s)?\b",
            r"\bincident\b",
            r"\bmodel card\b",
        ],
        "privacy_security": [
            r"\bprivacy policy\b",
            r"\bgdpr\b",
            r"\bdata processing\b",
            r"\bsecurity\b",
            r"\bsoc 2\b",
            r"\biso 27001\b",
        ],
    }

    PAGE_KEYWORDS = {
        "privacy": ["privacy"],
        "terms": ["terms"],
        "security": ["security", "trust"],
        "ai": ["ai", "artificial-intelligence", "responsible-ai"],
        "compliance": ["compliance", "legal"],
    }

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
    def convert_scan(cls, db: Session, tenant_id: str, scan_id: str) -> tuple[WebsiteScan, AiSystem, Any]:
        scan = cls.get_scan(db, tenant_id, scan_id)
        if scan.status != "completed":
            raise HTTPException(status_code=400, detail="Only completed scans can be converted")
        if scan.ai_system_id and scan.intake_id:
            system = ai_system_service.get_ai_system(db, tenant_id, scan.ai_system_id)
            intake = ClassificationService.get_intake(db, tenant_id, scan.intake_id)
            return scan, system, intake

        classification = scan.classification_json or {}
        answers = classification.get("intake_answers") or {}
        system = ai_system_service.create_ai_system(
            db,
            tenant_id,
            AiSystemCreate(
                name=scan.title or urlparse(scan.normalized_url).hostname or scan.normalized_url,
                description=f"Created from website scan of {scan.normalized_url}. {scan.summary or ''}".strip(),
            ),
        )
        intake = ClassificationService.create_intake(
            db,
            tenant_id,
            IntakeCreate(
                title=f"{system.name} website compliance scan",
                answers=answers,
            ),
        )
        scan.ai_system_id = system.id
        scan.intake_id = intake.id
        db.commit()
        db.refresh(scan)
        return scan, system, intake

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
                        "user-agent": "AIComplianceScanner/0.1 (+https://example.com/compliance-scanner)",
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
            )
        except Exception:
            return None

    def analyze_pages(self, normalized_url: str, pages: list[PageArtifact]) -> dict[str, Any]:
        combined = "\n".join(page.text for page in pages)
        title = pages[0].title or urlparse(normalized_url).hostname
        signals, evidence_refs = self.detect_signals(pages)
        classification = self.classify(signals)
        gaps = self.find_gaps(signals, pages, classification)
        suggested_actions = self.suggest_actions(classification, gaps)
        confidence = self.score_confidence(pages, signals)
        source_pages = [
            {
                "url": page.url,
                "status_code": page.status_code,
                "title": page.title,
                "text_excerpt": page.text[:280],
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
                    }
                    signals.append(signal)
                    evidence_refs.append({
                        "type": "public_page",
                        "category": category,
                        "source_url": page.url,
                        "excerpt": excerpt,
                    })
                    break

        return signals, evidence_refs[:20]

    def classify(self, signals: list[dict[str, Any]]) -> dict[str, Any]:
        categories = {signal["category"] for signal in signals}
        answers = {
            "is_developer": True,
            "is_deployer": False,
            "is_prohibited_use": "prohibited_risk" in categories,
            "is_high_risk_annex_iii": "high_risk_domain" in categories,
            "is_safety_component": False,
            "has_transparency_obligation": bool({"human_interaction", "synthetic_content"} & categories),
            "is_gpai": "gpai" in categories,
        }

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

        return {
            "classification": classification,
            "risk_level": risk_level,
            "obligation_path": obligation_path,
            "actor_assumption": "Provider",
            "intake_answers": answers,
            "rationale": self.classification_rationale(classification, categories),
        }

    def find_gaps(
        self,
        signals: list[dict[str, Any]],
        pages: list[PageArtifact],
        classification: dict[str, Any],
    ) -> list[dict[str, Any]]:
        categories = {signal["category"] for signal in signals}
        page_urls = " ".join(page.url.lower() for page in pages)
        gaps: list[dict[str, Any]] = []

        if "ai_claim" in categories and "governance" not in categories:
            gaps.append({
                "severity": "medium",
                "title": "No public responsible AI governance signal found",
                "detail": "The site appears to mention AI, but the scan did not find public language about oversight, risk management, audit logs, incidents, or responsible AI practices.",
            })
        if classification["risk_level"] in {"high", "prohibited_review"}:
            gaps.append({
                "severity": "high",
                "title": "High-risk language requires manual legal validation",
                "detail": "Public pages contain terms associated with Annex III or prohibited-risk review. Confirm the intended purpose and actual deployment context before relying on this classification.",
            })
        if "human_interaction" in categories and "ai" not in page_urls and "responsible-ai" not in page_urls:
            gaps.append({
                "severity": "medium",
                "title": "AI interaction disclosure page not obvious",
                "detail": "The scan found chatbot/assistant signals, but no obvious AI disclosure or responsible AI page in the crawled URLs.",
            })
        if "privacy_security" not in categories:
            gaps.append({
                "severity": "medium",
                "title": "Privacy/security evidence not found in scanned pages",
                "detail": "The scanner did not find privacy, GDPR, security, SOC 2, or data processing signals in the crawled public pages.",
            })
        if not gaps:
            gaps.append({
                "severity": "low",
                "title": "No critical public-page gaps detected",
                "detail": "The public website contains some governance or privacy evidence. Internal documentation is still required for compliance assurance.",
            })

        return gaps

    def suggest_actions(self, classification: dict[str, Any], gaps: list[dict[str, Any]]) -> list[dict[str, Any]]:
        actions = [
            {
                "priority": "high" if classification["risk_level"] in {"high", "prohibited_review"} else "medium",
                "title": "Confirm intended purpose and actor role",
                "detail": "Validate whether the organization is acting as provider, deployer, importer, or distributor, and document the intended purpose.",
            },
            {
                "priority": "medium",
                "title": "Convert scan into an intake record",
                "detail": "Use the generated intake answers as a draft and complete the classification with internal context.",
            },
        ]
        if any(gap["severity"] == "high" for gap in gaps):
            actions.append({
                "priority": "high",
                "title": "Run counsel/compliance review",
                "detail": "Escalate high-risk or prohibited-risk indicators before using this result in customer-facing claims.",
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

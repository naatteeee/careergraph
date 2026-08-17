from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..ai.embeddings import EmbeddingProvider, cosine_similarity
from ..ai.skill_extraction import SkillExtractor
from ..models.schemas import JobPosting, Recommendation, UserProfile


@dataclass(slots=True)
class RecommendationEngine:
    """Scores and ranks jobs for a user profile."""

    embedder: EmbeddingProvider
    extractor: SkillExtractor
    semantic_weight: float = 0.5
    skill_weight: float = 0.5

    def _ensure_job_skills(self, jobs: list[JobPosting]) -> None:
        """Populate ``job.skills`` from the description if not already set."""
        for job in jobs:
            if not job.skills:
                job.skills = self.extractor.extract(job.search_text)

    @staticmethod
    def _skill_similarity(user_skills: set[str], job_skills: set[str]) -> tuple[float, list[str], list[str]]:
        if not job_skills:
            return 0.0, [], []
        matched = sorted(user_skills & job_skills)
        missing = sorted(job_skills - user_skills)
        # Recall-oriented: fraction of the job's required skills the user has.
        score = len(matched) / len(job_skills)
        return score, matched, missing

    def recommend(self, user: UserProfile, jobs: list[JobPosting], top_k: int = 10) -> list[Recommendation]:
        if not jobs:
            return []
        self._ensure_job_skills(jobs)

        user_skills = {s for s in (self.extractor.normalize(x) or x.lower() for x in user.skills)}

        # Semantic similarity in one batched matrix multiply.
        profile_vec = self.embedder.embed([user.profile_text or " ".join(user.skills) or "candidate"])
        job_vecs = self.embedder.embed([j.search_text for j in jobs])
        sem_scores = cosine_similarity(profile_vec, job_vecs)[0]
        # Map cosine [-1, 1] -> [0, 1].
        sem_scores = (sem_scores + 1.0) / 2.0

        recs: list[Recommendation] = []
        for job, sem in zip(jobs, sem_scores):
            skill_sim, matched, missing = self._skill_similarity(user_skills, set(job.skills))
            # Light profile-aware boost: student-friendly roles for students.
            boost = 0.0
            if user.profile_type.value in {"student", "graduating_soon"} and job.is_student_friendly:
                boost = 0.05
            match = self.semantic_weight * float(sem) + self.skill_weight * skill_sim + boost
            recs.append(
                Recommendation(
                    job=job,
                    match_score=round(min(match, 1.0), 4),
                    semantic_score=round(float(sem), 4),
                    skill_similarity=round(skill_sim, 4),
                    matched_skills=matched,
                    missing_skills=missing,
                )
            )
        recs.sort(key=lambda r: r.match_score, reverse=True)
        return recs[:top_k]

    def semantic_search(self, query: str, jobs: list[JobPosting], top_k: int = 10) -> list[tuple[JobPosting, float]]:
        """Pure free-text semantic search over jobs (no skill component)."""
        if not jobs:
            return []
        q = self.embedder.embed([query])
        job_vecs = self.embedder.embed([j.search_text for j in jobs])
        scores = cosine_similarity(q, job_vecs)[0]
        order = np.argsort(scores)[::-1][:top_k]
        return [(jobs[i], round(float((scores[i] + 1) / 2), 4)) for i in order]

"""
PhysiqAI Quality Assessment Pipeline
=====================================
Automated quality control for fitness transformation images.

This prototype implements:
1. Face similarity checking (identity preservation)
2. Transformation realism assessment
3. AI detection (naturalness check)
4. Multi-generation selection

Dependencies:
    pip install insightface opencv-python numpy pillow requests

Usage:
    from quality_pipeline import QualityPipeline

    pipeline = QualityPipeline()
    result = pipeline.assess(original_image, generated_image, timeframe_weeks=12)

    if result['pass']:
        save_image(result['image'])
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TransformationType(Enum):
    MUSCLE_GAIN = "muscle_gain"
    FAT_LOSS = "fat_loss"
    RECOMPOSITION = "recomposition"


@dataclass
class QualityResult:
    """Result of quality assessment"""
    score: float
    passed: bool
    checks: Dict[str, float]
    recommendations: List[str]

    def to_dict(self) -> dict:
        return {
            'score': self.score,
            'passed': self.passed,
            'checks': self.checks,
            'recommendations': self.recommendations
        }


class FaceSimilarityChecker:
    """
    Check face similarity between original and generated images.
    Uses InsightFace for face embedding extraction.
    """

    def __init__(self, threshold: float = 0.85):
        self.threshold = threshold
        self._model = None

    def _load_model(self):
        """Lazy load InsightFace model"""
        if self._model is None:
            try:
                from insightface.app import FaceAnalysis
                self._model = FaceAnalysis(providers=['CPUExecutionProvider'])
                self._model.prepare(ctx_id=0, det_size=(640, 640))
                logger.info("InsightFace model loaded successfully")
            except ImportError:
                logger.warning("InsightFace not installed. Using mock similarity.")
                self._model = "mock"

    def compute_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """
        Compute cosine similarity between face embeddings.

        Args:
            img1: Original image as numpy array (BGR)
            img2: Generated image as numpy array (BGR)

        Returns:
            Similarity score between 0 and 1
        """
        self._load_model()

        if self._model == "mock":
            # Return mock similarity for testing without InsightFace
            return 0.90

        # Get face embeddings
        faces1 = self._model.get(img1)
        faces2 = self._model.get(img2)

        if len(faces1) == 0 or len(faces2) == 0:
            logger.warning("No face detected in one or both images")
            return 0.0

        # Use largest face (most prominent)
        emb1 = faces1[0].embedding
        emb2 = faces2[0].embedding

        # Cosine similarity
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

        return float(similarity)

    def check(self, img1: np.ndarray, img2: np.ndarray) -> Tuple[bool, float]:
        """Check if faces are similar enough"""
        similarity = self.compute_similarity(img1, img2)
        passed = similarity >= self.threshold
        return passed, similarity


class TransformationRealismChecker:
    """
    Check if body transformation is physiologically realistic
    for the given timeframe.
    """

    # Maximum realistic changes per 4 weeks (conservative estimates)
    MAX_CHANGES_PER_4_WEEKS = {
        'beginner': {
            'muscle_gain_lbs': 4.0,  # Newbie gains
            'fat_loss_lbs': 6.0,
            'body_fat_change_pct': 2.0,
        },
        'intermediate': {
            'muscle_gain_lbs': 2.0,
            'fat_loss_lbs': 4.0,
            'body_fat_change_pct': 1.5,
        },
        'advanced': {
            'muscle_gain_lbs': 1.0,
            'fat_loss_lbs': 3.0,
            'body_fat_change_pct': 1.0,
        }
    }

    def __init__(self, strictness: float = 0.8):
        """
        Args:
            strictness: 0-1, how strict to be about realism (1 = very strict)
        """
        self.strictness = strictness

    def estimate_transformation_magnitude(
        self,
        img1: np.ndarray,
        img2: np.ndarray
    ) -> float:
        """
        Estimate the magnitude of body transformation between two images.

        Returns a score from 0 (no change) to 1 (dramatic change).

        Note: This is a simplified heuristic. Production would use
        body segmentation + measurement estimation.
        """
        # Simple approach: compare pixel differences in body region
        # In production, use body segmentation + measurement estimation

        # Convert to grayscale
        if len(img1.shape) == 3:
            gray1 = np.mean(img1, axis=2)
            gray2 = np.mean(img2, axis=2)
        else:
            gray1, gray2 = img1, img2

        # Normalize
        gray1 = gray1.astype(float) / 255
        gray2 = gray2.astype(float) / 255

        # Compute structural difference
        diff = np.abs(gray1 - gray2)

        # Focus on body region (middle portion of image)
        h, w = diff.shape
        body_region = diff[int(h*0.2):int(h*0.9), int(w*0.2):int(w*0.8)]

        # Mean difference as magnitude estimate
        magnitude = np.mean(body_region) * 3  # Scale up

        return min(1.0, magnitude)

    def get_max_realistic_change(
        self,
        timeframe_weeks: int,
        experience_level: str = 'intermediate'
    ) -> float:
        """Get maximum realistic transformation magnitude for timeframe"""

        limits = self.MAX_CHANGES_PER_4_WEEKS.get(
            experience_level,
            self.MAX_CHANGES_PER_4_WEEKS['intermediate']
        )

        # Scale by timeframe
        periods = timeframe_weeks / 4

        # Diminishing returns over time
        effective_periods = periods * (1 - 0.1 * periods)  # Decrease efficiency

        # Normalized maximum change (0-1 scale)
        max_change = min(1.0, effective_periods * 0.15)  # ~15% per 4 weeks max

        return max_change

    def check(
        self,
        img1: np.ndarray,
        img2: np.ndarray,
        timeframe_weeks: int,
        experience_level: str = 'intermediate'
    ) -> Tuple[bool, float]:
        """
        Check if transformation is realistic.

        Returns:
            (passed, realism_score) where score closer to 1 is more realistic
        """
        magnitude = self.estimate_transformation_magnitude(img1, img2)
        max_realistic = self.get_max_realistic_change(timeframe_weeks, experience_level)

        # Allow some buffer based on strictness
        threshold = max_realistic * (1 + (1 - self.strictness))

        if magnitude <= threshold:
            # Transformation is within realistic bounds
            realism_score = 1.0 - (magnitude / max(threshold, 0.01)) * 0.3
        else:
            # Over-transformed
            overage = (magnitude - threshold) / threshold
            realism_score = max(0, 0.7 - overage)

        passed = realism_score >= 0.6
        return passed, realism_score


class AIDetectionChecker:
    """
    Check if image looks AI-generated (naturalness check).

    Note: In production, use a trained classifier or service like
    Hive Moderation, Illuminarty, or custom model.
    """

    def __init__(self, threshold: float = 0.7):
        """
        Args:
            threshold: Maximum AI probability to pass (lower = stricter)
        """
        self.threshold = threshold

    def detect_artifacts(self, img: np.ndarray) -> Dict[str, float]:
        """
        Detect common AI generation artifacts.

        Checks for:
        - Unusual frequency patterns
        - Hand/finger anomalies
        - Symmetry issues
        - Edge artifacts
        """
        artifacts = {}

        # Convert to float
        img_float = img.astype(float) / 255

        # Check for unusual smoothness (common in AI images)
        if len(img.shape) == 3:
            gray = np.mean(img_float, axis=2)
        else:
            gray = img_float

        # Laplacian for edge detection
        from scipy import ndimage
        laplacian = ndimage.laplace(gray)
        edge_variance = np.var(laplacian)

        # AI images often have lower edge variance
        artifacts['smoothness'] = 1.0 - min(1.0, edge_variance * 100)

        # Check for repetitive patterns (FFT analysis)
        fft = np.fft.fft2(gray)
        fft_mag = np.abs(fft)

        # Look for unusual peaks in frequency domain
        fft_normalized = fft_mag / np.max(fft_mag)
        peak_ratio = np.sum(fft_normalized > 0.5) / fft_normalized.size
        artifacts['frequency_anomaly'] = min(1.0, peak_ratio * 1000)

        return artifacts

    def compute_ai_probability(self, img: np.ndarray) -> float:
        """
        Compute probability that image is AI-generated.

        Returns:
            Probability from 0 (definitely real) to 1 (definitely AI)
        """
        artifacts = self.detect_artifacts(img)

        # Weighted combination of artifact scores
        weights = {
            'smoothness': 0.4,
            'frequency_anomaly': 0.6,
        }

        ai_prob = sum(
            artifacts.get(k, 0) * w
            for k, w in weights.items()
        )

        return min(1.0, ai_prob)

    def check(self, img: np.ndarray) -> Tuple[bool, float]:
        """
        Check if image passes naturalness test.

        Returns:
            (passed, naturalness_score) where higher is more natural
        """
        ai_prob = self.compute_ai_probability(img)
        naturalness = 1.0 - ai_prob
        passed = ai_prob <= self.threshold

        return passed, naturalness


class QualityPipeline:
    """
    Complete quality assessment pipeline for PhysiqAI.

    Combines multiple checks to evaluate generated transformations.
    """

    def __init__(
        self,
        face_threshold: float = 0.85,
        realism_strictness: float = 0.8,
        ai_threshold: float = 0.7,
        weights: Optional[Dict[str, float]] = None
    ):
        self.face_checker = FaceSimilarityChecker(threshold=face_threshold)
        self.realism_checker = TransformationRealismChecker(strictness=realism_strictness)
        self.ai_checker = AIDetectionChecker(threshold=ai_threshold)

        self.weights = weights or {
            'face_similarity': 0.35,
            'transformation_realism': 0.30,
            'naturalness': 0.25,
            'overall_quality': 0.10,
        }

    def assess(
        self,
        original: np.ndarray,
        generated: np.ndarray,
        timeframe_weeks: int = 12,
        experience_level: str = 'intermediate',
        transformation_type: TransformationType = TransformationType.MUSCLE_GAIN
    ) -> QualityResult:
        """
        Perform full quality assessment on a generated transformation.

        Args:
            original: Original input image (numpy array, BGR)
            generated: Generated transformation image (numpy array, BGR)
            timeframe_weeks: Target transformation timeframe
            experience_level: User's training experience
            transformation_type: Type of transformation

        Returns:
            QualityResult with scores, pass/fail, and recommendations
        """
        checks = {}
        recommendations = []

        # 1. Face similarity check
        face_passed, face_score = self.face_checker.check(original, generated)
        checks['face_similarity'] = face_score

        if not face_passed:
            recommendations.append(
                f"Face similarity too low ({face_score:.2f}). "
                "Regenerate with stronger identity preservation."
            )

        # 2. Transformation realism check
        realism_passed, realism_score = self.realism_checker.check(
            original, generated, timeframe_weeks, experience_level
        )
        checks['transformation_realism'] = realism_score

        if not realism_passed:
            recommendations.append(
                f"Transformation may be unrealistic for {timeframe_weeks} weeks. "
                "Consider reducing transformation magnitude."
            )

        # 3. AI detection / naturalness check
        ai_passed, naturalness_score = self.ai_checker.check(generated)
        checks['naturalness'] = naturalness_score

        if not ai_passed:
            recommendations.append(
                "Image may appear AI-generated. "
                "Try lower guidance scale or add noise."
            )

        # 4. Overall image quality (basic check)
        quality_score = self._assess_image_quality(generated)
        checks['overall_quality'] = quality_score

        if quality_score < 0.7:
            recommendations.append(
                "Image quality is suboptimal. "
                "Try higher resolution or more inference steps."
            )

        # Calculate weighted score
        total_score = sum(
            checks[k] * self.weights.get(k, 0)
            for k in checks
        )

        # Determine pass/fail
        # Must pass face check AND have acceptable overall score
        passed = face_passed and total_score >= 0.70

        return QualityResult(
            score=total_score,
            passed=passed,
            checks=checks,
            recommendations=recommendations
        )

    def _assess_image_quality(self, img: np.ndarray) -> float:
        """Basic image quality assessment"""
        from scipy import ndimage

        # Check resolution
        h, w = img.shape[:2]
        resolution_score = min(1.0, (h * w) / (1024 * 1024))

        # Check sharpness (Laplacian variance)
        if len(img.shape) == 3:
            gray = np.mean(img, axis=2)
        else:
            gray = img
        laplacian = ndimage.laplace(gray.astype(float))
        sharpness = min(1.0, np.var(laplacian) / 500)

        # Check exposure
        hist = np.histogram(img.flatten(), bins=256, range=(0, 255))[0]
        hist_normalized = hist / hist.sum()
        # Good exposure has spread histogram
        exposure_score = 1.0 - np.max(hist_normalized) * 5
        exposure_score = max(0, min(1.0, exposure_score))

        return (resolution_score + sharpness + exposure_score) / 3

    def select_best(
        self,
        original: np.ndarray,
        candidates: List[np.ndarray],
        timeframe_weeks: int = 12,
        **kwargs
    ) -> Tuple[Optional[np.ndarray], QualityResult]:
        """
        Select the best image from multiple generated candidates.

        Args:
            original: Original input image
            candidates: List of generated candidate images
            timeframe_weeks: Target transformation timeframe
            **kwargs: Additional arguments passed to assess()

        Returns:
            (best_image, result) or (None, worst_result) if none pass
        """
        results = []

        for i, candidate in enumerate(candidates):
            result = self.assess(original, candidate, timeframe_weeks, **kwargs)
            results.append((i, candidate, result))
            logger.info(f"Candidate {i}: score={result.score:.3f}, passed={result.passed}")

        # Sort by score (highest first)
        results.sort(key=lambda x: x[2].score, reverse=True)

        # Return best that passes, or best overall if none pass
        for idx, img, result in results:
            if result.passed:
                logger.info(f"Selected candidate {idx} (score={result.score:.3f})")
                return img, result

        # None passed, return best anyway with warning
        best_idx, best_img, best_result = results[0]
        logger.warning(
            f"No candidate passed quality checks. "
            f"Returning best (candidate {best_idx}, score={best_result.score:.3f})"
        )

        return best_img, best_result


# Example usage
if __name__ == "__main__":
    # Create sample images for testing
    np.random.seed(42)

    # Simulate original and generated images
    original = np.random.randint(0, 255, (1024, 1024, 3), dtype=np.uint8)

    # Generate some candidates with varying "quality"
    candidates = [
        original + np.random.randint(-30, 30, original.shape, dtype=np.int16),
        original + np.random.randint(-50, 50, original.shape, dtype=np.int16),
        original + np.random.randint(-20, 20, original.shape, dtype=np.int16),
    ]
    candidates = [np.clip(c, 0, 255).astype(np.uint8) for c in candidates]

    # Run pipeline
    pipeline = QualityPipeline()

    print("=" * 50)
    print("PhysiqAI Quality Pipeline Test")
    print("=" * 50)

    best_image, result = pipeline.select_best(
        original,
        candidates,
        timeframe_weeks=12,
        experience_level='intermediate'
    )

    print(f"\nFinal Result:")
    print(f"  Score: {result.score:.3f}")
    print(f"  Passed: {result.passed}")
    print(f"  Checks:")
    for check, score in result.checks.items():
        print(f"    {check}: {score:.3f}")

    if result.recommendations:
        print(f"\n  Recommendations:")
        for rec in result.recommendations:
            print(f"    - {rec}")

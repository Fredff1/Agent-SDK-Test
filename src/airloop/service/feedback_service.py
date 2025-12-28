from airloop.domain.schema import FeedbackRequest
from airloop.service.observility_service import ObservabilityService, NoopObservabilityService


class FeedbackService:
    def __init__(self, obs_service: ObservabilityService | None = None):
        self.obs_service = obs_service or NoopObservabilityService()

    def submit(self, feedback: FeedbackRequest):
        # score name fixed for user ratings
        self.obs_service.score(
            trace_id=feedback.trace_id,
            name="user_feedback",
            value=float(feedback.score),
            comment=feedback.comment,
        )
        return {"status": "ok"}

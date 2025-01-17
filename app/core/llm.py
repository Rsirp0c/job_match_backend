import cohere
from app.core.config import settings

cohere_client = cohere.ClientV2(settings.COHERE_API_KEY, log_warning_experimental_features=False)
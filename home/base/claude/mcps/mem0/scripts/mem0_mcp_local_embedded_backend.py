import os


class LocalEmbeddedMemoryBackend:
    backend_name = "local"

    def __init__(self, store_directory, embedding_model, collection_name):
        self.store_directory = store_directory
        self.embedding_model = embedding_model
        self.collection_name = collection_name
        self._memory_instance = None

    def is_healthy(self, health_timeout_seconds=None):
        return True

    def add(self, text, user_id):
        return self._memory().add(text, user_id=user_id, infer=False)

    def search(self, query, user_id, limit):
        return self._unwrap(
            self._memory().search(query, filters={"user_id": user_id}, limit=limit)
        )

    def list_memories(self, user_id):
        return self._unwrap(self._memory().get_all(filters={"user_id": user_id}))

    def delete(self, memory_id):
        return self._memory().delete(memory_id=memory_id)

    def _unwrap(self, result):
        if isinstance(result, dict) and "results" in result:
            return result["results"]
        return result

    def _memory(self):
        if self._memory_instance is not None:
            return self._memory_instance
        self._apply_cpu_only_and_offline_friendly_environment()
        os.makedirs(self.store_directory, exist_ok=True)
        from mem0 import Memory

        self._memory_instance = Memory.from_config(self._build_configuration())
        return self._memory_instance

    def _build_configuration(self):
        return {
            "vector_store": {
                "provider": "chroma",
                "config": {
                    "path": self.store_directory,
                    "collection_name": self.collection_name,
                },
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": self.embedding_model,
                    "model_kwargs": {"device": "cpu"},
                },
            },
            "llm": {
                "provider": "openai",
                "config": {
                    "api_key": "local-fallback-llm-never-called-because-infer-is-false",
                    "model": "gpt-4o-mini",
                },
            },
        }

    def _apply_cpu_only_and_offline_friendly_environment(self):
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
        os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
        os.environ.setdefault("MEM0_TELEMETRY", "False")
        os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

"""Step252: explicit real FLAN-T5-small CPU inference, NOT a server model.

Asset acquisition is restricted to one reviewed immutable Hugging Face
revision. Safetensors weight digest is independently checked; pickle and
remote Python code are forbidden. Downloads and inference are opt-in only.
The output is an untrusted candidate, never a source-verified fact.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

MODEL_REPO = "google/flan-t5-small"
MODEL_REVISION = "0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab"
MODEL_FILE = "model.safetensors"
MODEL_SHA256 = "495fa51e204676f1a857a9fc13c4c89f3f5ba9f480b898cebca02add25e6d749"
ALLOWED_FILES = (
    "config.json", "generation_config.json", "model.safetensors",
    "special_tokens_map.json", "tokenizer.json", "tokenizer_config.json",
)
MODEL_MAX_BYTES = 320_000_000


class GenerativeModelUnavailable(ValueError):
    """Fixed failure reason with no private paths or publisher text."""


def _check_weights(path: Path) -> None:
    if (
        not isinstance(path, Path) or not path.is_file()
        or not 0 < path.stat().st_size <= MODEL_MAX_BYTES
    ):
        raise GenerativeModelUnavailable("verified_model_unavailable")
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != MODEL_SHA256:
        raise GenerativeModelUnavailable("verified_model_digest_mismatch")


class FLANT5ClaimProposer:
    """Isolated CPU model, token-bounded and deterministic decoding."""

    def __init__(self, model: object, tokenizer: object):
        self._model = model
        self._tokenizer = tokenizer

    def propose(self, question: str) -> str:
        if (
            type(question) is not str or not 0 < len(question) <= 300
            or question != question.strip() or any(c in question for c in "\r\n\x00")
        ):
            raise GenerativeModelUnavailable("invalid_model_question")
        prompt = (
            "Rewrite the following yes-or-no question as one declarative "
            "sentence. Preserve names, versions, dates, negation and all "
            "meaning. Output just that single statement.\nQuestion: "
            + question + "\nStatement:"
        )
        try:
            import torch
            inputs = self._tokenizer(
                prompt, return_tensors="pt", max_length=192,
                truncation=True, padding=False,
            )
            with torch.inference_mode():
                tokens = self._model.generate(
                    **inputs, max_new_tokens=64, do_sample=False,
                    num_beams=1,
                )
            result = self._tokenizer.decode(
                tokens[0], skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )
            if type(result) is not str or len(result) > 500:
                raise GenerativeModelUnavailable("invalid_model_output")
            return result.strip()
        except GenerativeModelUnavailable:
            raise
        except Exception:
            raise GenerativeModelUnavailable("model_generation_failed") from None


def load_real_proposer(*, cache_dir: Path, live: bool) -> FLANT5ClaimProposer:
    """No implicit downloads or model execution on application import."""
    if live is not True:
        raise GenerativeModelUnavailable("explicit_model_opt_in_required")
    if not isinstance(cache_dir, Path) or not cache_dir.is_absolute():
        raise GenerativeModelUnavailable("invalid_model_cache")
    try:
        from huggingface_hub import snapshot_download
        location = Path(snapshot_download(
            repo_id=MODEL_REPO, revision=MODEL_REVISION,
            cache_dir=str(cache_dir), allow_patterns=list(ALLOWED_FILES),
        ))
        _check_weights(location / MODEL_FILE)
        from transformers import AutoTokenizer, T5ForConditionalGeneration
        import torch
        # Restrict the model to local verified assets; never trust Python
        # files from a model repository or load pickle .bin checkpoints.
        torch.set_num_threads(2)
        tokenizer = AutoTokenizer.from_pretrained(
            str(location), local_files_only=True, trust_remote_code=False,
            use_fast=True,
        )
        model = T5ForConditionalGeneration.from_pretrained(
            str(location), local_files_only=True, trust_remote_code=False,
            use_safetensors=True,
        ).eval().to("cpu")
        if getattr(model.config, "model_type", None) != "t5":
            raise GenerativeModelUnavailable("unexpected_model_architecture")
        return FLANT5ClaimProposer(model, tokenizer)
    except GenerativeModelUnavailable:
        raise
    except Exception:
        raise GenerativeModelUnavailable("model_runtime_unavailable") from None


__all__ = [
    "MODEL_REPO", "MODEL_REVISION", "MODEL_SHA256", "ALLOWED_FILES",
    "GenerativeModelUnavailable", "FLANT5ClaimProposer", "load_real_proposer",
]

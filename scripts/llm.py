#!/usr/bin/env python3
"""One small client for the optional model steps (card extraction and card checking), whatever model you run.

The comic pipeline itself needs no model: the scripts check, draw and export on their own. A model is used only to *draft*
claims from a PDF (scripts/extract_cards.py) and to give a second opinion on them (scripts/verify_cards.py). Both go through
this file, so you choose the model with three settings and nothing else changes:

    LLM_BACKEND   ollama | openai | anthropic         (default: ollama)
    LLM_BASE_URL  where the server is                  (default for ollama: http://localhost:11434)
    LLM_MODEL     the model's name on that server
    LLM_API_KEY   only for a hosted service; set it in the environment, never on the command line

Backends:
  ollama     Ollama's own API (/api/chat). Local or on another machine.
  openai     any server that speaks the OpenAI chat-completions API (/chat/completions): llama.cpp's llama-server, vLLM, LM Studio,
             LocalAI, Ollama's /v1 address, OpenRouter, OpenAI itself and most hosted services. Give the base URL up to and
             including /v1.
  anthropic  Anthropic's Messages API (https://api.anthropic.com).

The older OLLAMA_HOST / OLLAMA_MODEL / OLLAMA_VERIFY_MODEL variables still work and imply the ollama backend.

    python scripts/llm.py --ping          # one tiny request: proves the address, the key and the model name work
    python scripts/llm.py --list          # the model names the server offers (ollama and openai backends)

Only the standard library is used.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

DEFAULT_BASE = {"ollama": "http://localhost:11434", "openai": "http://localhost:8080/v1", "anthropic": "https://api.anthropic.com"}
BACKENDS = tuple(DEFAULT_BASE)


class LLMError(RuntimeError):
    """A readable reason a model call failed (bad address, bad key, unknown model, server error)."""


def settings(backend=None, base_url=None, model=None, env=None, model_env="LLM_MODEL"):
    """Resolve the model settings: explicit arguments first, then LLM_* variables, then the older OLLAMA_* ones."""
    env = os.environ if env is None else env
    legacy = bool(env.get("OLLAMA_HOST") or env.get("OLLAMA_MODEL") or env.get("OLLAMA_VERIFY_MODEL"))
    backend = backend or env.get("LLM_BACKEND") or "ollama"
    if backend not in BACKENDS:
        raise LLMError(f"unknown backend {backend!r}; choose one of {', '.join(BACKENDS)}")
    base = base_url or env.get("LLM_BASE_URL") or (env.get("OLLAMA_HOST") if backend == "ollama" else "") or DEFAULT_BASE[backend]
    mdl = model or env.get(model_env) or ""
    if not mdl and backend == "ollama" and legacy:
        mdl = env.get("OLLAMA_VERIFY_MODEL" if model_env == "LLM_VERIFY_MODEL" else "OLLAMA_MODEL", "")
    return {"backend": backend, "base_url": base.rstrip("/"), "model": mdl, "api_key": env.get("LLM_API_KEY", "")}


def add_arguments(ap, model_env="LLM_MODEL", model_help="the model's name on the server"):
    """Add --backend, --base-url (alias --host) and --model to an argparse parser."""
    ap.add_argument("--backend", choices=BACKENDS, default=None, help="which API the server speaks (default: LLM_BACKEND, else ollama)")
    ap.add_argument("--base-url", "--host", dest="base_url", default=None, help="the server's address (default: LLM_BASE_URL)")
    ap.add_argument("--model", default=None, help=model_help + f" (default: {model_env})")


def _post(url, payload, headers, timeout):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", **headers})
    try:
        return json.load(urllib.request.urlopen(req, timeout=timeout))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:300]
        raise LLMError(f"{url} answered {e.code}: {body}") from e
    except urllib.error.URLError as e:
        raise LLMError(f"could not reach {url}: {e.reason}") from e


def chat(prompt, cfg, temperature=0.0, max_tokens=16000, json_mode=True, num_ctx=32768, timeout=3000):
    """Send one user message and return the reply text. `cfg` is what settings() returns."""
    backend, base, model, key = cfg["backend"], cfg["base_url"], cfg["model"], cfg.get("api_key", "")
    if not model:
        raise LLMError("no model named: pass --model or set LLM_MODEL")
    if backend == "ollama":
        payload = {"model": model, "stream": False, "think": False, "options": {"num_ctx": num_ctx, "temperature": temperature, "num_predict": max_tokens},
                   "messages": [{"role": "user", "content": prompt}]}
        if json_mode:
            payload["format"] = "json"
        return _post(base + "/api/chat", payload, {}, timeout)["message"]["content"]
    if backend == "openai":
        payload = {"model": model, "temperature": temperature, "max_tokens": max_tokens, "messages": [{"role": "user", "content": prompt}]}
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        if json_mode:
            try:  # not every server knows response_format; the prompt asks for JSON anyway, so retry without it
                return _post(base + "/chat/completions", {**payload, "response_format": {"type": "json_object"}}, headers, timeout)["choices"][0]["message"]["content"]
            except LLMError as e:
                if " 400:" not in str(e) and " 422:" not in str(e):
                    raise
        return _post(base + "/chat/completions", payload, headers, timeout)["choices"][0]["message"]["content"]
    if backend == "anthropic":
        if not key:
            raise LLMError("the anthropic backend needs LLM_API_KEY in the environment")
        payload = {"model": model, "max_tokens": max_tokens, "temperature": temperature, "messages": [{"role": "user", "content": prompt}]}
        out = _post(base + "/v1/messages", payload, {"x-api-key": key, "anthropic-version": "2023-06-01"}, timeout)
        return "".join(b.get("text", "") for b in out.get("content", []))
    raise LLMError(f"unknown backend {backend!r}")


def list_models(cfg, timeout=30):
    """The model names the server offers (ollama and openai backends)."""
    base, key = cfg["base_url"], cfg.get("api_key", "")
    headers = {"Authorization": f"Bearer {key}"} if key else {}
    if cfg["backend"] == "ollama":
        req = urllib.request.Request(base + "/api/tags")
        return sorted(m["name"] for m in json.load(urllib.request.urlopen(req, timeout=timeout)).get("models", []))
    if cfg["backend"] == "openai":
        req = urllib.request.Request(base + "/models", headers=headers)
        return sorted(m["id"] for m in json.load(urllib.request.urlopen(req, timeout=timeout)).get("data", []))
    raise LLMError("the anthropic backend has no model list here; see the provider's documentation for model names")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    add_arguments(ap)
    ap.add_argument("--ping", action="store_true", help="send one tiny request and print the reply and the time taken")
    ap.add_argument("--list", action="store_true", help="list the model names the server offers")
    args = ap.parse_args(argv)
    try:
        cfg = settings(args.backend, args.base_url, args.model)
        print(f"backend {cfg['backend']}, server {cfg['base_url']}, model {cfg['model'] or '(none set)'}, key {'set' if cfg['api_key'] else 'not set'}")
        if args.list:
            print("\n".join(list_models(cfg)))
        if args.ping or not args.list:
            t = time.time()
            reply = chat("Reply with the single word: ready", cfg, json_mode=False, max_tokens=50, timeout=120)
            print(f"reply: {reply.strip()[:80]!r} in {time.time() - t:.1f} s")
    except (LLMError, urllib.error.URLError, KeyError, OSError) as e:
        print(f"FAILED: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

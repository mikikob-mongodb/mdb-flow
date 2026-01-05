"""Configuration definitions for evals comparison."""

EVAL_CONFIGS = {
    # Context Engineering (M2)
    "baseline": {
        "name": "Baseline",
        "short": "Base",
        "description": "No optimizations",
        "optimizations": {
            "compress_results": False,
            "streamlined_prompt": False,
            "prompt_caching": False,
        }
    },
    "compress_results": {
        "name": "Compress Results",
        "short": "Compress",
        "description": "Compress tool results to reduce context",
        "optimizations": {
            "compress_results": True,
            "streamlined_prompt": False,
            "prompt_caching": False,
        }
    },
    "streamlined_prompt": {
        "name": "Streamlined Prompt",
        "short": "Streamlined",
        "description": "Use directive, pattern-based prompt",
        "optimizations": {
            "compress_results": False,
            "streamlined_prompt": True,
            "prompt_caching": False,
        }
    },
    "prompt_caching": {
        "name": "Prompt Caching",
        "short": "Caching",
        "description": "Cache system prompt with Anthropic API",
        "optimizations": {
            "compress_results": False,
            "streamlined_prompt": False,
            "prompt_caching": True,
        }
    },
    "all_context": {
        "name": "All Context Engineering",
        "short": "All Ctx",
        "description": "All context engineering optimizations",
        "optimizations": {
            "compress_results": True,
            "streamlined_prompt": True,
            "prompt_caching": True,
        }
    },
}

# Default configs to show selected
DEFAULT_SELECTED = ["baseline", "all_context"]

def get_config_names() -> list:
    """Get list of config keys."""
    return list(EVAL_CONFIGS.keys())

def get_optimizations(config_key: str) -> dict:
    """Get optimizations dict for a config."""
    return EVAL_CONFIGS[config_key]["optimizations"]

#!/usr/bin/env bash
#
# setenv.sh – sets the environment

# ─── 0) Noise-free head-less Qt ──────────────────────────────────────────
export QT_LOGGING_RULES="*.warning=false;qt.qpa.*=false"

# ─── 0b) 3rd-party API keys (keep yours here) ────────────────────────────
export OPENAI_API_KEY="sk-proj-rjJGSlP9rRzc4jNMpt0BT3BlbkFJLMLQHqpdBOaoSow6zM7d"
export PIXABAY_API_KEY="44812949-ba98a63acdbb20b31f0281193"
export PEXELS_API_KEY="e4agaHhuOEpih3K562pmje6YJiy2jSQ37bYJU1nm5nw6NmeualG8afvG"
export UNSPLASH_API_KEY="ATMcaMHzCfB789pGt8m6L5Z3YyvdgndRqiBNaxwmbf8"

# ─── 0c) YouTube OAuth2 / Google Cloud config ────────────────────────────
export YOUTUBE_REDIRECT_URI="https://studio.ai-videocreator.com/oauth2callback"

# ─── 0d) Alternative service tokens (optional) ────────────────────────────
# export HUGGING_FACE_TOKEN="your-huggingface-token-here"

# ─── 0e) Monitoring and fallback settings ──────────────────────────────────
export ENABLE_API_MONITORING="true"
export API_RETRY_ATTEMPTS="3"
export API_RETRY_DELAY="2"

# Add to your ~/.bashrc or ~/.profile:
export HUGGING_FACE_TOKEN="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"
export STRIPE_SECRET_KEY="sk_test_51RyjXz3d5aUJQk1CVS3ABwQd5D1hnYdr7t3D87z4UmK8LsbvJBm5730vhejiPN5rqtD5s0bhbXSEERB3TAiJfXU600jzKT18QZ"
export STRIPE_PUBLISHABLE_KEY="pk_test_51RyjXz3d5aUJQk1CGyuqnNLBFP87R2dmtQmIeNTdQjlKbB5QFKRIqsSojFa6mq434ycCRb4tag9efm5CMnGyp8y700Ri8zevKT"
export STRIPE_SUBSCRIPTION_PRICE_ID="price_1Ryjfh3d5aUJQk1CZaoR4Ef4"        # from your Stripe dashboard
export STRIPE_ONE_TIME_PRICE_ID="price_1RyjdO3d5aUJQk1CmrFNSup6"

export STRIPE_WEBHOOK_SECRET="we_1Ryjmw3d5aUJQk1CwpdRInJO"  # from your Stripe webhook settings

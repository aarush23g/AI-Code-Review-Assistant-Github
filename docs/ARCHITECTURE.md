# Architecture

## Overview

AI Code Review Assistant is a GitHub App-style service that receives pull request webhooks, fetches changed files, analyzes diffs with an LLM, and posts review summaries and selective inline comments.

## Flow

1. GitHub sends pull_request webhook.
2. FastAPI validates webhook signature.
3. GitHub client fetches PR metadata and changed files.
4. Diff parser filters noisy files.
5. Chunker creates LLM-ready review chunks.
6. LLM reviewer generates summary and inline findings.
7. Post-processor filters low-confidence findings.
8. GitHub client posts/updates review comments.
9. Metrics store records review history.

## Main Components

- Webhook Service
- GitHub Client
- Diff Parser
- Review Orchestrator
- LLM Reviewer
- Post Processor
- Metrics Store
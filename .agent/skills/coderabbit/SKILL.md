---
name: coderabbit
description: AI-powered code review and PR autofix using CodeRabbit CLI. Use when the user asks to review code, run coderabbit, check code quality, or resolve PR review comments.
---

# CodeRabbit CLI & AI Review

Run AI-powered code reviews and automated feedback fixes using the official CodeRabbit CLI.

## Quick Reference Commands

- **Local Code Review**:
  ```bash
  coderabbit review --agent
  ```
- **Uncommitted Changes Only**:
  ```bash
  coderabbit review --uncommitted --agent
  ```
- **Committed Changes vs Branch**:
  ```bash
  coderabbit review --committed --base main --agent
  ```
- **Inspect PR Review Comments**:
  ```bash
  coderabbit pullrequest <PR_NUMBER_OR_URL> --show-prompts
  ```
- **Authentication**:
  ```bash
  coderabbit auth status
  coderabbit auth login
  ```
- **Diagnostics**:
  ```bash
  coderabbit doctor
  coderabbit config validate
  ```

## Review Workflow

1. Verify `coderabbit --version`.
2. Check `git status` for clean vs uncommitted changes.
3. Run `coderabbit review --agent` (or with `--uncommitted` / `--committed`).
4. Parse findings by severity: `critical`, `major`, `minor`, `trivial`, `info`.
5. Proactively offer to implement fixes for identified issues.

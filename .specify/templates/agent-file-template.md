# [PROJECT NAME] Development Guidelines

Auto-generated from all feature plans. Last updated: [DATE]

## Active Technologies

[EXTRACTED FROM ALL PLAN.MD FILES]

## Project Structure

```text
[ACTUAL STRUCTURE FROM PLANS]
```

## Commands

[ONLY COMMANDS FOR ACTIVE TECHNOLOGIES]

## Testing Commands

After `/speckit.implement` completes, run the following in order:

1. **Code Review** (required):
   - Run `/rsmdt-the-startup-code-quality-review` to audit code quality
   - Fix all issues before proceeding

2. **Tests** (required):
   - Backend tests: `pytest backend/tests/ -v`
   - Frontend tests: `vitest frontend/ -v`
   - Performance tests: `pytest backend/tests/performance/ -v`

3. **E2E Page Testing** (required):
   - Run `/webapp-testing` to verify UI functionality and user flows

## Code Style

[LANGUAGE-SPECIFIC, ONLY FOR LANGUAGES IN USE]

## Recent Changes

[LAST 3 FEATURES AND WHAT THEY ADDED]

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->

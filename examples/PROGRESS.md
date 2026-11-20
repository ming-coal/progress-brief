# Invoice2Sheet

> Status: **40 handlers scaffolded, 5/40 error paths done** · updated 2026-11-20

## One-liner
Turn invoice photos into editable spreadsheets. Built for myself and a few friends.

## Output
| file | spec | note |
|---|---|---|
| `lib/schema.ts` | 60 columns | table shape locked |
| `src/m*.ts` | 40 files | skeleton only, logic stubbed |
| `status.png` | 1080×1350 | optional share card |

## Progress
| # | item | where | state |
|---|---|---|---|
| 1 | column schema | `lib/schema.ts` | ✅ done |
| 2 | 40-step pipeline skeleton | `src/` | ✅ done |
| 3 | error handling per step | 40 TODOs in `src/` | 🟡 5/40 |
| 4 | parsing tests | `tests/` | 🟡 one empty test |
| 5 | export queue | not started | ⛔ blocked on schema versioning |

## Where things live
- docs: `README.md`, `docs/ARCH.md`
- code: `src/` pipeline, `lib/` data shapes
- tests: `tests/`

## Decisions
| topic | choice | why |
|---|---|---|
| backend | Supabase | don't want to run infra |
| export | background queue | OCR is slow, requests would time out |

## Pitfalls
1. `node_modules` almost got committed → added `.gitignore`

## Next
1. finish error handling in `src/m1.ts` through `src/m10.ts` (35 left)
2. replace `tests/a.test.mjs` with real parsing cases
3. wire Supabase, persist parsed rows
4. unblock the export queue: version `lib/schema.ts` first

## Open questions
- Should multiple invoices merge into one sheet?

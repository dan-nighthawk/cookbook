#!/usr/bin/env python3
"""Patch the live YakYak OpenAPI spec so it passes openapi-generator codegen.

The published spec at https://api.yakyak.ai/api/docs-json has a couple of quirks
that break code generation:

  1. Dangling $refs — e.g. `CampaignResponseDto` references
     `#/components/schemas/CampaignMovieDto`, but that schema is not defined under
     `components.schemas`. The generator then emits imports to a model it never
     created, so the TypeScript build fails.

  2. OpenAPI 3.1 `examples` (plural) used inside 3.0 *schema* objects (e.g.
     `SendFreeTrialDto.email.examples`). `examples` is only valid on MediaType /
     Parameter objects in 3.0, not on schemas, so validation rejects it.

This script applies targeted, generic fixes and writes the patched spec out. It is
intentionally conservative: it only strips `examples` *within components.schemas*
(where it is never valid in 3.0) and only stubs refs that are genuinely missing.

Usage:
    python sdk/patch-spec.py <input.json> <output.json>
"""
import json
import sys


def strip_schema_examples(node):
    """Recursively remove `examples` keys anywhere under a schema subtree.

    Safe because this is only ever called on components.schemas, where `examples`
    is not a valid keyword in OpenAPI 3.0 (only `example` is).
    """
    removed = 0
    if isinstance(node, dict):
        if "examples" in node:
            del node["examples"]
            removed += 1
        for value in node.values():
            removed += strip_schema_examples(value)
    elif isinstance(node, list):
        for item in node:
            removed += strip_schema_examples(item)
    return removed


def add_missing_response_content(paths):
    """Give success responses a body schema so the client returns the payload.

    typescript-fetch (and the Python generator) emit a `void`/`None` return for
    any 2xx response that has no `content`, silently discarding the JSON body.
    The live spec omits response schemas on almost every endpoint, so methods
    like `getStyles()` resolve to `undefined` even though the API returns data.

    Inject a permissive `application/json` object schema for every 2xx response
    (other than 204 No Content) that lacks one. The generated method then parses
    and returns the body, typed loosely as an object. Error responses (4xx/5xx)
    are left untouched — they don't affect the success return type.
    """
    added = 0
    for ops in paths.values():
        if not isinstance(ops, dict):
            continue
        for op in ops.values():
            if not isinstance(op, dict):
                continue
            for code, resp in (op.get("responses") or {}).items():
                if not isinstance(resp, dict):
                    continue
                if not code.startswith("2") or code == "204":
                    continue
                if "content" in resp:
                    continue
                resp["content"] = {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "additionalProperties": True,
                            "description": (
                                "Auto-added by sdk/patch-spec.py: the source spec "
                                "declared no response body schema, so the client "
                                "would otherwise return void and drop the payload."
                            ),
                        }
                    }
                }
                added += 1
    return added


def collect_schema_refs(node, refs):
    """Collect every `#/components/schemas/<name>` reference in the document."""
    prefix = "#/components/schemas/"
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str) and ref.startswith(prefix):
            refs.add(ref[len(prefix):])
        for value in node.values():
            collect_schema_refs(value, refs)
    elif isinstance(node, list):
        for item in node:
            collect_schema_refs(item, refs)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)

    src, dst = sys.argv[1], sys.argv[2]
    with open(src) as f:
        spec = json.load(f)

    # 0. Fill publisher metadata the live spec omits. The Python generator reads
    #    author/license straight from `info`, and both generators read `servers`
    #    for the client base URL. typescript-fetch ignores `info.contact`/
    #    `info.license`, so these are no-ops for the npm build (which sets the
    #    same fields via `npm pkg set` in the workflow).
    info = spec.setdefault("info", {})
    info.setdefault("contact", {
        "name": "YakYak Support",
        "email": "support@yakyak.ai",
        "url": "https://github.com/yakyak-support/cookbook",
    })
    info.setdefault("license", {
        "name": "Apache-2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0",
    })
    # Safety net: if the deployed API hasn't yet published a `servers` entry, the
    # generators would otherwise fall back to http://localhost.
    if not spec.get("servers"):
        spec["servers"] = [{"url": "https://api.yakyak.ai"}]

    schemas = spec.setdefault("components", {}).setdefault("schemas", {})

    # 1. Strip schema-level `examples` (3.1 leakage) from every defined schema.
    removed = strip_schema_examples(schemas)

    # 1b. Give success responses a body schema so generated methods return the
    #     payload instead of `void` (the live spec omits response schemas).
    bodies = add_missing_response_content(spec.get("paths", {}))

    # 2. Stub any referenced-but-undefined schema so $refs resolve and the
    #    generator produces a (permissive) model instead of a dangling import.
    referenced = set()
    collect_schema_refs(spec, referenced)
    missing = sorted(referenced - set(schemas))
    for name in missing:
        schemas[name] = {
            "type": "object",
            "additionalProperties": True,
            "description": (
                "Auto-stubbed by sdk/patch-spec.py: referenced by the spec but "
                "not defined under components.schemas in the source document."
            ),
        }

    with open(dst, "w") as f:
        json.dump(spec, f, indent=2)

    print(f"patched spec written to {dst}")
    print(f"  removed {removed} schema-level 'examples' key(s)")
    print(f"  added body schema to {bodies} success response(s)")
    print(f"  stubbed {len(missing)} missing schema(s): {missing or 'none'}")


if __name__ == "__main__":
    main()

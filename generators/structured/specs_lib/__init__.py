"""Builders for the structured 'specs' part (ST027-ST060): JSON, XML, YAML/YML and wiki HTML.

Entry point: generators/structured/gen_specs.py. Each builder module exposes BUILDERS, a dict
{file_id: callable(ctx) -> Built}. Everything is derived from the world model; randomness only
comes from generators.common.util.rng(key).
"""

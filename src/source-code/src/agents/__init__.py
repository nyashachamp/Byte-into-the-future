"""Agent logic modules for the Public Service Risk Dashboard.

Each module contains the pure logic for one of the five planned agents.
They are called by pipeline.analyze() and will also back the watsonx
Orchestrate specialist tool packages in M1.

Modules
-------
investigator   : Security Investigator — input validation, exception suppression,
                 baseline comparison.
analyst        : Risk & Dependency Analyst — service mapping, score calculation,
                 notification trigger.
response_agent : Response Agent — authorization gate, sandbox action, bounded retry.
verifier       : Verification & Handoff — independent state read, outcome routing,
                 handoff packet assembly.
"""

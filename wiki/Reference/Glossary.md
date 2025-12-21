# Glossary

## Scenario

A `crml_scenario: "1.0"` document describing frequency + severity assumptions (and optionally referenced controls).

See: [Language/Schemas/Scenario](../Language/Schemas/Scenario.md)

## Portfolio

A `crml_portfolio: "1.0"` document that defines exposure (assets, cardinalities) and binds scenarios.

See: [Language/Schemas/Portfolio](../Language/Schemas/Portfolio.md)

## EAL

Expected annual loss: the mean of the annual loss distribution.

## VaR

Value at Risk at percentile $p$: the $p$-quantile of the annual loss distribution.

## Basis

The unit semantics of the frequency model (e.g., per organization per year vs per asset unit per year).

See: [CRML Specification (Overview)](CRML-Specification.md)

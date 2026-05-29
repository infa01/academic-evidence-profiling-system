# ESCO Data Setup

This directory is intentionally ignored by Git except for documentation and
placeholder files. The ESCO classification archive is large and should be
downloaded locally by each user.

## Required Local File

Download the ESCO classification JSON-LD archive from the official ESCO
download page:

```text
https://esco.ec.europa.eu/en/use-esco/download
```

The prototype was developed with:

```text
ESCO version: v1.2.1
Content: Classification
File type: JSON-LD
```

Place the downloaded archive here:

```text
data/esco/esco_classification_jsonld.zip
```

The setup scripts expect this exact path and filename.

## Build Local Lookup Files

After adding the zip file, run:

```powershell
python scripts\build_esco_lookup.py
python scripts\build_esco_interpretation_lookup.py
```

This creates:

```text
data/esco/esco_skill_lookup.json
data/esco/esco_interpretation_lookup.json
```

## What These Files Do

`esco_skill_lookup.json` maps ESCO skill URIs to readable English labels.

`esco_interpretation_lookup.json` stores ESCO metadata used by the pipeline,
including:

- preferred skill labels;
- skill type;
- reuse level;
- transversal/sector-specific interpretation;
- essential occupation links;
- optional occupation links.

## What These Scripts Do Not Do

The setup scripts do not decide which ESCO skills are relevant to a student.
They only build the local ESCO reference data.

Relevant skills are selected later by the pipeline:

```text
learning outcomes
-> candidate ESCO extraction
-> semantic similarity filtering
-> retained ESCO skill evidence
```

## Git Policy

Do not commit:

```text
data/esco/esco_classification_jsonld.zip
data/esco/esco_skill_lookup.json
data/esco/esco_interpretation_lookup.json
```

These files are generated or downloaded locally.

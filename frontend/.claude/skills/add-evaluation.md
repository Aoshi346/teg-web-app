---
name: add-evaluation
description: Add new evaluation questions or sections to the scoring system
user_invocable: true
arguments:
  - name: document_type
    description: "Which document type: Proyecto, Tesis, or Both"
    required: true
  - name: section
    description: "The section name: Diagramacion, Contenido, or a new section name"
    required: true
---

# Add Evaluation Questions

Add new evaluation questions or sections to TesisFar's scoring system.

## System Overview

The evaluation system has two dimensions:
- **Diagramacion** (Formatting): 5 points total — checks layout, fonts, margins, structure
- **Contenido** (Content): 15 points total — checks substance, methodology, conclusions
- **Total**: 20 points, passing threshold: 10 points
- **Thesis** projects have two sequential phases (fase1, fase2); **Proyecto** has one evaluation

## Question Types

Defined in `src/lib/questions/questions.ts`:

| `answerType` | Options | Use Case |
|---|---|---|
| `yesno` | No (1), Sí (2) | Binary compliance checks |
| `frequency` | Muy Poco (1), Medianamente (2), Sí/Siempre (3), No aplica (4) | Degree of adherence |
| `ternary` | No (1), Medianamente (2), Sí (3) | Three-level assessment |
| `ternary_na` | No, Medianamente, Sí, No se incluyó, No hay subtítulo | With N/A options |
| `ternary_info` | No, Medianamente, Sí, No se incluyó información | With missing info option |
| `text` | Free text | Open-ended observations |

## Steps

1. **Add questions** to `src/lib/questions/questions.ts`:
   - Find the appropriate array: `PROJECT_QUESTIONS` or `TESIS_QUESTIONS`
   - Add new `Question` objects following this structure:
     ```typescript
     {
       id: "qNN",                          // Sequential ID (check last existing ID)
       label: "Question text in Spanish",
       helper: "Optional helper text",       // Shown as tooltip
       section: "{{ section }}",             // "Diagramacion" or "Contenido"
       subsection: "Subsection Name",        // Grouping within the section
       documentType: "{{ document_type }}",  // "Proyecto", "Tesis", or "Both"
       answerType: "yesno",                  // One of the types above
       weight: 0.18,                         // Points for this question
       relatedImage: "/help-image.svg",      // Optional visual aid path (in public/)
     }
     ```

2. **Update scoring logic** in `src/lib/questions/scoring.ts`:
   - If adding to an existing section, verify the total weight still sums correctly:
     - Diagramacion: all weights must sum to 5.0
     - Contenido: all weights must sum to 15.0
   - If creating a new section, add scoring constants and update the `calculateScore()` function
   - Adjust `DIAGRAMACION_WEIGHT` and `CONTENIDO_WEIGHT` if point allocation changes

3. **Update the EvaluationForm** in `src/components/evaluation/EvaluationForm.tsx` if:
   - A new section is being added (needs a new pagination section)
   - New answer types are introduced (needs new input rendering)

4. **Conventions**:
   - Question IDs are sequential: `q1`, `q2`, ..., `qNN`
   - All question labels and helpers must be in **Spanish**
   - Questions are grouped by `section` then `subsection` in the form
   - The form paginates by section — each section is one "page"
   - Draft answers are auto-saved to `localStorage` key: `teg_eval_draft:{type}:{projectId}`

5. **Do NOT**:
   - Change existing question IDs (evaluations in the database reference them)
   - Modify the total point allocation (20 pts) without explicit approval
   - Remove existing questions without checking if they have stored evaluations

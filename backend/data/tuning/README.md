# Tuning Data Directory

This directory contains Q&A pairs for Gemini model tuning.

## Structure

```
tuning/
├── cbse_class9_tuning.json      # Combined tuning data
├── class9_science_tuning.json   # Science Q&A pairs
├── class9_maths_tuning.json     # Maths Q&A pairs
├── class9_sst_tuning.json       # Social Science Q&A pairs
└── class9_english_tuning.json   # English Q&A pairs
```

## Format

Each JSON file contains an array of tuning examples:

```json
[
  {
    "text_input": "Question (marks) [Class Subject]",
    "output": "CBSE-style answer with formatting"
  }
]
```

## Guidelines for Creating Tuning Data

1. **Variety**: Include 1, 2, 3, and 5 mark questions
2. **Formatting**: Use bold, bullets, and proper structure
3. **Terminology**: Use exact NCERT terms
4. **Length**: Match answer length to marks
5. **Quality**: Use actual marking scheme patterns

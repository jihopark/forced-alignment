# Forced Aligment Tool + Childes Dataset
Python 3.5

## Discussed Approach:
1. Separate the each audio file into segments (one per conversation turn) using transcription
2. Use force alignment tool to create further segments (one per word)
3. Using the most frequent words, choose the most important keywords to detect
4. Train a classifier to detect keyword

- this repository is for 1~2.

## Dataset:
From CHILDES Dataset
- Gleason (2~5 years old) - father/mother children conversation
- Weist (2~5 years old) - 6 kids. Little bit noisy but okay
- Van Houten (2-3 years old) - bit short, but okay

## Forced Alignment Tools:
Which one to use? Documentation (v), Python (v), Easy to use (v), Need to test Different algorithms
### Candidates:
- AENAS (DTW algorithm) : See `aeneas_test.ipynb`
- ~~FAVE (HMM; HTK based)~~
- ~~Montreal (HMM; Kaldi based)~~
- ~~SPPAS (HMM; Julius based)~~


# Prepare your training text

1. Write or export plain text and save it as a **`.txt` file encoded as UTF-8**. Keep paragraphs and sensible separators; remove page headers, navigation, and material you do not have permission to use. Do not put passwords, private data, or confidential text in a training file.
2. Copy the file into this `Training_Data/` folder (subfolders are also scanned). The dashboard lists available `.txt` files when it loads; refresh the page after adding files.
3. In **Training**, select one or more files. The combined `training_corpus.txt` is selected by default. If you select that combined corpus, do not also select its individual source books unless you intentionally want their text repeated.
4. Choose **Train from scratch** for a tiny character-level learning demo, or **Fine-tune a saved model** to continue a checkpoint such as Pythia-70M. Fine-tuning adapts the model to your examples; it does not guarantee that the result will be accurate or follow instructions.

Use enough text for the context length you select. Very small or repetitive files can overfit quickly. Files are combined in selection order and remain on your computer.

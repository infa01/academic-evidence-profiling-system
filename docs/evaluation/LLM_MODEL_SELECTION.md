# LLM Model Selection Dissertation Insert

This text can be inserted into Chapter 4, near the RAG reports/evaluation
section, or adapted into Chapter 3 if the model-selection process is discussed
as part of the methodology.

## Greek Draft

Για την παραγωγή των RAG-supported reports αξιολογήθηκαν διαφορετικά τοπικά
γλωσσικά μοντέλα μέσω Ollama. Η αξιολόγηση δεν είχε ως στόχο να αποτελέσει
γενικό leaderboard μοντέλων, αλλά να εξετάσει ποιο μοντέλο μπορεί να παραγάγει
την αναφορά του prototype με ικανοποιητική ισορροπία ανάμεσα σε χρόνο εκτέλεσης,
πληρότητα δομής, αποφυγή υπερβολικών ισχυρισμών και πρακτική λειτουργία σε
τοπικό hardware. Η τοπική εκτέλεση επιλέχθηκε επίσης επειδή περιορίζει την
ανάγκη αποστολής φοιτητικών δεδομένων σε εξωτερικές υπηρεσίες LLM.

Η αξιολόγηση πραγματοποιήθηκε στο ίδιο RAG prompt, με τα ίδια retrieved evidence
chunks, temperature 0.2 και output budget `num_predict=900`. Το test περιβάλλον
ήταν AMD Ryzen 7 2700X, 16GB DDR4 RAM και NVIDIA GTX 1050 Ti 4GB. Τα μοντέλα
που συγκρίθηκαν ήταν `phi3:mini`, `mistral`, `qwen2.5:7b`, `llama3.1:8b` και
`gemma2:9b`.

| Model | Total script time | LLM request time | Tokens/sec | Quality gate |
|---|---:|---:|---:|---|
| `phi3:mini` | 126.135s | 118.932s | 6.38 | Passed |
| `mistral` | 136.503s | 131.974s | 3.61 | Passed |
| `qwen2.5:7b` | 178.972s | 173.993s | 3.76 | Passed |
| `llama3.1:8b` | 217.030s | 211.163s | 3.18 | Passed |
| `gemma2:9b` | 306.676s | 302.029s | n/a | Failed: timeout |

Το `phi3:mini` ήταν το ταχύτερο επιτυχημένο μοντέλο, αλλά η ποιοτική επιθεώρηση
του output έδειξε πιο αδύναμο evidence handling, placeholders και λιγότερο
σταθερή διατύπωση. Το `mistral` παρήγαγε σύντομη και καθαρή αναφορά, όμως με
λιγότερο αναλυτικό βάθος. Το `llama3.1:8b` λειτούργησε ως ισχυρό baseline, αλλά
με μεγαλύτερο χρόνο εκτέλεσης. Το `gemma2:9b` δεν θεωρήθηκε πρακτική επιλογή
στο συγκεκριμένο hardware, καθώς ξεπέρασε το χρονικό όριο. Με βάση αυτή τη
σύγκριση, το `qwen2.5:7b` επιλέχθηκε ως default μοντέλο, επειδή προσέφερε την
καλύτερη ισορροπία ανάμεσα σε ποιότητα, πληρότητα αναφοράς και χρόνο εκτέλεσης.

Η επιλογή αυτή στηρίζεται επίσης στη βιβλιογραφία για small/local language
models και RAG, όπου η αποτελεσματικότητα δεν εξαρτάται μόνο από το μέγεθος του
μοντέλου, αλλά και από την ικανότητά του να ακολουθεί οδηγίες, να αξιοποιεί το
retrieved context και να παράγει σταθερό output με περιορισμένο prompt budget
(Mohammadi et al., 2026; Qwen Team, 2024). Συνεπώς, το LLM component της
εργασίας αξιολογείται ως evidence-grounded generation layer και όχι ως
ανεξάρτητος μηχανισμός αξιολόγησης επαγγελματικής καταλληλότητας.

## Reference Pointers

- Qwen Team (2024) Qwen2.5 Technical Report.
- Microsoft (2024) Phi-3 Technical Report.
- Meta (2024) Llama 3.1 release/model information.
- Mistral AI (2023) Mistral 7B model card.
- Google DeepMind (2024) Gemma 2 technical report.
- Mohammadi et al. (2026) Evaluating Prompt Engineering Techniques for RAG in Small Language Models.

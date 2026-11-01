# Included training data

`training_corpus.txt` combines five cleaned public-domain book texts with the small original practice text in `corpus.txt` (original project text dedicated to CC0 1.0). At about 2.8 million characters it is ready for scratch training and fine-tuning. Individual book files are in `books/`.

| Text | Author (died) | Source edition |
|---|---|---|
| *Pride and Prejudice* | Jane Austen (1817) | [Standard Ebooks](https://standardebooks.org/ebooks/jane-austen/pride-and-prejudice) |
| *Alice’s Adventures in Wonderland* | Lewis Carroll (1898) | [Standard Ebooks](https://standardebooks.org/ebooks/lewis-carroll/alices-adventures-in-wonderland/john-tenniel) |
| *Treasure Island* | Robert Louis Stevenson (1894) | [Standard Ebooks](https://standardebooks.org/ebooks/robert-louis-stevenson/treasure-island) |
| *Little Women* | Louisa May Alcott (1888) | [Standard Ebooks](https://standardebooks.org/ebooks/louisa-may-alcott/little-women) |
| *The Adventures of Sherlock Holmes* | Arthur Conan Doyle (1930) | [Standard Ebooks](https://standardebooks.org/ebooks/arthur-conan-doyle/the-adventures-of-sherlock-holmes) |

The underlying works are out of copyright; Standard Ebooks dedicates its edition contributions to the worldwide public domain under CC0 1.0. Cleaned text was extracted from their EPUB editions; packaging and ebook branding were not included. Refer to each source page and its Uncopyright/Imprint notes for provenance and terms.

`tinyshakespeare.txt` is the 1,115,394-character Tiny Shakespeare corpus referenced by nanoGPT’s official character-level preparation script, from Andrej Karpathy’s char-rnn repository: [pinned source file](https://github.com/karpathy/char-rnn/blob/6f9487a6fe5b420b7ca9afb0d7c078e37c1d1b4e/data/tinyshakespeare/input.txt). Shakespeare’s original plays are public domain. This copy is used to train the bundled nanoGPT starter; SHA-256: `86c4e6aa9db7c042ec79f339dcb96d42b0075e16b8fc2e86bf0ca57e2dc565ed`. The books remain the default user training corpus.

These compact classic-text samples are suitable for learning/testing small models, not for creating a capable general-purpose LLM. Use only data you have the right to train on.

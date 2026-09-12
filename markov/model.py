import random, os
from collections import defaultdict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
_TRAIN_DATA = os.getenv('TRAIN_ARTICLES')

class Markov:
    def __init__(self):
        self.chain_3 = defaultdict(dict) # {(w1, w1, w3): {next_word: count)}
        self.chain_2 = defaultdict(dict) # {(w1, w2): {next_word: count)}

    def train(self, filepath):
        with open(filepath, 'r') as f:
            text = f.read()

        words = text.lower().split() # tokenize

        # Slide through words (3 word chain)
        for i in range(len(words) - 3):
            # Get sequence of words
            current_words = tuple(words[i:i + 3])
            next_word = words[i + 3]
            # Store word
            if next_word not in self.chain_3[current_words]:
                self.chain_3[current_words][next_word] = 0
            self.chain_3[current_words][next_word] += 1

        # Slide through words (2 word chain)
        for i in range(len(words) - 2):
            # Get sequence of words
            current_words = tuple(words[i:i + 2])
            next_word = words[i + 2]
            # Store word
            if next_word not in self.chain_2[current_words]:
                self.chain_2[current_words][next_word] = 0
            self.chain_2[current_words][next_word] += 1

    def generate(self, length=50):
        # Choose a random start chain
        current_words_3 = random.choice(list(self.chain_3.keys()))
        output = list(current_words_3)

        # Continue through
        for i in range(length - 3):
            # 3 Word chain
            if current_words_3 in self.chain_3:
                next_words = self.chain_3[current_words_3]
            else:
                # 2 word chain
                current_words_2 = tuple(output[-2:])
                if current_words_2 not in self.chain_2:
                    break
                next_words = self.chain_2[current_words_2]

            next_word = random.choices(
                 list(next_words.keys()),
                 weights=list(next_words.values())
            )[0]

            output.append(next_word)

            # Slide window
            current_words_3 = tuple(output[-3:])

        return ' '.join(output)

if __name__ == "__main__":
    markov = Markov()
    markov.train(_TRAIN_DATA)
    print(markov.generate(length=100))

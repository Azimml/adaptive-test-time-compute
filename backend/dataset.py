import re

PRESET_QUESTIONS = [
    # Easy
    {
        "id": "easy_1",
        "question": "What is 15 + 27?",
        "answer": "42",
        "difficulty": "easy",
    },
    {
        "id": "easy_2",
        "question": "If a shirt costs $25 and is on sale for 20% off, how much does it cost?",
        "answer": "20",
        "difficulty": "easy",
    },
    {
        "id": "easy_3",
        "question": "A rectangle has a length of 8 cm and a width of 5 cm. What is its area in square cm?",
        "answer": "40",
        "difficulty": "easy",
    },
    {
        "id": "easy_4",
        "question": "There are 15 trees in the grove. Grove workers will plant trees in the grove today. After they are done, there will be 21 trees. How many trees did the grove workers plant today?",
        "answer": "6",
        "difficulty": "easy",
    },
    # Medium
    {
        "id": "med_1",
        "question": "Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. How many clips did Natalia sell altogether in April and May?",
        "answer": "72",
        "difficulty": "medium",
    },
    {
        "id": "med_2",
        "question": "Weng earns $12 an hour for babysitting. Yesterday, she just did 50 minutes of babysitting. How much did she earn?",
        "answer": "10",
        "difficulty": "medium",
    },
    {
        "id": "med_3",
        "question": "Betty is saving money for a new wallet which costs $100. Betty has only half of the money she needs. Her parents decided to give her $15 for that purpose, and her grandparents twice as much as her parents. How much more money does Betty need to buy the wallet?",
        "answer": "5",
        "difficulty": "medium",
    },
    {
        "id": "med_4",
        "question": "Julie is reading a 120-page book. Yesterday, she was able to read 12 pages and today, she read twice as many pages as yesterday. If she wants to read half of the remaining pages tomorrow, how many pages should she read?",
        "answer": "42",
        "difficulty": "medium",
    },
    # Hard
    {
        "id": "hard_1",
        "question": "A merchant wants to make a choice of purchase between 2 purchase plans: jewelry worth $5,000 or electronic gadgets worth $8,000. His financial advisor speculates that the jewelry market will go up 2.5% while the electronic gadgets market will rise 1.2% within the same month. If the merchant is to maximize profit at the end of 5 months by making a choice, how much profit would this be?",
        "answer": "625",
        "difficulty": "hard",
    },
    {
        "id": "hard_2",
        "question": "Elaine initially had 20 Pokemon cards. After a Pokemon card releasing event, she earned 20 times more cards. However, her Pokemon card collection got damaged, and she lost Pokemon cards equal to the square of 5. How many Pokemon cards does she have now?",
        "answer": "395",
        "difficulty": "hard",
    },
    {
        "id": "hard_3",
        "question": "Mark has a garden with flowers. He planted plants of three colors in it. Ten of them are yellow, and there are 80% more of those in red. Blue flowers make up only 25% of the red flowers. How many flowers does Mark have in his garden?",
        "answer": "35",
        "difficulty": "hard",
    },
    {
        "id": "hard_4",
        "question": "Albert is wondering how much pizza he can eat in one day. He buys 2 large pizzas and 2 small pizzas. A large pizza has 16 slices and a small pizza has 8 slices. If he eats it all, how many pieces does he eat that day?",
        "answer": "48",
        "difficulty": "hard",
    },
]


async def load_gsm8k(n_samples: int = None) -> list[dict]:
    """Load GSM8K test set from HuggingFace."""
    try:
        from datasets import load_dataset

        ds = load_dataset("openai/gsm8k", "main", split="test")

        questions = []
        for i, item in enumerate(ds):
            if n_samples and i >= n_samples:
                break

            answer_text = item["answer"]
            match = re.search(r"####\s*(-?\d[\d,]*\.?\d*)", answer_text)
            ground_truth = match.group(1).replace(",", "") if match else None

            questions.append(
                {
                    "id": f"gsm8k_{i}",
                    "question": item["question"],
                    "answer": ground_truth,
                    "full_answer": answer_text,
                    "difficulty": "unknown",
                }
            )

        return questions
    except Exception as e:
        print(f"Could not load GSM8K from HuggingFace: {e}")
        print("Falling back to preset questions.")
        if n_samples:
            return PRESET_QUESTIONS[:n_samples]
        return PRESET_QUESTIONS


def get_presets() -> list[dict]:
    return PRESET_QUESTIONS

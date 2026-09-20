import json
from app.services.ai_service import _count_meaningful_answers

def run_tests():
    print("Running Tests for _count_meaningful_answers...")

    def make_history(answers):
        return [{"role": "user", "content": a} for a in answers]

    # TEST 1: AI Interview 7/7 meaningful
    ans_7 = ["I have 5 years experience in Python.", "My approach is to use React.", "I optimized the database using indices.", "I collaborate using Git.", "I solve conflicts by discussing.", "I am looking for a challenging role.", "My strength is debugging."]
    count_7 = _count_meaningful_answers(make_history(ans_7))
    assert count_7 == 7, f"Expected 7, got {count_7}"

    # TEST 2: AI Interview 2/7 meaningful (rest empty/filler)
    ans_2 = ["I use Python.", "ok", "   ", "yes", "I know React.", "hmm", ""]
    count_2 = _count_meaningful_answers(make_history(ans_2))
    assert count_2 == 2, f"Expected 2, got {count_2}"

    # TEST 3: AI Interview 0/7 meaningful
    ans_0 = ["ok", "yes", "hmm", "   ", "", "nah", "sure"]
    count_0 = _count_meaningful_answers(make_history(ans_0))
    assert count_0 == 0, f"Expected 0, got {count_0}"

    # TEST 4: Voice Screening 5/5
    vs_5 = ["Hello, I am ready.", "I worked as a frontend dev.", "I prefer agile methodologies.", "I handle stress well.", "Thank you."]
    count_vs_5 = _count_meaningful_answers(make_history(vs_5))
    assert count_vs_5 == 5, f"Expected 5, got {count_vs_5}"

    # TEST 5: Voice Screening 1/5
    vs_1 = ["hmm", "ok", "I have some experience with React.", "yes", "  "]
    count_vs_1 = _count_meaningful_answers(make_history(vs_1))
    assert count_vs_1 == 1, f"Expected 1, got {count_vs_1}"

    # TEST 6: Voice Screening 0/5
    vs_0 = ["", "  ", "ok", "yes", "hmm"]
    count_vs_0 = _count_meaningful_answers(make_history(vs_0))
    assert count_vs_0 == 0, f"Expected 0, got {count_vs_0}"

    print("All tests passed successfully!")

if __name__ == "__main__":
    run_tests()

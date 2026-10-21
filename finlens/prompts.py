"""Prompt strategies used when an LLM key is configured. Edit freely for the lab."""
SYSTEM = ("You are a careful financial analyst. Use ONLY facts and numbers present in the report text. "
          "If a figure is not in the report, write 'not found'. Never invent numbers.")

TASK = ("Analyse the report below. Give: 1) Business snapshot (2 sentences) 2) Key figures with year-on-year change "
        "3) Strengths 4) Risks and red flags 5) Overall assessment. Keep it under 350 words.")

FEW_SHOT = ("Example of the expected style:\nKey figures: Revenue 120.4M (up 8.1% from 111.4M); Net profit 9.2M (down 3.0%).\n"
            "Risks: Debt-to-equity rose to 1.8 from 1.4; one customer is 31% of sales.\n")

COT = "Think step by step: first list the figures you can find, then compute changes and ratios, then judge. Show the working briefly before the final answer."

STRATEGIES = {
    "zero_shot": lambda t: f"{TASK}\n\nREPORT:\n{t}",
    "few_shot":  lambda t: f"{TASK}\n\n{FEW_SHOT}\nREPORT:\n{t}",
    "chain_of_thought": lambda t: f"{TASK}\n\n{COT}\n\nREPORT:\n{t}",
}

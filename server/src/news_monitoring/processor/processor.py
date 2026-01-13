from dataclasses import dataclass


@dataclass
class Processor:
    def normalize(self, text: str) -> str:
        return " ".join(text.split())

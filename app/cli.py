"""사용법: python -m app.cli "질문" """

import sys

from app.agent import answer

if __name__ == "__main__":
    print(answer(sys.argv[1]))

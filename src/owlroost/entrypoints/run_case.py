import json
import sys

from owlroost.core.owl_runner import run_single_case


def main():
    args = json.loads(sys.stdin.read())

    result = run_single_case(**args)

    print(
        json.dumps(
            {
                "status": result.status,
                "output_file": result.output_file,
                "summary": result.summary,
            }
        )
    )


if __name__ == "__main__":
    main()

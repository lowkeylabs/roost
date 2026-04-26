import os
import json
import sys

from owlroost.core.configure_logging import configure_logging
configure_logging(os.getenv("OWLROOST_LOG_LEVEL", "INFO"))


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
                "failure_category": result.failure_category,
                "failure_subtype": result.failure_subtype,
                "failure_detail": result.failure_detail,
            }
        )
    )


if __name__ == "__main__":
    main()

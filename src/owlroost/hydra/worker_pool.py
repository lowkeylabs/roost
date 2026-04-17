from loguru import logger


def safe_run_trial(payload):
    """
    payload = (worker_fn, args)
    """
    worker_fn, args = payload

    (
        job_id,
        tid,
        rates_seed,
        longevity_seed,
        case_file,
        overrides,
        run_dir,
        master_seed,
        longevity_cfg,
    ) = args

    try:
        return worker_fn(*args)

    except Exception as e:
        logger.exception(
            "{} - Trial {:04d} crashed: {}",
            job_id,
            tid,
            e,
        )

        return {
            "trial_id": tid,
            "rates_seed": rates_seed,
            "longevity_seed": longevity_seed,
            "status": "error",
            "output": None,
            "error": str(e),
        }

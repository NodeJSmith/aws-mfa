import logging
import sys
from configparser import NoOptionError, RawConfigParser
from pathlib import Path

import pendulum
from humanize import precisedelta
from loguru import logger

from aws_mfa import constants
from aws_mfa.args import (
    ArgsModel,
    get_args,
    get_long_and_short_term_names,
)
from aws_mfa.aws import get_credentials
from aws_mfa.config import get_aws_key_values, get_config, initial_setup
from aws_mfa.utils import log_error_and_exit
from aws_mfa.validate import (
    validate_assume_role,
    validate_device,
    validate_duration,
    validate_profile,
    validate_short_term_config,
)


def do_the_stuff(args: ArgsModel, config: RawConfigParser):
    """Validate the arguments and config object. If the short term credentials section is missing, it will be created.

    Args:
        args (ArgsModel): The command line arguments
        config (RawConfigParser): The config object
    """

    args = validate_profile(args)

    long_term_name, short_term_name = get_long_and_short_term_names(args, config)

    args = validate_device(args, config, long_term_name)
    args = validate_assume_role(args, config, long_term_name)
    args = validate_duration(args)

    key_id, access_key = get_aws_key_values(config, long_term_name)

    force_refresh = validate_short_term_config(config, short_term_name, args, constants.REUP_MESSAGE)

    # check expiration, if expired then set force_refresh = True
    exp, sec_remaining = get_expiration_and_seconds_remaining(config, short_term_name)
    if sec_remaining <= 0:
        force_refresh = True

    if force_refresh:
        get_credentials(short_term_name, key_id, access_key, args, config)
        return

    remaining_str = precisedelta(sec_remaining, suppress=["seconds"])
    logger.info(f"Your credentials are still valid for {remaining_str}, they will expire at {exp}")


def get_expiration_and_seconds_remaining(
    config: RawConfigParser, short_term_name: str
) -> tuple[pendulum.DateTime, int]:
    """Get the expiration time and the seconds remaining until expiration.

    Args:
        config (RawConfigParser): The config object
        short_term_name (str): The name of the short term credentials section

    Returns:
        tuple[pendulum.DateTime, int]: The expiration time and the seconds remaining until expiration
    """
    try:
        exp_str = config.get(short_term_name, "expiration")
        exp: pendulum.DateTime = pendulum.parse(exp_str)  # type: ignore
    except NoOptionError:
        exp = pendulum.datetime(1970, 1, 1, 0, 0, 0, tz=pendulum.UTC)
        exp_str = exp.strftime("%Y-%m-%d %H:%M:%S")

    diff = int((exp - pendulum.now(tz=pendulum.UTC)).total_seconds())

    exp = exp.in_timezone("local")

    return exp, diff


def main():
    args = get_args()
    level = getattr(logging, args.log_level)
    logger.remove()
    logger.configure(handlers=[{"sink": sys.stdout, "level": level, "format": constants.LOGGER_FORMAT}])

    if not args.credentials_path.is_file():
        create = input(
            f"Could not locate credentials file at {args.credentials_path}, would you like to create one?  [y/n]"
        )
        if create.lower() == "y":
            with open(args.credentials_path, "a"):
                pass
        else:
            log_error_and_exit(f"Could not locate credentials file at {args.credentials_path}")

    config = get_config(args.credentials_path)

    if args.setup:
        initial_setup(config, args.credentials_path)
        return

    do_the_stuff(args, config)


def run_aws_mfa(
    assume_role_arn: str,
    short_term_suffix: str,
    token: str | None = None,
    profile: str = "default",
    force: bool = False,
):
    """To be called from outside scripts."""

    args = ArgsModel(
        profile=profile, short_term_suffix=short_term_suffix, assume_role=assume_role_arn, token=token, force=force
    )
    config = get_config(args.credentials_path)
    do_the_stuff(args, config)


if __name__ == "__main__":
    main()

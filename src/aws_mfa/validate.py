import configparser
import os
from configparser import NoOptionError, RawConfigParser

from loguru import logger

from aws_mfa import constants
from aws_mfa.args import ArgsModel
from aws_mfa.utils import log_error_and_exit


def validate_profile(args: ArgsModel) -> ArgsModel:
    if args.profile:
        return args

    if env_aws_profile := os.environ.get("AWS_PROFILE"):
        args.profile = env_aws_profile
    else:
        args.profile = "default"

    return args


def validate_duration(args: ArgsModel) -> ArgsModel:
    # get duration from param, env var or set default
    if args.duration:
        return args

    if env_mfa_sts_duration := os.environ.get("MFA_STS_DURATION"):
        args.duration = int(env_mfa_sts_duration)
    else:
        args.duration = 3600 if args.assume_role else 43200

    return args


def validate_assume_role(args: ArgsModel, config: RawConfigParser, long_term_name: str) -> ArgsModel:
    # get assume_role from param or env var
    if args.assume_role:
        return args

    if env_mfa_assume_role := os.environ.get("MFA_ASSUME_ROLE"):
        args.assume_role = env_mfa_assume_role
    elif config.has_option(long_term_name, "assume_role"):
        args.assume_role = config.get(long_term_name, "assume_role")

    if args.assume_role and not args.role_session_name:
        args.role_session_name = args.short_term_suffix

    return args


def validate_device(args: ArgsModel, config: RawConfigParser, long_term_name: str) -> ArgsModel:
    # get device from param, env var or config
    if args.device:
        return args

    if env_mfa_device := os.environ.get("MFA_DEVICE"):
        args.device = env_mfa_device
    elif config.has_option(long_term_name, "aws_mfa_device"):
        args.device = config.get(long_term_name, "aws_mfa_device")
    else:
        log_error_and_exit(constants.ERR_MFA_DEVICE)

    return args


def validate_short_term_config(config: RawConfigParser, short_term_name: str, args: ArgsModel, reup_message: str):
    """Validate the short term credentials section in the config file. If the section is missing, it will be created.

    Will return a boolean indicating if the credentials should be refreshed.

    Args:
        config (RawConfigParser): The config object
        short_term_name (str): The name of the short term credentials section
        args (ArgsModel): The command line arguments
        reup_message (str): The message to display when re-upping credentials

    Returns:
        bool: Whether the credentials should be refreshed
    """

    force_refresh = False

    # Validate presence of short-term section
    if not config.has_section(short_term_name):
        logger.info(f"Short term credentials section {short_term_name} is missing, obtaining new credentials.")
        if short_term_name == "default":
            try:
                config.add_section(short_term_name)
            # a hack for creating a section named "default"
            except ValueError:
                configparser.DEFAULTSECT = short_term_name
                config.set(short_term_name, "CREATE", "TEST")
                config.remove_option(short_term_name, "CREATE")
        else:
            config.add_section(short_term_name)
        force_refresh = True

        return force_refresh

    # Validate option integrity of short-term section
    required_options = [
        "assumed_role",
        "aws_access_key_id",
        "aws_secret_access_key",
        "aws_session_token",
        "aws_security_token",
        "expiration",
    ]
    try:
        short_term = {}
        for option in required_options:
            short_term[option] = config.get(short_term_name, option)
    except NoOptionError:
        logger.warning("Your existing credentials are missing or invalid, obtaining new credentials.")
        force_refresh = True

    try:
        current_role = config.get(short_term_name, "assumed_role_arn")
    except NoOptionError:
        current_role = None

    if args.force:
        logger.info("Forcing refresh of credentials.")
        force_refresh = True

    # There are not credentials for an assumed role, but the user is trying to assume one
    elif current_role is None and args.assume_role:
        logger.info(reup_message)
        force_refresh = True

    # There are current credentials for a role and the role arn being provided is the same.
    elif current_role is not None and current_role == args.assume_role:
        pass

    # There are credentials for a current role and the role that is attempting to be assumed is different
    elif (
        current_role is not None
        and args.assume_role
        and current_role != args.assume_role
        or current_role is not None
        and args.assume_role is None
    ):
        logger.info(reup_message)
        force_refresh = True

    return force_refresh

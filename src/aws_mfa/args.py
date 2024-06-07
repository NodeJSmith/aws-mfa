import argparse
import getpass
from configparser import RawConfigParser
from pathlib import Path

from loguru import logger
from pydantic import BaseModel

from aws_mfa import constants
from aws_mfa.utils import log_error_and_exit

AWS_CREDS_PATH = Path("~/.aws/credentials").expanduser()


class ArgsModel(BaseModel):
    """Model for the command line arguments.

    An instance of this model is created by dumping the args namespace.
    """

    device: str | None = None
    duration: int | None = None
    profile: str | None = None
    long_term_suffix: str | None = None
    short_term_suffix: str | None = None
    assume_role: str | None = None
    role_session_name: str | None = None
    force: bool | None = None
    log_level: str | None = None
    setup: bool | None = None
    token: str | None = None
    credentials_path: Path = AWS_CREDS_PATH


def get_args() -> ArgsModel:
    parser = argparse.ArgumentParser()

    parser.add_argument("--device", required=False, metavar=constants.METAVAR_DEVICE, help=constants.HELP_DEVICE)
    parser.add_argument("--duration", type=int, help=constants.HELP_DURATION)
    parser.add_argument("--profile", help=constants.HELP_PROFILE, required=False)
    parser.add_argument("--long-term-suffix", "--long-suffix", help=constants.HELP_LONG_TERM_SUFFIX, required=False)
    parser.add_argument("--short-term-suffix", "--short-suffix", help=constants.HELP_SHORT_TERM_SUFFIX, required=False)
    parser.add_argument(
        "--assume-role",
        "--assume",
        metavar=constants.METAVAR_ASSUME_ROLE,
        help=constants.HELP_ASSUME_ROLE,
        required=False,
    )
    parser.add_argument(
        "--role-session-name", help=constants.HELP_ROLE_SESSION_NAME, default=getpass.getuser(), required=False
    )
    parser.add_argument("--force", help=constants.HELP_FORCE, action="store_true", required=False)
    parser.add_argument(
        "--log-level", help="Set log level", choices=constants.CHOICES_LOG_LEVEL, required=False, default="DEBUG"
    )
    parser.add_argument("--setup", help=constants.HELP_SETUP, action="store_true", required=False)
    parser.add_argument("--token", "--mfa-token", type=str, help="Provide MFA token as an argument", required=False)
    args: ArgsModel = parser.parse_args()

    args = ArgsModel(**vars(args))

    return args


def get_long_and_short_term_names(args: ArgsModel, config: RawConfigParser) -> tuple[str, str]:
    """Get the long and short term credential section names.

    Args:
        args (ArgsModel): The command line arguments
        config (RawConfigParser): The config object

    Returns:
        tuple[str, str]: The long term and short term credential section names

    Raises:
        SystemExit: If the long term and short term credential section names are the same
    """
    if not args.long_term_suffix:
        long_term_name = f"{args.profile}-long-term"
    elif args.long_term_suffix.lower() == "none":
        long_term_name = args.profile
    else:
        long_term_name = f"{args.profile}-{args.long_term_suffix}"

    if not args.short_term_suffix or args.short_term_suffix.lower() == "none":
        short_term_name = args.profile
    else:
        short_term_name = f"{args.profile}-{args.short_term_suffix}"

    if long_term_name == short_term_name:
        log_error_and_exit(constants.ERR_LONG_TERM_EQ_SHORT_TERM)

    if args.assume_role:
        role_msg = f"with assumed role: {args.assume_role}"
    elif config_assumed_role_arn := config.has_option(args.profile, "assumed_role_arn"):
        role_msg = f"with assumed role: {config_assumed_role_arn}"
    else:
        role_msg = ""
    logger.info(f"Validating credentials for profile: {short_term_name} {role_msg}")

    return long_term_name, short_term_name

import configparser
import getpass
import sys
from configparser import NoOptionError, NoSectionError, RawConfigParser
from pathlib import Path

from loguru import logger

from aws_mfa import constants
from aws_mfa.utils import log_error_and_exit


def get_config(aws_creds_path: Path | str) -> RawConfigParser:
    """Read the AWS credentials file and return the config object.

    Args:
        aws_creds_path (Path | str): The path to the AWS credentials file

    Returns:
        RawConfigParser: The config object
    """
    config = configparser.RawConfigParser()
    try:
        config.read(aws_creds_path)
    except configparser.ParsingError:
        logger.exception("Error parsing the AWS credentials file")
        sys.exit(1)
    return config


def initial_setup(config: RawConfigParser, config_path: str):
    """Setup a new long term credentials section in the credentials file.
    This will prompt the user for the aws_access_key_id and aws_secret_access_key
    and write them to the credentials file.

    Args:
        config (RawConfigParser): The config object
        config_path (str): The path to the config file
    """
    profile_name = input("Profile name to use [default]: ") or "default"
    profile_name = f"{profile_name}-long-term"

    if not (aws_access_key_id := getpass.getpass("aws_access_key_id: ")):
        log_error_and_exit("You must supply aws_access_key_id")

    if not (aws_secret_access_key := getpass.getpass("aws_secret_access_key: ")):
        log_error_and_exit("You must supply aws_secret_access_key")

    config.add_section(profile_name)
    config.set(profile_name, "aws_access_key_id", aws_access_key_id)
    config.set(profile_name, "aws_secret_access_key", aws_secret_access_key)

    with open(config_path, "w") as configfile:
        config.write(configfile)


def get_aws_key_values(config: RawConfigParser, long_term_name: str) -> tuple[str, str]:
    """Get the aws_access_key_id and aws_secret_access_key from the long term credentials section.

    Args:
        config (RawConfigParser): The config object
        long_term_name (str): The name of the long term credentials section

    Returns:
        tuple[str, str]: The aws_access_key_id and aws_secret_access_key
    """
    try:
        key_id = config.get(long_term_name, "aws_access_key_id")
        access_key = config.get(long_term_name, "aws_secret_access_key")
    except NoSectionError:
        log_error_and_exit(constants.ERR_LONG_TERM_CREDS.format(long_term_name=long_term_name))
    except NoOptionError as e:
        log_error_and_exit(e)

    return key_id, access_key

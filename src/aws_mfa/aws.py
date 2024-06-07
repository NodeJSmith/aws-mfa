import typing
from configparser import RawConfigParser

import boto3
import pendulum
from botocore.exceptions import ClientError, ParamValidationError
from loguru import logger

from aws_mfa import constants
from aws_mfa.args import ArgsModel
from aws_mfa.utils import log_error_and_exit

if typing.TYPE_CHECKING:
    from mypy_boto3_sts import STSClient


def get_credentials(short_term_name: str, lt_key_id: str, lt_access_key: str, args: ArgsModel, config: RawConfigParser):
    """Get the short term credentials and write them to the config file.

    Args:
        short_term_name (str): The name of the short term credentials section
        lt_key_id (str): The long term aws_access_key_id
        lt_access_key (str): The long term aws_secret_access_key
        args (ArgsModel): The command line arguments
        config (RawConfigParser): The config object
    """
    client: "STSClient" = boto3.client("sts", aws_access_key_id=lt_key_id, aws_secret_access_key=lt_access_key)

    if args.token:
        logger.debug("Received token as argument")
        mfa_token = f"{args.token}"
    else:
        mfa_token = input(f"Enter AWS MFA code for device [{args.device}] " f"(renewing for {args.duration} seconds):")

    if args.assume_role:
        response = handle_assume_role(short_term_name, args, config, mfa_token, client)
    else:
        response = handle_not_assume_role(short_term_name, args, config, client, mfa_token)

    for option, value in constants.AWS_OPTION_MAP:
        config.set(short_term_name, option, response["Credentials"][value])

    # Save expiration individiually, so it can be manipulated
    exp_val = pendulum.instance(response["Credentials"]["Expiration"]).in_timezone("local")

    with open(args.credentials_path, "w") as configfile:
        config.write(configfile)

    logger.info(f"Success! Your credentials will expire in {args.duration} seconds at: {exp_val}")


def handle_not_assume_role(
    short_term_name: str, args: ArgsModel, config: RawConfigParser, client: "STSClient", mfa_token: str
):
    """Handle the path where the user is not assuming a role

    Not actually sure what the purpose of this function is, but it's here.

    Args:
        short_term_name (str): The short term credentials section name
        args (ArgsModel): The command line arguments
        config (RawConfigParser): The config object
        client (STSClient): The boto3 STS client
        mfa_token (str): The MFA token

    Returns:
        dict: The response from the get session token call
    """

    logger.info(f"Fetching Credentials - Profile: {short_term_name}, Duration: {args.duration}")
    try:
        response = client.get_session_token(
            DurationSeconds=args.duration, SerialNumber=args.device, TokenCode=mfa_token
        )
    except ClientError as e:
        log_error_and_exit(f"An error occured while calling assume role: {e}")
    except ParamValidationError:
        log_error_and_exit("Token must be six digits")

    config.set(short_term_name, "assumed_role", "False")
    config.remove_option(short_term_name, "assumed_role_arn")
    return response


def handle_assume_role(
    short_term_name: str, args: ArgsModel, config: RawConfigParser, mfa_token: str, client: "STSClient"
):
    """Handle the assume role path

    Args:
        short_term_name (str): The short term credentials section name
        args (ArgsModel): The command line arguments
        config (RawConfigParser): The config object
        mfa_token (str): The MFA token
        client (STSClient): The boto3 STS client

    Returns:
        dict: The response from the assume role call
    """
    logger.info(f"Assuming Role - Profile: {short_term_name}, Role: {args.assume_role}, Duration: {args.duration}")

    if args.role_session_name is None:
        args.role_session_name = short_term_name
        # log_error_and_exit("You must specify a role session name  via --role-session-name")

    try:
        response = client.assume_role(
            RoleArn=args.assume_role,
            RoleSessionName=args.role_session_name,
            DurationSeconds=args.duration,
            SerialNumber=args.device,
            TokenCode=mfa_token,
        )
    except ClientError as e:
        log_error_and_exit("An error occured while calling " f"assume role: {e}")
    except ParamValidationError:
        log_error_and_exit("Token must be six digits")

    config.set(short_term_name, "assumed_role", "True")
    config.set(short_term_name, "assumed_role_arn", args.assume_role)

    return response

LOGGER_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)


HELP_DEVICE = """
The MFA Device ARN. This value can also be provided via the environment variable 'MFA_DEVICE' or the ~/.aws/credentials
variable 'aws_mfa_device'."""

HELP_DURATION = """
The duration, in seconds, that the temporary credentials should remain valid.
Minimum value: 900 (15 minutes). Maximum: 129600 (36 hours). Defaults to 43200 (12 hours), or 3600 (one hour)
when using '--assume-role'. This value can also be provided via the environment variable 'MFA_STS_DURATION'."""

HELP_ASSUME_ROLE = """
The ARN of the AWS IAM Role you would like to assume, if specified. This value can also be provided via the
environment variable 'MFA_ASSUME_ROLE'"""

HELP_PROFILE = """
If using profiles, specify the name here. The default profile name is 'default'. The value can also
be provided via the environment variable 'AWS_PROFILE'."""

HELP_LONG_TERM_SUFFIX = "The suffix appended to the profile name to identify the long term credential section"
HELP_SHORT_TERM_SUFFIX = "The suffix appended to the profile name to identify the short term credential section"
HELP_FORCE = "Refresh credentials even if currently valid."
HELP_SETUP = "Setup a new log term credentials section"
HELP_ROLE_SESSION_NAME = "Friendly session name required when using --assume-role"

CHOICES_LOG_LEVEL = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]
METAVAR_DEVICE = "arn:aws:iam::123456788990:mfa/dudeman"
METAVAR_ASSUME_ROLE = "arn:aws:iam::123456788990:role/RoleName"

AWS_OPTION_MAP = [
    ("aws_access_key_id", "AccessKeyId"),
    ("aws_secret_access_key", "SecretAccessKey"),
    ("aws_session_token", "SessionToken"),
    ("aws_security_token", "SessionToken"),
    ("expiration", "Expiration"),
]

ERR_LONG_TERM_CREDS = """
Long term credentials session '[{long_term_name}]' is missing. You must add this section to your credentials file along
with your long term 'aws_access_key_id' and 'aws_secret_access_key'"""
ERR_LONG_TERM_EQ_SHORT_TERM = "The value for 'long-term-suffix' cannot be equal to the value for 'short-term-suffix'"
ERR_MFA_DEVICE = (
    "You must provide --device or set environment variable MFA_DEVICE or set 'aws_mfa_device in .aws/credentials"
)


REUP_MESSAGE = "Obtaining credentials for a new role or profile."

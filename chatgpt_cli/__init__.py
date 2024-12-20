from chatgpt_cli.utils.env_vars import check_environment_variables

REQUIRED_ENV_VARS = [
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME",
    "OPENAI_API_KEY",
]

env_results = check_environment_variables(
    *REQUIRED_ENV_VARS,
)
if not env_results.is_valid:
    raise EnvironmentError(env_results.message)

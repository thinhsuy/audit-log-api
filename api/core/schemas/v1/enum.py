from sqlalchemy import Enum

action_type_enum = Enum(
    "CREATE",
    "UPDATE",
    "DELETE",
    "VIEW",
    "LOGIN",
    "LOGOUT",
    name="action_type_enum",
)
severity_enum = Enum(
    "INFO",
    "WARNING",
    "ERROR",
    "CRITICAL",
    name="severity_enum",
)
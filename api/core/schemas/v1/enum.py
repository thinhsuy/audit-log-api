from sqlalchemy import Enum as Pg_Enum
from enum import StrEnum


class ActionTypeEnum(StrEnum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VIEW = "VIEW"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"


class SeverityEnum(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class UserRoleEnum(StrEnum):
    ADMIN = "Admin"
    CLIENT = "User"
    AUDITOR = "Auditor"


class LogStatsEnum(StrEnum):
    TOTOL_LOGS = "total_logs"
    INFO_LOGS = "info_logs"
    WARN_LOGS = "warning_logs"
    ERROR_LOGS = "error_logs"
    CRITICAL_lOGS = "critical_logs"
    CREATE_LOGS = "create_logs"
    UPDATE_LOGS = "update_logs"
    DELETE_LOGS = "delete_logs"
    VIEW_LOGS = "view_logs"


class ChatRoleEnum(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


# ------------------------- PG_ENUM ------------------
action_type_enum = Pg_Enum(
    ActionTypeEnum,
    name="action_type_enum",
    native_enum=True,
    create_type=True,
)

severity_enum = Pg_Enum(
    SeverityEnum,
    name="severity_enum",
    native_enum=True,
    create_type=True,
)

user_role_enum = Pg_Enum(
    UserRoleEnum,
    name="user_role_enum",
    native_enum=True,
    create_type=True,
)

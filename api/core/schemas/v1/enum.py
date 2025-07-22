from sqlalchemy import Enum as Pg_Enum
from enum import Enum

class ActionTypeEnum(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    VIEW = "VIEW"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"

class SeverityEnum(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class UserRoleEnum(str, Enum):
    ADMIN = "ADMIN"
    CLIENT = "CLIENT"

class LogStatsEnum(str, Enum):
    TOTOL_LOGS = "total_logs"
    INFO_LOGS = "info_logs"
    WARN_LOGS = "warning_logs"
    ERROR_LOGS = "error_logs"
    CRITICAL_lOGS = "critical_logs"
    CREATE_LOGS = "create_logs"
    UPDATE_LOGS = "update_logs"
    DELETE_LOGS = "delete_logs"
    VIEW_LOGS = "view_logs"

# ------------------------- PG_ENUM ------------------
action_type_enum = Pg_Enum(
    ActionTypeEnum.CREATE,
    ActionTypeEnum.UPDATE,
    ActionTypeEnum.DELETE,
    ActionTypeEnum.VIEW,
    ActionTypeEnum.LOGIN,
    ActionTypeEnum.LOGOUT,
    name="action_type_enum",
)

severity_enum = Pg_Enum(
    SeverityEnum.INFO,
    SeverityEnum.WARNING,
    SeverityEnum.ERROR,
    SeverityEnum.CRITICAL,
    name="severity_enum",
)

user_role_enum = Pg_Enum(
    UserRoleEnum.ADMIN,
    UserRoleEnum.CLIENT,
    name="user_role_enum",
)
